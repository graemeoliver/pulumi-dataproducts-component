# Scripts Directory

This directory contains utility scripts for setting up and managing the DataProductWithAspects component.

## Available Scripts

### setup-cloud-scheduler-iam.sh

Sets up IAM permissions required for Cloud Scheduler to trigger Dataplex Datascans.

**Purpose**: Grant the `roles/dataplex.datascans.runner` role to the service account used by Cloud Scheduler jobs.

**Prerequisites**:
- You must have `roles/iam.securityAdmin` or `roles/owner` on the project
- The service account must already exist (or use default compute SA)

**Usage**:
```bash
./setup-cloud-scheduler-iam.sh PROJECT_ID [SERVICE_ACCOUNT_EMAIL]
```

**Examples**:
```bash
# Use default compute service account
./setup-cloud-scheduler-iam.sh my-project-123

# Use custom service account
./setup-cloud-scheduler-iam.sh my-project-123 scheduler-sa@my-project-123.iam.gserviceaccount.com
```

**When to run**: Before deploying a Pulumi stack that uses `useCloudSchedulerForScans: true`

**What it does**:
1. Validates the project ID and gets the project number
2. Determines which service account to use (provided or default compute SA)
3. Grants `roles/dataplex.datascans.runner` to the service account
4. Verifies the IAM binding was created successfully

**Required IAM Role**:
- `roles/dataplex.datascans.runner` - Allows the service account to trigger datascan runs via the Dataplex API

## Cloud Scheduler Overview

When `useCloudSchedulerForScans: true` (the default), the component creates:

1. **On-Demand Datascans**: Datascans configured with `trigger.on_demand` instead of internal scheduling
2. **Cloud Scheduler Jobs**: Jobs that POST to the Dataplex API to trigger the datascans
3. **OAuth Authentication**: Scheduler jobs use OAuth tokens with the specified service account

**Benefits**:
- Centralized scheduling in Cloud Scheduler UI
- Better monitoring and alerting capabilities
- Easy pause/resume functionality
- Audit trail in Cloud Logging
- Consistent retry policies

**Architecture**:
```
Cloud Scheduler Job → HTTP POST → Dataplex API → Trigger Datascan
        ↓                              ↓
  Cloud Logging               Cloud Logging + Monitoring
```

## Migration from Internal Scheduling

If you have existing datascans using internal Dataplex scheduling:

1. Run the IAM setup script (see above)
2. Update your Pulumi stack to use Cloud Scheduler:
   ```yaml
   # No changes needed - Cloud Scheduler is the default
   # Or explicitly enable it:
   useCloudSchedulerForScans: true
   ```
3. Deploy with `pulumi up`
4. Existing datascans will be replaced with on-demand versions + scheduler jobs

**To opt-out** (use internal scheduling):
```yaml
useCloudSchedulerForScans: false
```

## Troubleshooting

### Permission Denied Errors

**Error**: "Permission denied when triggering datascan"

**Solution**: Run the IAM setup script:
```bash
./scripts/setup-cloud-scheduler-iam.sh <PROJECT_ID>
```

### Service Account Not Found

**Error**: "Service account does not exist"

**Solution**:
1. Create a custom service account:
   ```bash
   gcloud iam service-accounts create scheduler-sa \
       --display-name="Cloud Scheduler Service Account"
   ```
2. Run the IAM setup script with the custom SA:
   ```bash
   ./scripts/setup-cloud-scheduler-iam.sh <PROJECT_ID> scheduler-sa@<PROJECT_ID>.iam.gserviceaccount.com
   ```
3. Update your Pulumi stack to use the custom SA:
   ```yaml
   schedulerServiceAccount: "scheduler-sa@<PROJECT_ID>.iam.gserviceaccount.com"
   ```

### Scheduler Jobs Not Created

**Issue**: Datascans created but no scheduler jobs

**Possible Causes**:
1. `useCloudSchedulerForScans` is set to `false`
2. `enableDataQualityScans` is not set to `true`
3. No BigQuery datasets specified in `bigqueryDatasets`

**Check**:
```bash
# List scheduler jobs
gcloud scheduler jobs list --location=<LOCATION>

# Check component outputs
pulumi stack output schedulerJobs
```

### Scheduler Job Fails to Trigger

**Issue**: Job runs but datascan doesn't execute

**Debugging Steps**:
1. Check Cloud Scheduler logs:
   ```bash
   gcloud logging read "resource.type=cloud_scheduler_job" --limit=50
   ```
2. Verify service account has correct role:
   ```bash
   gcloud projects get-iam-policy <PROJECT_ID> \
       --flatten="bindings[].members" \
       --filter="bindings.members:serviceAccount:<SA_EMAIL>"
   ```
3. Test manual trigger:
   ```bash
   gcloud scheduler jobs run <JOB_NAME> --location=<LOCATION>
   ```

## References

- [Cloud Scheduler Documentation](https://cloud.google.com/scheduler/docs)
- [Dataplex Datascan API](https://cloud.google.com/dataplex/docs/reference/rest/v1/projects.locations.dataScans/run)
- [IAM Roles for Dataplex](https://cloud.google.com/dataplex/docs/iam-roles)
