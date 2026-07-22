# Data Quality Quick Start Guide

## Overview

The component now supports standardized data quality scans that automatically monitor your BigQuery datasets with minimal configuration.

## Enable Standardized Data Quality (Recommended)

### Basic Configuration
Add these properties to your data product configuration:

```yaml
resources:
  myDataProduct:
    type: dataproducts:index:DataProductWithAspects
    properties:
      # ... existing required fields ...

      # Enable standardized data quality
      enableDataQualityScans: true
      bigqueryDatasets:
        - my_dataset_id
        - another_dataset
```

This will:
- Create daily quality scans (2 AM) for each BigQuery dataset
- Use standardized rules covering 5 quality dimensions (Volume, Freshness, Completeness, Validity, Consistency)
- Create Cloud Scheduler jobs to trigger scans automatically
- Work with any dataset without column-specific configuration

### Enhanced Configuration (with Profiling)

For deeper insights, enable data profiling to get automatic column-level statistics:

```yaml
resources:
  myDataProduct:
    type: dataproducts:index:DataProductWithAspects
    properties:
      # ... existing required fields ...

      # Enable both quality scans and profiling
      enableDataQualityScans: true
      enableDataProfiling: true
      profilingSamplingPercent: 100  # Optional: 1-100 (default: 100)

      bigqueryDatasets:
        - my_dataset_id
```

Data profiling provides:
- Null percentages per column
- Distinct value counts
- Min/max values for numeric columns
- String length distributions
- Data type conformance

### Enable Alerting (Recommended)

Get notified when data quality issues occur by simply adding an email address:

```yaml
resources:
  myDataProduct:
    type: dataproducts:index:DataProductWithAspects
    properties:
      # ... existing required fields ...

      # Enable quality scans with automatic alerting
      enableDataQualityScans: true
      dataQualityAlertEmail: "data-team@company.com"  # Alerts auto-enabled

      # Optional: Custom alert threshold (default: 0.8 = 80%)
      qualityScoreThreshold: 0.9  # Alert if quality drops below 90%

      bigqueryDatasets:
        - my_dataset_id
```

**How it works:** Alerts are automatically enabled when you provide an email address via `dataQualityAlertEmail` or `alertEmail`.

This creates **3 alert types per dataset**:

1. **Scan Failure Alert** - Notifies when a scan fails to run
2. **Low Quality Score Alert** - Notifies when quality drops below threshold
3. **Scan Staleness Alert** - Notifies when scan hasn't run in 48 hours

**Alert Emails Include:**
- Direct links to Dataplex Console for investigation
- Possible causes and recommended actions
- Severity and affected data product details

### Custom Schedule

Change the scan frequency:

```yaml
# Every 6 hours (high-frequency data)
qualityScanSchedule: "0 */6 * * *"

# Weekly on Mondays at 2 AM
qualityScanSchedule: "0 2 * * 1"

# Daily at 2 AM (default)
qualityScanSchedule: "0 2 * * *"
```

### Custom Quality Rules

Override the default rules with your own:

```yaml
enableDataQualityScans: true
qualityRules:
  - dimension: "COMPLETENESS"
    name: "customer_id_not_null"
    description: "Customer ID must always be populated"
    non_null_expectation:
      column: "customer_id"
    threshold: 1.0

  - dimension: "VALIDITY"
    name: "amount_positive"
    description: "Amount must be positive"
    range_expectation:
      column: "amount"
      min_value: "0"
    threshold: 0.95  # 95% of rows must pass
```

## What Gets Created

When you enable `enableDataQualityScans: true`:

### Per BigQuery Dataset:
1. **Data Quality Scan** (`{dataProductId}-dq-{dataset_id}`)
   - Runs standardized quality rules
   - Checks: Volume, Freshness, Completeness, Validity, Consistency

2. **Data Profile Scan** (if `enableDataProfiling: true`)
   - Runs column-level statistical profiling
   - Generates automatic statistics for all columns

3. **Cloud Scheduler Jobs**
   - One job per scan to trigger on schedule
   - Named: `{dataProductId}-dq-{dataset_id}-scheduler`

4. **Alert Policies** (if `dataQualityAlertEmail` or `alertEmail` is set)
   - **Scan Failure Alert**: Detects when scan execution fails
   - **Low Quality Score Alert**: Triggers when score < threshold
   - **Scan Staleness Alert**: Detects when scan hasn't run in 48h
   - One notification channel for email alerts
   - **Note**: Alerts are automatically enabled when an email is provided

## Default Quality Rules

The standardized default rules cover:

### 1. VOLUME
- **table_has_data**: Ensures table contains at least one row
- Detects: Empty tables, pipeline failures

### 2. FRESHNESS
- **data_updated_recently**: Data modified in last 48 hours
- Applies to: Partitioned tables
- Detects: Stale data, pipeline delays

### 3. COMPLETENESS
- **table_not_empty**: Table has rows
- Detects: Missing data, load failures

### 4. VALIDITY
- **rows_exist**: Table has valid rows
- Detects: All-null scenarios, corrupted data

### 5. CONSISTENCY
- Future: Duplicate detection rules
- Detects: Data duplication, referential integrity issues

## Alert Configuration

### Alert Email Format

When a quality issue is detected, you'll receive an email with:

**Subject**: `Data Quality Scan Failure - {scan_id}` (or Low Score / Stale)

**Body**:
```markdown
## Data Quality Scan Failure

**Data Product**: Production Analytics
**Scan**: prod-analytics-001-dq-analytics_prod

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
https://console.cloud.google.com/dataplex/process/data-scans/prod-analytics-001-dq-analytics_prod?project=my-project
```

### Alert Types Details

| Alert Type | Trigger Condition | Auto-Close | Rate Limit |
|------------|------------------|------------|------------|
| **Scan Failure** | DataScan job fails with error | 24 hours | Max 1/hour |
| **Low Quality Score** | Quality score < threshold | 24 hours | Max 1/hour |
| **Scan Staleness** | No successful run in 48 hours | 24 hours | Max 1/6 hours |

### Distribution Lists

You can use Google Groups as distribution lists:

```yaml
dataQualityAlertEmail: "data-quality-alerts@company.com"
```

This allows:
- Team-wide visibility of quality issues
- Easy membership management
- Historical email archive

## Viewing Results

### In GCP Console
1. Navigate to **Dataplex** > **Data Scans**
2. Find scans named: `{dataProductId}-dq-{dataset_id}`
3. Click to view:
   - Pass/fail status
   - Quality score by dimension
   - Individual rule results
   - Historical trends

### In BigQuery
Quality results are automatically exported (future enhancement):
```sql
SELECT
  scan_time,
  data_asset,
  dimension,
  rule_name,
  passed,
  pass_rate
FROM `{project}.data_quality_results.dq_results`
WHERE data_asset LIKE '%my_dataset%'
ORDER BY scan_time DESC
LIMIT 100;
```

## Cost Considerations

### Data Quality Scans
- Charged per GB of data scanned
- Default: 100% sampling (scans all data)
- Optimization: Use sampling for large datasets

### Data Profiling
- Similar pricing to quality scans
- Use `profilingSamplingPercent` to reduce cost
- Example: `profilingSamplingPercent: 10` = 90% cost reduction

### Cloud Scheduler
- Minimal cost (~$0.10/month per job)
- One job per scan
- Example: 2 datasets × 2 scans = 4 jobs = $0.40/month

## Troubleshooting

### Scan fails with "Table not found"
- Ensure `bigqueryDatasets` contains dataset IDs, not full paths
- Correct: `analytics_prod`
- Incorrect: `projects/my-project/datasets/analytics_prod`

### Freshness rule always fails
- Freshness rule only applies to partitioned tables
- Non-partitioned tables: Rule is ignored (set `ignore_null: true`)

### Want to disable specific rules
- Override `qualityRules` with your custom rule list
- Omit unwanted dimensions entirely

## Best Practices

1. **Start with defaults**: Enable `enableDataQualityScans: true` for all data products
2. **Add profiling selectively**: Use `enableDataProfiling: true` for critical datasets
3. **Monitor trends**: Quality scores should be stable over time
4. **Set alerts**: Configure monitoring when scores drop below thresholds
5. **Review failures**: Investigate rule failures within 24 hours

## Complete Example

```yaml
name: my-data-product
runtime: yaml

resources:
  productionDataProduct:
    type: dataproducts:index:DataProductWithAspects
    properties:
      # Required fields
      project: my-gcp-project
      projectNumber: "123456789012"
      location: northamerica-northeast1
      dataProductId: prod-analytics-001
      displayName: Production Analytics
      description: Core analytics data product

      # Business metadata
      businessDomain: Analytics
      businessOwner: data-owner@company.com
      businessPurpose: Executive reporting and analytics

      # Technical metadata
      technicalOwner: data-platform@company.com
      technicalContact: platform-oncall@company.com

      # Compliance
      dataClassification: confidential
      retentionJustification: 7 year retention for financial data

      # Dataplex resources
      lakeName: data-products
      zoneName: raw-assets

      # Data assets
      bigqueryDatasets:
        - analytics_prod
        - reports_prod

      # Standardized data quality (RECOMMENDED)
      enableDataQualityScans: true
      enableDataProfiling: true
      qualityScanSchedule: "0 2 * * *"  # Daily at 2 AM

      # Automatic alerting (alerts enabled when email is present)
      dataQualityAlertEmail: "data-quality-team@company.com"
      qualityScoreThreshold: 0.85  # Alert if quality < 85%

      # Cloud Scheduler
      useCloudSchedulerForScans: true
      schedulerTimeZone: America/Toronto

outputs:
  dataProductId: ${productionDataProduct.dataProductId}
  qualityScans: ${productionDataProduct.quality_scans}
  qualityAlerts: ${productionDataProduct.quality_alerts}
```

## Next Steps

- Review the full design: [STANDARDIZED-DATA-QUALITY.md](./STANDARDIZED-DATA-QUALITY.md)
- Customize rules for your use case
- Set up alerting on quality scores
- Build dashboards to track quality trends
