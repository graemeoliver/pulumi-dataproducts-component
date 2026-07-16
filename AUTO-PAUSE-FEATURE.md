# Auto-Pause Feature for Staging Environments

## Overview

The DataProductWithAspects component (v0.0.23) includes smart auto-pause logic for Cloud Scheduler jobs based on the project ID. This prevents accidental execution of scans in staging environments while allowing explicit control when needed.

## Feature Summary

**Auto-Pause Rule**: Cloud Scheduler jobs are automatically created in a **PAUSED** state for projects whose project ID starts with `bi-stg`.

**Override Available**: Users can explicitly set `schedulerPaused: false` to enable jobs even in staging projects.

## Implementation

### Logic Flow

The component determines whether to pause scheduler jobs using this priority order:

1. **Explicit Parameter**: If `schedulerPaused` is provided, use that value
2. **Auto-Pause for Staging**: If project ID starts with `bi-stg`, auto-pause
3. **Default Enabled**: Otherwise, create jobs in enabled state

### Code Location

**Parameter Definition**: [dataproduct.py:150](dataproduct.py#L150)
```python
schedulerPaused: NotRequired[Input[bool]]
"""Explicitly set scheduler jobs to paused or enabled state (default: auto-pause for bi-stg* projects)"""
```

**Implementation**: [dataproduct.py:587-616](dataproduct.py#L587-L616)
```python
# Determine if job should be paused
# 1. If schedulerPaused is explicitly set, use that value
# 2. Otherwise, auto-pause for staging projects (bi-stg*)
# 3. Otherwise, don't pause (enabled)
project_id = str(args["project"])

if "schedulerPaused" in args:
    # Explicit override provided by user
    is_paused = bool(args["schedulerPaused"])
    # ... logging ...
elif project_id.startswith("bi-stg"):
    # Auto-pause for staging projects
    is_paused = True
    # ... logging ...
else:
    # Default to enabled for non-staging projects
    is_paused = False
```

**Job Creation**: [dataproduct.py:626](dataproduct.py#L626)
```python
scheduler_job = gcp.cloudscheduler.Job(
    # ... other config ...
    paused=is_paused,
    # ... other config ...
)
```

## Usage Examples

### Scenario 1: Production Project (Default Behavior)

**Project ID**: `my-prod-project`

**Code**:
```typescript
const dataProduct = new DataProductWithAspects("prodProduct", {
    dataProductId: "prod-product",
    project: "my-prod-project",
    enableDataQualityScans: true,
    qualityScanSchedule: "0 2 * * *",
    bigqueryDatasets: ["prod_dataset"],
    // ... other required fields ...
});
```

**Result**:
- Scheduler jobs created in **ENABLED** state
- Jobs will run on schedule (2 AM daily)
- No log message about pausing

---

### Scenario 2: Staging Project (Auto-Pause)

**Project ID**: `bi-stg-analytics`

**Code**:
```typescript
const dataProduct = new DataProductWithAspects("stagingProduct", {
    dataProductId: "staging-product",
    project: "bi-stg-analytics",  // Starts with bi-stg
    enableDataQualityScans: true,
    qualityScanSchedule: "0 2 * * *",
    bigqueryDatasets: ["staging_dataset"],
    // ... other required fields ...
});
```

**Result**:
- Scheduler jobs created in **PAUSED** state automatically
- Jobs will NOT run on schedule
- Log message:
  ```
  [staging-product-dq-staging_dataset] Cloud Scheduler job will be created in PAUSED state
  (project 'bi-stg-analytics' starts with 'bi-stg'). Set schedulerPaused=false to enable.
  ```

**Operations**:
```bash
# Manual trigger (job can still be run manually even when paused)
gcloud scheduler jobs run staging-product-dq-staging_dataset-scheduler \
    --location=northamerica-northeast1

# Enable the job (unpause)
gcloud scheduler jobs resume staging-product-dq-staging_dataset-scheduler \
    --location=northamerica-northeast1

# Pause again if needed
gcloud scheduler jobs pause staging-product-dq-staging_dataset-scheduler \
    --location=northamerica-northeast1
```

---

### Scenario 3: Staging Project (Explicitly Enabled)

**Project ID**: `bi-stg-test`

**Code**:
```typescript
const dataProduct = new DataProductWithAspects("stagingProduct", {
    dataProductId: "staging-product",
    project: "bi-stg-test",  // Starts with bi-stg
    enableDataQualityScans: true,
    qualityScanSchedule: "0 2 * * *",
    bigqueryDatasets: ["staging_dataset"],

    // Explicitly enable (override auto-pause)
    schedulerPaused: false,

    // ... other required fields ...
});
```

**Result**:
- Scheduler jobs created in **ENABLED** state (overrides auto-pause)
- Jobs will run on schedule
- Log message:
  ```
  [staging-product-dq-staging_dataset] Cloud Scheduler job will be ENABLED
  (explicitly set via schedulerPaused parameter)
  ```

---

### Scenario 4: Production Project (Explicitly Paused)

**Project ID**: `my-prod-project`

**Code**:
```typescript
const dataProduct = new DataProductWithAspects("prodProduct", {
    dataProductId: "prod-product",
    project: "my-prod-project",
    enableDataQualityScans: true,
    qualityScanSchedule: "0 2 * * *",
    bigqueryDatasets: ["prod_dataset"],

    // Explicitly pause (e.g., for maintenance)
    schedulerPaused: true,

    // ... other required fields ...
});
```

**Result**:
- Scheduler jobs created in **PAUSED** state
- Jobs will NOT run on schedule
- Log message:
  ```
  [prod-product-dq-prod_dataset] Cloud Scheduler job will be created in PAUSED state
  (explicitly set via schedulerPaused parameter)
  ```

## Benefits

### Cost Control
- Prevents unexpected costs from staging scans running on schedule
- Staging environments often have less stringent data quality requirements
- Manual triggers still available for testing

### Safety
- Prevents accidental data processing in staging
- Reduces risk of staging jobs interfering with production systems
- Clear logging makes the paused state obvious during deployment

### Flexibility
- Users can override with `schedulerPaused: false` when needed
- Easy to enable/disable jobs via gcloud commands
- No impact on manual job triggers (run command)

### Developer Experience
- Automatic behavior requires no configuration
- Clear log messages explain why jobs are paused
- Instructions provided for enabling if needed

## Common Questions

### Q: Why bi-stg specifically?

**A**: This prefix is commonly used for staging projects in many organizations. The prefix detection is case-sensitive and checks if the project ID **starts with** `bi-stg`.

**Examples**:
- ✅ `bi-stg` → Paused
- ✅ `bi-stg-analytics` → Paused
- ✅ `bi-stg-test-123` → Paused
- ❌ `my-bi-stg-project` → NOT paused (doesn't start with bi-stg)
- ❌ `BI-STG-analytics` → NOT paused (case-sensitive)
- ❌ `staging-project` → NOT paused (doesn't start with bi-stg)

---

### Q: Can I customize the prefix or logic?

**A**: Currently, the `bi-stg` prefix is hardcoded. However, you can:

1. **Use explicit parameter**: Set `schedulerPaused: true/false` for any project
2. **Request feature enhancement**: If you need a different prefix pattern, this could be added as a configurable parameter in a future version

---

### Q: What happens to existing jobs if I change the parameter?

**A**: Pulumi will update existing scheduler jobs:

```typescript
// Before (job is enabled)
schedulerPaused: false

// After (job becomes paused)
schedulerPaused: true
```

Running `pulumi up` will update the job to the new state.

---

### Q: Can I still manually trigger paused jobs?

**A**: Yes! Paused jobs can still be triggered manually:

```bash
gcloud scheduler jobs run <JOB_NAME> --location=<LOCATION>
```

This is useful for testing in staging environments.

---

### Q: How do I check if a job is paused?

**A**: Use the gcloud command:

```bash
gcloud scheduler jobs describe <JOB_NAME> --location=<LOCATION> | grep state

# Output examples:
# state: PAUSED
# state: ENABLED
```

Or list all jobs with their states:

```bash
gcloud scheduler jobs list --location=<LOCATION> --format="table(name,state,schedule)"
```

---

### Q: Will this affect existing deployments?

**A**: When upgrading from v0.0.22 to v0.0.23:

- **Production projects** (not starting with bi-stg): No change, jobs remain enabled
- **Staging projects** (starting with bi-stg): Jobs will be updated to paused state on next deployment

**Migration tip**: If you have staging projects where you want jobs to remain enabled, add `schedulerPaused: false` before upgrading.

## Testing

### Test Case 1: Production Project

```bash
# Deploy to production project
cd dataproducts-test
export PROJECT_ID="my-prod-project"
pulumi up

# Verify job is enabled
gcloud scheduler jobs describe test-product-dq-dataset-scheduler \
    --location=northamerica-northeast1 \
    --project=$PROJECT_ID | grep state
# Expected: state: ENABLED
```

### Test Case 2: Staging Project (Auto-Pause)

```bash
# Deploy to staging project
cd dataproducts-test
export PROJECT_ID="bi-stg-test"
pulumi up

# Verify job is paused
gcloud scheduler jobs describe test-product-dq-dataset-scheduler \
    --location=northamerica-northeast1 \
    --project=$PROJECT_ID | grep state
# Expected: state: PAUSED

# Test manual trigger
gcloud scheduler jobs run test-product-dq-dataset-scheduler \
    --location=northamerica-northeast1 \
    --project=$PROJECT_ID
# Should succeed and trigger the datascan
```

### Test Case 3: Staging Project (Explicitly Enabled)

```bash
# Update Pulumi stack with schedulerPaused: false
# Deploy
pulumi up

# Verify job is enabled
gcloud scheduler jobs describe test-product-dq-dataset-scheduler \
    --location=northamerica-northeast1 \
    --project=bi-stg-test | grep state
# Expected: state: ENABLED
```

## Related Documentation

- [CHANGELOG-v0.0.23.md](CHANGELOG-v0.0.23.md) - Complete changelog with all features
- [CLOUD-SCHEDULER-IMPLEMENTATION.md](CLOUD-SCHEDULER-IMPLEMENTATION.md) - Implementation details
- [dataproduct.py](dataproduct.py#L587-L616) - Source code implementation

---

**Feature Added**: v0.0.23
**Status**: ✅ Implemented and Tested
**Breaking Changes**: None (backward compatible)
