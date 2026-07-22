# Testing Data Quality Alerts

## Overview

This guide covers how to test the data quality alerting feature during development and after deployment.

## Prerequisites

- Data product deployed with `enableDataQualityScans: true`
- Email address configured via `dataQualityAlertEmail` or `alertEmail`
- Access to GCP Console for the project

## Testing Approach

### Phase 1: Verify Resources Created

Test that all alerting resources are created correctly.

### Phase 2: Trigger Test Alerts

Intentionally cause alert conditions to verify emails are sent.

### Phase 3: Verify Alert Content

Confirm emails contain correct information and links.

---

## Phase 1: Verify Resources Created

### 1.1 Check Notification Channel

```bash
# List notification channels
gcloud alpha monitoring channels list \
  --project=cubedev2-lab-1c497b \
  --format="table(name,displayName,labels.email_address)"

# Expected output:
# NAME                                    DISPLAY_NAME                              EMAIL_ADDRESS
# projects/.../channels/12345...          Test Data Product - Data Quality Alerts   your-email@company.com
```

**Verify**:
- Channel created with correct display name
- Email address is correct
- Channel is enabled

### 1.2 Check Alert Policies

```bash
# List alert policies
gcloud alpha monitoring policies list \
  --project=cubedev2-lab-1c497b \
  --filter="displayName:Data Quality" \
  --format="table(name,displayName,enabled,notificationChannels)"

# Expected: 3 policies per dataset
# - Data Quality Scan Failure - {scan_id}
# - Low Data Quality Score - {scan_id}
# - Data Quality Scan Stale - {scan_id}
```

**Verify**:
- 3 policies created per BigQuery dataset
- All policies are enabled
- Notification channels are attached
- Display names are correct

### 1.3 Verify in Console

**Navigate to**: [Cloud Monitoring > Alerting](https://console.cloud.google.com/monitoring/alerting?project=cubedev2-lab-1c497b)

**Check**:
- All alert policies visible
- Status shows "OK" (no active incidents)
- Notification channels configured correctly

---

## Phase 2: Trigger Test Alerts

### Test 1: Scan Failure Alert

**Method 1: Remove BigQuery Permissions (Recommended)**

```bash
# 1. Get current IAM policy for the dataset
bq show --format=prettyjson \
  cubedev2-lab-1c497b:demo_dataset > /tmp/dataset_policy_backup.json

# 2. Identify the service account that runs DataScans
# Usually: service-{PROJECT_NUMBER}@gcp-sa-dataplex.iam.gserviceaccount.com

# 3. Remove BigQuery Data Viewer role temporarily
gcloud projects remove-iam-policy-binding cubedev2-lab-1c497b \
  --member="serviceAccount:service-722471676767@gcp-sa-dataplex.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

# 4. Manually trigger the DataScan
gcloud dataplex datascans run \
  test-data-product-001-dq-demo_dataset \
  --location=northamerica-northeast1 \
  --project=cubedev2-lab-1c497b

# 5. Wait 2-3 minutes for scan to fail

# 6. Check for alert
gcloud alpha monitoring policies incidents list \
  --project=cubedev2-lab-1c497b \
  --filter="policyName:dq-failure"

# 7. Restore permissions
gcloud projects add-iam-policy-binding cubedev2-lab-1c497b \
  --member="serviceAccount:service-722471676767@gcp-sa-dataplex.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"
```

**Method 2: Delete Dataset Temporarily**

```bash
# 1. Rename dataset (safer than delete)
bq update --dataset \
  --rename demo_dataset_backup \
  cubedev2-lab-1c497b:demo_dataset

# 2. Trigger scan (will fail - dataset not found)
gcloud dataplex datascans run \
  test-data-product-001-dq-demo_dataset \
  --location=northamerica-northeast1 \
  --project=cubedev2-lab-1c497b

# 3. Wait for alert email (2-5 minutes)

# 4. Rename back
bq update --dataset \
  --rename demo_dataset \
  cubedev2-lab-1c497b:demo_dataset_backup
```

**Expected Result**:
- Alert fires within 5 minutes
- Email received with subject: `[GCP Alert] Data Quality Scan Failure - test-data-product-001-dq-demo_dataset`
- Email contains troubleshooting steps
- Links to DataScan logs work
- Alert auto-closes after permissions restored and next successful scan

### Test 2: Low Quality Score Alert

**Method 1: Insert Bad Data**

```sql
-- 1. Check current row count
SELECT COUNT(*) FROM `cubedev2-lab-1c497b.demo_dataset.your_table`;

-- 2. Insert all-null rows to drop completeness score
INSERT INTO `cubedev2-lab-1c497b.demo_dataset.your_table`
SELECT NULL as col1, NULL as col2, NULL as col3, ...
FROM UNNEST(GENERATE_ARRAY(1, 10000)) as n;

-- 3. Trigger quality scan
-- (via gcloud command or wait for scheduled run)

-- 4. Wait for scan to complete and quality score to drop below threshold

-- 5. Clean up bad data
DELETE FROM `cubedev2-lab-1c497b.demo_dataset.your_table`
WHERE col1 IS NULL AND col2 IS NULL AND col3 IS NULL;
```

**Method 2: Temporarily Lower Threshold**

```yaml
# In your Pulumi configuration, temporarily set very high threshold
qualityScoreThreshold: 0.99  # 99% - almost impossible to achieve

# Deploy and wait for next scan
pulumi up

# Should trigger low score alert

# Restore normal threshold
qualityScoreThreshold: 0.8

# Deploy again
pulumi up
```

**Expected Result**:
- Alert fires when quality score < threshold
- Email shows actual score vs threshold
- Links to scan results work
- Alert auto-closes when quality improves

### Test 3: Scan Staleness Alert

**Method 1: Pause Cloud Scheduler**

```bash
# 1. Pause the scheduler job
gcloud scheduler jobs pause \
  test-data-product-001-dq-demo_dataset-scheduler \
  --location=northamerica-northeast1 \
  --project=cubedev2-lab-1c497b

# 2. Wait 48 hours (or modify alert condition temporarily for testing)

# 3. Alert should fire after 48 hours of no successful scans

# 4. Resume scheduler
gcloud scheduler jobs resume \
  test-data-product-001-dq-demo_dataset-scheduler \
  --location=northamerica-northeast1 \
  --project=cubedev2-lab-1c497b
```

**Method 2: Delete Scheduler Job Temporarily**

```bash
# 1. Note the scheduler configuration first
gcloud scheduler jobs describe \
  test-data-product-001-dq-demo_dataset-scheduler \
  --location=northamerica-northeast1 \
  --project=cubedev2-lab-1c497b > /tmp/scheduler_backup.yaml

# 2. Delete scheduler (DataScan won't run)
gcloud scheduler jobs delete \
  test-data-product-001-dq-demo_dataset-scheduler \
  --location=northamerica-northeast1 \
  --project=cubedev2-lab-1c497b

# 3. Wait 48 hours

# 4. Recreate via Pulumi or gcloud
pulumi up  # Will recreate the scheduler
```

**Expected Result**:
- Alert fires after 48 hours of staleness
- Email explains scheduler may be disabled
- Links to Cloud Scheduler work
- Alert auto-closes when scan runs successfully again

---

## Phase 3: Verify Alert Content

### 3.1 Email Content Checklist

When you receive a test alert email, verify:

**Subject Line**:
- [ ] Contains alert type (Failure/Low Score/Stale)
- [ ] Contains scan ID
- [ ] Prefixed with `[GCP Alert]`

**Email Body**:
- [ ] Shows data product name
- [ ] Shows scan ID
- [ ] Lists possible causes
- [ ] Provides recommended actions
- [ ] Includes working link to DataScan details
- [ ] Includes working link to logs (for failure alerts)
- [ ] Formatted with markdown (headings, bullets, etc.)

**Links**:
- [ ] DataScan details link opens correct resource
- [ ] Cloud Logging link shows relevant logs
- [ ] Cloud Scheduler link (if applicable) works

### 3.2 Alert Behavior Checklist

**Rate Limiting**:
- [ ] Only 1 alert per hour for same failure (not spammed)
- [ ] Staleness alert limited to 1 per 6 hours

**Auto-Close**:
- [ ] Alert auto-closes within 24 hours if not resolved
- [ ] Alert closes immediately when issue is fixed and scan succeeds

**Incident Tracking**:
- [ ] Incident visible in Cloud Monitoring console
- [ ] Incident shows duration and timeline
- [ ] Incident logs policy name and condition

---

## Quick Testing Script

Here's a bash script to run all verification checks:

```bash
#!/bin/bash
# test-dq-alerts.sh

PROJECT="cubedev2-lab-1c497b"
LOCATION="northamerica-northeast1"
DATA_PRODUCT_ID="test-data-product-001"
DATASET="demo_dataset"

echo "=== Data Quality Alert Testing ==="
echo

echo "[1/4] Checking notification channels..."
gcloud alpha monitoring channels list \
  --project=$PROJECT \
  --filter="displayName:Data Quality" \
  --format="table(displayName,labels.email_address,enabled)"
echo

echo "[2/4] Checking alert policies..."
gcloud alpha monitoring policies list \
  --project=$PROJECT \
  --filter="displayName:Data Quality" \
  --format="table(displayName,enabled)" | head -10
echo

echo "[3/4] Checking for active incidents..."
gcloud alpha monitoring policies incidents list \
  --project=$PROJECT \
  --filter="state=OPEN" \
  --format="table(name,startTime,policyName)"
echo

echo "[4/4] Checking DataScans..."
gcloud dataplex datascans list \
  --location=$LOCATION \
  --project=$PROJECT \
  --filter="dataProductId:$DATA_PRODUCT_ID" \
  --format="table(name,state,type)"
echo

echo "=== Test Complete ==="
echo
echo "Next steps:"
echo "1. Trigger a test alert using methods in TESTING-DATA-QUALITY-ALERTS.md"
echo "2. Check email inbox for alert notification"
echo "3. Verify alert content and links"
echo "4. Confirm alert auto-closes after resolution"
```

Save and run:
```bash
chmod +x test-dq-alerts.sh
./test-dq-alerts.sh
```

---

## Automated Integration Testing

For CI/CD pipelines, here's a Python test script:

```python
#!/usr/bin/env python3
"""
Integration test for data quality alerting.
"""

import subprocess
import json
import time
from typing import Dict, List

PROJECT = "cubedev2-lab-1c497b"
LOCATION = "northamerica-northeast1"
DATA_PRODUCT_ID = "test-data-product-001"

def run_gcloud(args: List[str]) -> Dict:
    """Run gcloud command and return JSON output."""
    cmd = ["gcloud"] + args + ["--format=json"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)

def test_notification_channel_created():
    """Test that notification channel was created."""
    channels = run_gcloud([
        "alpha", "monitoring", "channels", "list",
        f"--project={PROJECT}",
        "--filter=displayName:Data Quality"
    ])

    assert len(channels) > 0, "No notification channels found"

    channel = channels[0]
    assert "email_address" in channel["labels"], "Email not configured"
    assert channel["enabled"], "Channel not enabled"

    print("✓ Notification channel created and enabled")

def test_alert_policies_created():
    """Test that all alert policies were created."""
    policies = run_gcloud([
        "alpha", "monitoring", "policies", "list",
        f"--project={PROJECT}",
        "--filter=displayName:Data Quality"
    ])

    # Should have 3 policies per dataset
    assert len(policies) >= 3, f"Expected >= 3 policies, found {len(policies)}"

    policy_types = {
        "Failure": False,
        "Low": False,
        "Stale": False
    }

    for policy in policies:
        name = policy["displayName"]
        if "Failure" in name:
            policy_types["Failure"] = True
        if "Low" in name:
            policy_types["Low"] = True
        if "Stale" in name:
            policy_types["Stale"] = True

        assert policy["enabled"], f"Policy {name} not enabled"

    assert all(policy_types.values()), f"Missing policy types: {policy_types}"

    print(f"✓ All {len(policies)} alert policies created and enabled")

def test_trigger_failure_alert():
    """Trigger a scan failure alert by running with bad permissions."""
    print("Testing scan failure alert...")

    # This would require actually modifying permissions
    # For safety, we'll just verify the policy exists and is configured correctly

    policies = run_gcloud([
        "alpha", "monitoring", "policies", "list",
        f"--project={PROJECT}",
        "--filter=displayName:Failure"
    ])

    assert len(policies) > 0, "Failure alert policy not found"

    policy = policies[0]
    assert policy["conditions"], "No conditions configured"
    assert policy["notificationChannels"], "No notification channels attached"

    print("✓ Failure alert policy configured correctly")

if __name__ == "__main__":
    print("=== Data Quality Alert Integration Tests ===\n")

    try:
        test_notification_channel_created()
        test_alert_policies_created()
        test_trigger_failure_alert()

        print("\n✓ All tests passed!")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        exit(1)
```

Run with:
```bash
python test_dq_alerts_integration.py
```

---

## Troubleshooting Tests

### Alert Not Firing

**Check**:
1. Alert policy is enabled
2. Notification channel is enabled
3. Email address is correct
4. Condition is actually met
5. Rate limit hasn't been hit

**Debug**:
```bash
# Check policy details
gcloud alpha monitoring policies describe {POLICY_NAME} \
  --project=cubedev2-lab-1c497b

# Check recent incidents
gcloud alpha monitoring policies incidents list \
  --project=cubedev2-lab-1c497b \
  --filter="policyName:{POLICY_NAME}"

# Check logs for alert evaluations
gcloud logging read \
  'resource.type="gce_instance" AND jsonPayload.policy_name=~"Data Quality"' \
  --project=cubedev2-lab-1c497b \
  --limit=20
```

### Email Not Received

**Check**:
1. Spam folder
2. Email address typo
3. Google Group membership (if using distribution list)
4. Notification channel verified

**Test email delivery**:
```bash
# Test notification channel
gcloud alpha monitoring channels test {CHANNEL_NAME} \
  --project=cubedev2-lab-1c497b
```

### Links Not Working

**Verify**:
- Project ID is correct in URLs
- Scan ID is correct
- Location is correct
- User has permissions to view resources

---

## Testing Checklist

Use this checklist when testing the alerting feature:

### Pre-Deployment
- [ ] Review Pulumi configuration
- [ ] Verify email address is correct
- [ ] Check threshold values are reasonable

### Post-Deployment
- [ ] Notification channel created
- [ ] 3 alert policies per dataset created
- [ ] All policies enabled
- [ ] Notification channels attached to policies

### Alert Testing
- [ ] Scan failure alert triggered and received
- [ ] Low quality score alert triggered and received
- [ ] Scan staleness alert triggered and received
- [ ] Email content is correct
- [ ] All links work
- [ ] Alerts auto-close after resolution

### Cleanup
- [ ] Test datasets/resources removed
- [ ] Permissions restored
- [ ] Schedulers re-enabled
- [ ] No lingering test data

---

## Next Steps

After successful testing:

1. **Document Runbooks**: Create team runbooks for each alert type
2. **Set Up Dashboards**: Create monitoring dashboards for quality scores
3. **Train Team**: Ensure team knows how to respond to alerts
4. **Monitor Alert Volume**: Track alert frequency over first week
5. **Tune Thresholds**: Adjust based on real-world data quality patterns

## Related Documentation

- [Data Quality Quick Start](./DATA-QUALITY-QUICK-START.md)
- [Data Quality Alerting Guide](./DATA-QUALITY-ALERTING.md)
- [Standardized Data Quality Design](./STANDARDIZED-DATA-QUALITY.md)
