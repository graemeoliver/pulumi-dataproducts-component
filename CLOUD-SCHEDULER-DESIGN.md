# Cloud Scheduler for Data Quality Scans - Design Document

## Requirement

All data quality scans and other scans must be scheduled using Cloud Scheduler instead of internal Dataplex scheduling mechanisms.

## Benefits

1. **Centralized Monitoring**: All scheduled jobs visible in one place (Cloud Scheduler UI)
2. **Better Alerting**: Cloud Scheduler provides built-in retry policies and error notifications
3. **Audit Trail**: Clear logs of when jobs were triggered and their outcomes
4. **Flexibility**: Easy to pause, modify, or manually trigger scans
5. **Consistency**: Same scheduling mechanism across all GCP services
6. **Integration**: Can trigger Cloud Workflows, Cloud Run, or other services
7. **Cost Visibility**: Track scheduling costs separately from scan execution costs

## Current Implementation (v0.0.22)

### Data Quality Scans

**Current Code** ([dataproduct.py:531-536](dataproduct.py#L531-L536)):
```python
execution_spec={
    "trigger": {
        "schedule": {
            "cron": args.get("qualityScanSchedule", "0 2 * * *")
        }
    }
}
```

**Issue**: Uses Dataplex's internal scheduler

### Data Profiling Scans (DH2 Orchestrator)

Similar pattern in [data_product_dh2_orchestrator.py](data_product_dh2_orchestrator.py) for data profiling scans.

## Proposed Implementation

### Architecture

```
Cloud Scheduler Job → HTTP POST → Dataplex API → Trigger Datascan
                ↓
         Cloud Logging
         Cloud Monitoring
```

### Components

1. **Datascan** (on-demand execution)
   - Remove schedule from execution_spec
   - Set to on-demand trigger mode

2. **Cloud Scheduler Job**
   - Schedule: Cron expression
   - Target: Dataplex API endpoint
   - Authentication: Service Account with permissions
   - Retry Policy: Configurable retries

3. **Service Account**
   - Permission: `dataplex.datascans.run`
   - Assigned to Cloud Scheduler job

### Code Changes

#### 1. Update Datascan Configuration

**Before**:
```python
execution_spec={
    "trigger": {
        "schedule": {
            "cron": args.get("qualityScanSchedule", "0 2 * * *")
        }
    }
}
```

**After**:
```python
execution_spec={
    "trigger": {
        "on_demand": {}  # On-demand execution only
    }
}
```

#### 2. Create Cloud Scheduler Job

**New Method**:
```python
def _create_scheduler_job_for_datascan(
    self,
    name: str,
    datascan: gcp.dataplex.Datascan,
    schedule: str,
    opts: ResourceOptions
) -> gcp.cloudscheduler.Job:
    """
    Create a Cloud Scheduler job to trigger a Dataplex Datascan.

    Args:
        name: Resource name for the scheduler job
        datascan: The Datascan resource to trigger
        schedule: Cron schedule expression
        opts: Pulumi resource options

    Returns:
        Cloud Scheduler Job resource
    """
    # Create service account for scheduler (if not provided)
    scheduler_sa = gcp.serviceaccount.Account(
        f"{name}-scheduler-sa",
        account_id=f"{name}-scheduler".replace("_", "-")[:30],
        display_name=f"Scheduler for {name}",
        opts=ResourceOptions(parent=self)
    )

    # Grant permission to run datascans
    iam_binding = gcp.projects.IAMMember(
        f"{name}-scheduler-datascan-runner",
        project=args["project"],
        role="roles/dataplex.datascans.runner",
        member=scheduler_sa.email.apply(lambda email: f"serviceAccount:{email}"),
        opts=ResourceOptions(parent=self)
    )

    # Create scheduler job
    scheduler_job = gcp.cloudscheduler.Job(
        f"{name}-scheduler",
        name=f"{name}-datascan-scheduler",
        description=f"Trigger {name} data quality scan",
        schedule=schedule,
        time_zone="America/Toronto",  # Make configurable
        attempt_deadline="320s",  # 5+ minutes for API call

        # HTTP target to trigger Datascan via API
        http_target={
            "uri": datascan.name.apply(
                lambda datascan_name:
                f"https://dataplex.googleapis.com/v1/{datascan_name}:run"
            ),
            "http_method": "POST",
            "headers": {
                "Content-Type": "application/json"
            },
            # Empty body for run request
            "body": base64.b64encode(b"{}").decode("utf-8"),
            "oauth_token": {
                "service_account_email": scheduler_sa.email,
                "scope": "https://www.googleapis.com/auth/cloud-platform"
            }
        },

        # Retry configuration
        retry_config={
            "retry_count": 3,
            "max_retry_duration": "300s",
            "min_backoff_duration": "5s",
            "max_backoff_duration": "3600s",
            "max_doublings": 5
        },

        opts=ResourceOptions(
            parent=self,
            depends_on=[datascan, iam_binding]
        )
    )

    return scheduler_job
```

#### 3. Update Data Quality Scan Setup

**Modified Method**:
```python
def _setup_data_quality_scans(
    self,
    name: str,
    args: DataProductArgs,
    opts: ResourceOptions
) -> Dict[str, Any]:
    """
    Create Dataplex data quality scans with Cloud Scheduler triggers.

    Returns dict with:
    - scans: List of Datascan resources
    - schedulers: List of Cloud Scheduler Job resources
    """
    scans = []
    schedulers = []

    for dataset_id in args.get("bigqueryDatasets", []):
        # Create on-demand datascan
        scan = gcp.dataplex.Datascan(
            f"{name}-dq-{dataset_id}",
            data_scan_id=f"{args["dataProductId"]}-dq-{dataset_id}",
            location=args["location"],
            project=args["project"],
            data={
                "resource": f"//bigquery.googleapis.com/projects/{args["project"]}/datasets/{dataset_id}"
            },
            execution_spec={
                "trigger": {
                    "on_demand": {}  # No internal schedule
                }
            },
            data_quality_spec={
                "rules": args.get("qualityRules", None) or self._default_quality_rules()
            },
            labels=self._build_cost_labels(args),
            opts=opts
        )
        scans.append(scan)

        # Create Cloud Scheduler job to trigger the scan
        if args.get("qualityScanSchedule"):
            scheduler = self._create_scheduler_job_for_datascan(
                name=f"{name}-dq-{dataset_id}",
                datascan=scan,
                schedule=args.get("qualityScanSchedule", "0 2 * * *"),
                opts=opts
            )
            schedulers.append(scheduler)

    return {
        "scans": scans,
        "schedulers": schedulers
    }
```

#### 4. Update Component Initialization

**Modified `__init__`**:
```python
# Set up data quality scans with Cloud Scheduler
self.quality_scans = {"scans": [], "schedulers": []}
if args.get("enableDataQualityScans", False):
    self.quality_scans = self._setup_data_quality_scans(name, args, child_opts)

# Update outputs to include scheduler information
self.register_outputs({
    'dataProductId': self.dataProductId,
    'dataProductName': self.dataProductName,
    'aspectsApplied': self.aspectsApplied,
    'aspects': self.aspects,
    'dataAssets': self.data_assets,
    'qualityScans': self.quality_scans.get("scans", []),
    'qualityScanSchedulers': self.quality_scans.get("schedulers", []),
    'monitoring': self.monitoring,
    'version': args.get("version", defaults.DEFAULT_VERSION)
})
```

### New Configuration Parameters

Add to `DataProductArgs`:

```python
class DataProductArgs(TypedDict):
    # ... existing fields ...

    # Data Quality Scheduling
    qualityScanSchedule: NotRequired[Input[str]]
    """Cron schedule for quality scans (Cloud Scheduler format)"""

    qualityScanTimeZone: NotRequired[Input[str]]
    """Time zone for quality scan schedule (default: America/Toronto)"""

    schedulerServiceAccount: NotRequired[Input[str]]
    """Service account email for scheduler (creates new if not provided)"""

    schedulerRetryCount: NotRequired[Input[int]]
    """Number of retries for failed scans (default: 3)"""
```

## Migration Path

### Breaking Change Analysis

**Impact**: MEDIUM - Changes scan triggering mechanism

**Affected Users**: Anyone using `enableDataQualityScans=True`

### Migration Strategy

#### Option 1: Automatic Migration (Recommended)

Component automatically migrates to Cloud Scheduler while maintaining backward compatibility.

**Implementation**:
```python
# In _setup_data_quality_scans:
use_cloud_scheduler = args.get("useCloudSchedulerForScans", True)  # Default to new behavior

if use_cloud_scheduler:
    # New Cloud Scheduler approach
    execution_spec = {"trigger": {"on_demand": {}}}
    # Create scheduler job
else:
    # Legacy internal scheduler (deprecated)
    execution_spec = {
        "trigger": {
            "schedule": {
                "cron": args.get("qualityScanSchedule", "0 2 * * *")
            }
        }
    }
    pulumi.log.warn(
        "Using internal Dataplex scheduler is deprecated. "
        "Set useCloudSchedulerForScans=true to use Cloud Scheduler."
    )
```

#### Option 2: Major Version Bump

Release as v1.0.0 with breaking changes, require manual migration.

**Recommended**: Option 1 (automatic with opt-out)

### Rollout Plan

1. **v0.0.23**: Add Cloud Scheduler support with `useCloudSchedulerForScans` parameter (default: false)
2. **v0.0.24**: Change default to true, add deprecation warning for old approach
3. **v1.0.0**: Remove legacy internal scheduler support entirely

## Testing

### Unit Tests

Add to `tests/test_aspect_registry.py` or new `tests/test_scheduler.py`:

```python
def test_cloud_scheduler_creation():
    """Test that Cloud Scheduler jobs are created correctly"""
    # Mock Datascan
    # Test scheduler job creation
    # Verify HTTP target configuration
    # Check retry policy

def test_scheduler_service_account():
    """Test service account creation and IAM binding"""
    # Verify SA is created
    # Check IAM binding for dataplex.datascans.runner role

def test_on_demand_datascan():
    """Test that Datascans are configured for on-demand execution"""
    # Verify execution_spec has on_demand trigger
    # Verify no schedule is set
```

### Integration Tests

```bash
# Test stack in dataproducts-test
cd dataproducts-test

# Update Pulumi.yaml to enable quality scans
resources:
  testDataProduct:
    properties:
      enableDataQualityScans: true
      qualityScanSchedule: "0 3 * * *"  # 3 AM daily
      bigqueryDatasets:
        - test_dataset

# Deploy
NO_PROXY="localhost,127.0.0.1,::1" pulumi up

# Verify resources created:
# 1. Datascan (on-demand)
# 2. Service Account
# 3. IAM Binding
# 4. Cloud Scheduler Job

# Manually trigger via scheduler
gcloud scheduler jobs run <job-name> --location=<location>

# Verify datascan was triggered
gcloud dataplex datascans list --location=<location>
```

## IAM Permissions Required

### Service Account (Created by Component)

```yaml
roles:
  - roles/dataplex.datascans.runner  # Run datascans
```

### Deploying User/Service Account

```yaml
roles:
  - roles/cloudscheduler.admin       # Create scheduler jobs
  - roles/iam.serviceAccountCreator  # Create service accounts
  - roles/iam.securityAdmin          # Bind IAM roles (or roles/owner)
  - roles/dataplex.admin             # Create datascans
```

## Cost Implications

### Cloud Scheduler Costs

- **Free Tier**: 3 jobs per month
- **Paid**: $0.10 per job per month after free tier
- **Example**: 10 data quality scans = $0.70/month (7 paid jobs)

### Benefits vs Costs

- **Monitoring**: Cloud Scheduler provides better monitoring for free
- **Reliability**: Built-in retries reduce failed scans
- **Worth It**: Small cost ($<1/month) for significantly better operability

## Example Usage

### Consumer Stack (Pulumi.yaml)

```yaml
resources:
  myDataProduct:
    type: dataproducts:index:DataProductWithAspects
    properties:
      # ... required fields ...

      # Enable data quality scans with Cloud Scheduler
      enableDataQualityScans: true
      qualityScanSchedule: "0 2 * * *"        # 2 AM daily
      qualityScanTimeZone: "America/Toronto"
      schedulerRetryCount: 3

      bigqueryDatasets:
        - sales_data
        - customer_data

outputs:
  scans: ${myDataProduct.qualityScans}
  schedulers: ${myDataProduct.qualityScanSchedulers}
```

### Monitoring Example

```bash
# List all scheduled scans
gcloud scheduler jobs list --location=northamerica-northeast1

# View job details
gcloud scheduler jobs describe my-datascan-scheduler \
  --location=northamerica-northeast1

# View execution history
gcloud logging read "resource.type=cloud_scheduler_job" \
  --limit=50 --format=json

# Pause a scan schedule
gcloud scheduler jobs pause my-datascan-scheduler \
  --location=northamerica-northeast1

# Resume
gcloud scheduler jobs resume my-datascan-scheduler \
  --location=northamerica-northeast1
```

## Documentation Updates

### README.md

Add section:

```markdown
## Data Quality Scans with Cloud Scheduler

The component uses Cloud Scheduler to trigger data quality scans, providing:
- Centralized scheduling and monitoring
- Configurable retry policies
- Easy pause/resume functionality
- Audit trail in Cloud Logging

Configuration:
\`\`\`yaml
enableDataQualityScans: true
qualityScanSchedule: "0 2 * * *"  # Cron format
qualityScanTimeZone: "America/Toronto"
schedulerRetryCount: 3
\`\`\`

Manual trigger:
\`\`\`bash
gcloud scheduler jobs run <job-name> --location=<location>
\`\`\`
```

## Implementation Timeline

### Phase 1: Core Implementation (v0.0.23)
- [ ] Add `_create_scheduler_job_for_datascan()` method
- [ ] Update `_setup_data_quality_scans()` for Cloud Scheduler
- [ ] Add new TypedDict fields
- [ ] Update outputs to include schedulers
- [ ] Add unit tests
- **Time**: 3-4 hours
- **Tag**: v0.0.23-alpha

### Phase 2: Testing & Documentation (v0.0.23)
- [ ] Integration testing with test stack
- [ ] Update README.md
- [ ] Add Cloud Scheduler monitoring examples
- [ ] Update CHANGELOG
- **Time**: 2-3 hours
- **Tag**: v0.0.23

### Phase 3: DH2 Orchestrator (v0.0.24)
- [ ] Apply same pattern to DH2 data profiling scans
- [ ] Update orchestrator documentation
- [ ] Test with DH2 pipelines
- **Time**: 2-3 hours
- **Tag**: v0.0.24

**Total Implementation Time**: 7-10 hours

## Questions for Clarification

1. **Time Zone**: What time zone should be default? (Currently: America/Toronto)
2. **Retry Policy**: Current proposal: 3 retries, 5s-1h backoff. Acceptable?
3. **Service Account**: Create per-scan or shared across all scans?
4. **Migration**: Auto-migrate (Option 1) or require opt-in?
5. **DH2 Scans**: Apply same pattern to data profiling scans in orchestrator?

## Approval Needed

- [ ] Design approved
- [ ] Ready to implement Phase 1
- [ ] Ready to test Phase 2
- [ ] Ready to extend to DH2 (Phase 3)
