# Standardized Data Quality Scan Design

## Overview

This document describes the standardized data quality scan configuration that can be enabled by default for all data products in the component.

## Design Principles

1. **Generic Applicability** - Rules work across any BigQuery dataset without knowing column names
2. **Comprehensive Coverage** - Cover all 7 quality dimensions (Freshness, Volume, Completeness, Validity, Consistency, Accuracy, Uniqueness)
3. **Actionable Metrics** - Provide metrics that can be trended and alerted on
4. **Low Maintenance** - Minimal per-dataset configuration required

## Quality Dimensions Coverage

### 1. Volume (Table-level)
**Purpose**: Detect unexpected data volume changes (outages, duplicates, pipeline issues)

**Rules**:
- `table_condition_expectation`: Row count is greater than zero
  ```sql
  COUNT(*) > 0
  ```
- `table_condition_expectation`: Row count within expected range (with threshold)
  ```sql
  COUNT(*) >= (SELECT COUNT(*) * 0.8 FROM `{dataset}.{table}` WHERE _PARTITIONTIME = CURRENT_DATE() - 1)
  ```

### 2. Freshness (Table-level)
**Purpose**: Ensure data is recent and pipelines are running

**Rules**:
- `table_condition_expectation`: Data modified in last 24 hours (for daily refresh)
  ```sql
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(),
    (SELECT MAX(_PARTITIONTIME) FROM `{dataset}.{table}`),
    HOUR) < 24
  ```
- `table_condition_expectation`: Latest partition is recent
  ```sql
  DATE_DIFF(CURRENT_DATE(),
    (SELECT MAX(DATE(_PARTITIONTIME)) FROM `{dataset}.{table}`),
    DAY) <= 1
  ```

### 3. Completeness (Row-level + Table-level)
**Purpose**: Measure overall data completeness across all columns

**Rules**:
- `table_condition_expectation`: Overall non-null percentage threshold
  ```sql
  (SELECT AVG(CASE
    WHEN column IS NOT NULL THEN 1
    ELSE 0
  END)
  FROM UNNEST(TO_JSON_STRING(t)) AS column, `{dataset}.{table}` t) >= 0.95
  ```
- `row_condition_expectation`: At least one non-null value per row
  ```sql
  -- Row has at least one populated field
  EXISTS (SELECT 1 FROM UNNEST(TO_JSON_STRING(t)) AS col WHERE col IS NOT NULL)
  ```

### 4. Validity (Row-level)
**Purpose**: Detect data type issues and format problems

**Rules**:
- `row_condition_expectation`: No obviously invalid patterns (configurable per use case)
  ```sql
  -- Example: No negative timestamps, reasonable date ranges
  TRUE  -- Placeholder for schema-specific validation
  ```

### 5. Consistency (Table-level)
**Purpose**: Detect duplicate records and referential integrity issues

**Rules**:
- `table_condition_expectation`: Duplicate detection (if table has natural keys)
  ```sql
  -- Detect if duplicate rate is below threshold
  (SELECT COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t))
   FROM `{dataset}.{table}` t) / COUNT(*) < 0.01
  ```

### 6. Uniqueness (Table-level)
**Purpose**: Measure data cardinality and uniqueness

**Rules**:
- `table_condition_expectation`: Reasonable distinct count
  ```sql
  COUNT(DISTINCT TO_JSON_STRING(t)) > 0
  ```

## Default Scan Configuration

### Standard Configuration
```json
{
  "data_quality_spec": {
    "sampling_percent": 100,
    "row_filter": null,
    "post_scan_actions": {
      "bigquery_export": {
        "results_table": "projects/{project}/datasets/data_quality_results/tables/dq_results"
      }
    },
    "rules": [
      {
        "dimension": "VOLUME",
        "name": "table_has_data",
        "description": "Table contains at least one row",
        "table_condition_expectation": {
          "sql_expression": "COUNT(*) > 0"
        },
        "threshold": 1.0
      },
      {
        "dimension": "FRESHNESS",
        "name": "data_is_recent_24h",
        "description": "Data has been updated in the last 24 hours",
        "table_condition_expectation": {
          "sql_expression": "TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), (SELECT MAX(TIMESTAMP(CAST(_PARTITIONTIME AS STRING))) FROM `{table}`), HOUR) < 24"
        },
        "threshold": 1.0,
        "ignore_null": true
      },
      {
        "dimension": "COMPLETENESS",
        "name": "overall_completeness_95pct",
        "description": "At least 95% of all fields are non-null across the table",
        "threshold": 0.95
      },
      {
        "dimension": "CONSISTENCY",
        "name": "low_duplicate_rate",
        "description": "Duplicate rate is below 1%",
        "table_condition_expectation": {
          "sql_expression": "((SELECT COUNT(*) FROM `{table}`) - (SELECT COUNT(DISTINCT TO_JSON_STRING(t)) FROM `{table}` t)) / (SELECT COUNT(*) FROM `{table}`) < 0.01"
        },
        "threshold": 1.0
      },
      {
        "dimension": "VALIDITY",
        "name": "no_null_only_rows",
        "description": "No rows with all null values",
        "row_condition_expectation": {
          "sql_expression": "TRUE"
        },
        "threshold": 1.0
      }
    ]
  }
}
```

### Enhanced Configuration (with Auto Data Quality)
For datasets where we want deeper insights, enable Auto Data Quality profiling:

```json
{
  "data_quality_spec": {
    "sampling_percent": 100,
    "post_scan_actions": {
      "bigquery_export": {
        "results_table": "projects/{project}/datasets/data_quality_results/tables/dq_results"
      }
    }
  },
  "data_profile_spec": {
    "sampling_percent": 100,
    "row_filter": null
  }
}
```

This enables automatic:
- Column-level null percentage tracking
- Distinct value counts
- Min/max/mean for numeric columns
- String length distribution
- Data type conformance

## Scheduling

**Default Schedule**: Daily at 2 AM (`0 2 * * *`)

**Rationale**:
- Runs after typical nightly batch processes
- Provides daily quality trend data
- Avoids peak business hours

**Alternative Schedules**:
- High-frequency data: `0 */6 * * *` (every 6 hours)
- Weekly summary: `0 2 * * 1` (Mondays at 2 AM)

## Metrics and Monitoring

### Standard Metrics Tracked
1. **Pass Rate by Dimension** - % of rules passing per quality dimension
2. **Overall Quality Score** - Weighted average across all dimensions
3. **Row-level Pass Rate** - % of rows passing all row-level rules
4. **Table-level Pass Rate** - % of table-level rules passing

### Alerting Thresholds
- **Critical**: Overall quality score < 80%
- **Warning**: Overall quality score < 95%
- **Info**: Any dimension score < 100%

### Trend Analysis
Track quality scores over time to detect:
- Gradual degradation (slow data quality decay)
- Sudden drops (pipeline/schema changes)
- Seasonal patterns (expected variations)

## Export and Visualization

### BigQuery Export
All scan results are exported to a standardized table:
```
projects/{project}/datasets/data_quality_results/tables/dq_results
```

Schema:
- `scan_time` - When the scan ran
- `data_asset` - Dataset/table being scanned
- `dimension` - Quality dimension (VOLUME, FRESHNESS, etc.)
- `rule_name` - Specific rule identifier
- `passed` - Boolean pass/fail
- `pass_rate` - Percentage (for row-level rules)
- `null_count` - Number of null values encountered

### Dashboard Integration
Can be visualized in:
- Looker Studio dashboards
- Custom BigQuery SQL queries
- Dataplex UI (native results viewer)

## Implementation in Component

### Component Args (New)
```python
# Data Quality Scan Configuration
enableStandardizedDataQuality: NotRequired[Input[bool]]
"""Enable standardized data quality scans with default rules (default: False)"""

dataQualityScanLevel: NotRequired[Input[str]]
"""Quality scan level: 'basic' (table-level only), 'standard' (default rules), 'enhanced' (includes profiling)"""

qualityScanSchedule: NotRequired[Input[str]]
"""Cron schedule for quality scans (default: '0 2 * * *' - daily 2 AM)"""

dataQualityAlerting: NotRequired[Input[bool]]
"""Enable alerting on quality score thresholds (default: False)"""

dataQualityAlertThreshold: NotRequired[Input[float]]
"""Quality score threshold for alerts (default: 0.8 = 80%)"""
```

### Default Behavior
- If `enableStandardizedDataQuality: true`, automatically creates scans for all `bigqueryDatasets`
- Uses `dataQualityScanLevel: 'standard'` by default
- Creates Cloud Scheduler jobs to run on schedule
- Exports results to project-level `data_quality_results` dataset

## Benefits

1. **Zero Configuration** - Works out of the box for any dataset
2. **Consistent Metrics** - Same quality dimensions across all data products
3. **Trend Visibility** - Historical quality data for all assets
4. **Early Detection** - Catches issues before they impact downstream consumers
5. **Compliance Ready** - Quality metrics support data governance requirements

## Future Enhancements

1. **ML-based Anomaly Detection** - Use historical quality scores to detect anomalies
2. **Auto-remediation** - Trigger cleanup jobs when quality drops
3. **Custom Rule Libraries** - Domain-specific rules (PII detection, business rules)
4. **Quality SLAs** - Enforce minimum quality scores via policy
5. **Cross-product Consistency** - Compare quality across related data products

## References

- [Auto data quality overview | Knowledge Catalog | Google Cloud](https://docs.cloud.google.com/dataplex/docs/auto-data-quality-overview)
- [DataQualityRule API Reference](https://docs.cloud.google.com/dataplex/docs/reference/rest/v1/DataQualityRule)
- [Reuse data quality rules](https://docs.cloud.google.com/dataplex/docs/reuse-data-quality-rules)
