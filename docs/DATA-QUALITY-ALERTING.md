# Data Quality Alerting

## Overview

Automatic email alerting for data quality issues, integrated with GCP Cloud Monitoring.

## Quick Start

```yaml
resources:
  myDataProduct:
    type: dataproducts:index:DataProductWithAspects
    properties:
      # ... required fields ...

      # Enable quality scans
      enableDataQualityScans: true
      bigqueryDatasets:
        - my_dataset

      # Add email to automatically enable alerts
      dataQualityAlertEmail: "data-team@company.com"
```

That's it! Alerts are automatically configured when you provide an email address.

## Configuration Options

### Basic Alerting

```yaml
# Use component-wide alert email
alertEmail: "alerts@company.com"
enableDataQualityScans: true
```

### Dedicated Data Quality Email

```yaml
# Separate email for data quality alerts
dataQualityAlertEmail: "dq-team@company.com"
enableDataQualityScans: true
```

This is useful when you want quality alerts to go to a different team than other alerts.

### Custom Alert Threshold

```yaml
dataQualityAlertEmail: "dq-team@company.com"
qualityScoreThreshold: 0.9  # Alert if quality < 90% (default: 0.8)
```

### Distribution Lists

Use Google Groups for team-wide alerting:

```yaml
dataQualityAlertEmail: "data-quality-alerts@company.com"
```

## Alert Types

### 1. Scan Failure Alert

**Triggers when**: DataScan job fails to execute

**Email includes**:
- Data product and scan details
- Possible causes (permissions, config, resources)
- Recommended troubleshooting steps
- Direct link to DataScan logs

**Rate limit**: Max 1 alert per hour per scan
**Auto-close**: After 24 hours

**Example scenarios**:
- BigQuery dataset deleted or not accessible
- Invalid quality rules configuration
- Insufficient service account permissions
- Dataplex API errors

### 2. Low Quality Score Alert

**Triggers when**: Quality score drops below threshold (default: 80%)

**Email includes**:
- Current quality score
- Configured threshold
- Affected quality dimensions
- Possible root causes
- Direct link to scan results

**Rate limit**: Max 1 alert per hour per scan
**Auto-close**: After 24 hours

**Example scenarios**:
- Data completeness drops (missing records)
- Freshness issues (stale data)
- Validity failures (schema changes, bad data)
- Upstream pipeline failures

### 3. Scan Staleness Alert

**Triggers when**: No successful scan execution in 48 hours

**Email includes**:
- Data product and scan details
- Last successful execution time
- Possible scheduler issues
- Direct link to Cloud Scheduler

**Rate limit**: Max 1 alert per 6 hours per scan
**Auto-close**: After 24 hours

**Example scenarios**:
- Cloud Scheduler job disabled
- Scheduler job failures
- DataScan resource deleted
- Service account permission revoked

## Alert Email Format

### Subject Line
```
[GCP Alert] Data Quality Scan Failure - prod-analytics-001-dq-analytics_prod
```

### Email Body
```markdown
## Data Quality Scan Failure

**Data Product**: Production Analytics
**Scan**: prod-analytics-001-dq-analytics_prod
**Project**: cubedev2-lab-1c497b
**Location**: northamerica-northeast1

A data quality scan has failed to complete successfully.

### Possible Causes:
- BigQuery dataset or table not accessible
- Invalid quality rules configuration
- Insufficient permissions
- Resource unavailable

### Recommended Actions:
1. Check the DataScan logs in Cloud Logging
2. Verify BigQuery dataset exists and is accessible
3. Review quality rules configuration
4. Check service account permissions

### View Scan Details:
https://console.cloud.google.com/dataplex/process/data-scans/prod-analytics-001-dq-analytics_prod?project=cubedev2-lab-1c497b

### View Logs:
https://console.cloud.google.com/logs/query?project=cubedev2-lab-1c497b&query=resource.type%3D%22dataplex.googleapis.com%2FDataScan%22%0Aresource.labels.data_scan_id%3D%22prod-analytics-001-dq-analytics_prod%22

---
Incident ID: 7c8a9b2f-1234-5678-abcd-ef1234567890
Alert Policy: Data Quality Scan Failure - prod-analytics-001-dq-analytics_prod
```

## Alert Configuration Details

### Notification Channel

A single notification channel is created per data product:

**Resource Name**: `{dataProductId}-dq-alert-channel`
**Type**: Email
**Display Name**: `{displayName} - Data Quality Alerts`

### Alert Policies

3 alert policies per DataScan (quality scan):

| Policy | Resource Name | Condition Type |
|--------|---------------|----------------|
| Failure | `{dataProductId}-dq-failure-{dataset}` | Log match |
| Low Score | `{dataProductId}-dq-low-score-{dataset}` | Log match |
| Staleness | `{dataProductId}-dq-stale-{dataset}` | Log match |

### Alert Strategy

All alerts use:
- **Auto-close**: 86400s (24 hours)
- **Combiner**: OR (any condition triggers)
- **Enabled**: True by default

**Rate Limits** (per alert type):
- Scan Failure: 3600s (1 hour)
- Low Quality Score: 3600s (1 hour)
- Scan Staleness: 21600s (6 hours)

## Multi-Dataset Example

For a data product with multiple datasets:

```yaml
enableDataQualityScans: true
dataQualityAlertEmail: "dq-team@company.com"
bigqueryDatasets:
  - analytics_prod
  - reports_prod
  - staging_data
```

**Creates**:
- 1 notification channel
- 9 alert policies (3 per dataset)
- Alerts for all 3 datasets go to same email

## Viewing Alerts

### In Cloud Monitoring Console

1. Navigate to **Monitoring** > **Alerting**
2. Filter by: `Display Name contains "Data Quality"`
3. View alert status, history, incidents

### Alert History

Each alert maintains history showing:
- When it fired
- Duration of incident
- Auto-close events
- Manual acknowledgments

### Incident Dashboard

Access incident details:
```
https://console.cloud.google.com/monitoring/alerting/incidents?project={project}
```

## Testing Alerts

### Trigger a Scan Failure Alert

1. Temporarily revoke BigQuery permissions
2. Wait for next scan execution
3. Alert should fire within minutes
4. Restore permissions
5. Alert auto-closes after next successful scan

### Trigger a Low Quality Score Alert

1. Inject bad data into BigQuery dataset
2. Wait for next scan execution
3. If quality score < threshold, alert fires
4. Fix data quality issue
5. Alert auto-closes after next passing scan

### Trigger a Staleness Alert

1. Pause the Cloud Scheduler job
2. Wait 48 hours
3. Alert fires after 48 hours of no successful scans
4. Resume scheduler
5. Alert auto-closes after next successful scan

## Troubleshooting

### Not Receiving Alerts

**Check**:
1. Email address is correct in configuration
2. Notification channel created successfully
3. Alert policies are enabled
4. Email isn't being filtered to spam
5. Google Group membership (if using distribution list)

**Verify in Console**:
```bash
# List notification channels
gcloud alpha monitoring channels list --project={project}

# List alert policies
gcloud alpha monitoring policies list --project={project} --filter="displayName:Data Quality"
```

### Too Many Alerts

**Solutions**:
1. Increase `qualityScoreThreshold` to reduce sensitivity
2. Fix underlying data quality issues
3. Adjust rate limits (requires manual policy modification)
4. Use separate emails for different criticality levels

### Alerts Not Auto-Closing

**Possible causes**:
- Issue not actually resolved
- Next scan hasn't run yet
- Scan still failing for different reason

**Check**:
- View latest scan results in Dataplex
- Check scheduler execution history
- Review scan logs for new errors

## Cost

### Notification Channels
- Free (no charge)

### Alert Policies
- First 100 rules: Free
- Additional rules: $0.02 per rule per month

**Example**:
- 2 datasets = 6 alert policies
- Well within free tier
- $0/month cost

### Email Delivery
- Free (unlimited emails)

## Security

### Email Delivery

Emails are sent via Google Cloud's trusted email service:
- From: `noreply@google.com`
- SPF/DKIM authenticated
- Safe to whitelist

### Sensitive Information

Alert emails contain:
- Resource names (scan IDs, dataset IDs)
- Project IDs and locations
- Console URLs

**DO NOT include**:
- Actual data values
- Credentials or secrets
- PII or sensitive business data

## Best Practices

1. **Use Distribution Lists**: Route alerts to team aliases, not individual emails
2. **Set Appropriate Thresholds**: Start with 0.8 (80%) and adjust based on alert fatigue
3. **Monitor Alert Volume**: If getting too many alerts, investigate root causes
4. **Document Runbooks**: Create team runbooks for each alert type
5. **Test Regularly**: Periodically test alerts to ensure they're working
6. **Review Incidents**: Weekly review of incident history to identify patterns

## Integration with Incident Management

### PagerDuty Integration

Configure PagerDuty notification channel instead of email:

```yaml
# Note: Requires manual PagerDuty channel creation
# Then reference in component (future enhancement)
```

### Slack Integration

Route alerts to Slack channels (future enhancement):

```yaml
# Future: Direct Slack notification support
# For now: Use email-to-Slack forwarding
```

## Next Steps

- [Quick Start Guide](./DATA-QUALITY-QUICK-START.md)
- [Standardized Quality Rules](./STANDARDIZED-DATA-QUALITY.md)
- [GCP Cloud Monitoring Documentation](https://cloud.google.com/monitoring/docs)
