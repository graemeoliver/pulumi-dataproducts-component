# Dataplex Data Product Component — Build Instructions for Claude Code

## Your Task
Build and validate an isolated Pulumi Python project that implements a new DataProductOrchestrator for the TELUS DataHub 2 platform. This component creates Dataplex Data Products (Knowledge Catalog entries) as a replacement for the existing BigQuery Analytics Hub sharing mechanism (bqsharing).

**Do not modify any existing files. Create all files from scratch exactly as specified below.**

---

## Background

### What This Replaces
`bqsharing` is the current data-access mechanism. It uses Google Analytics Hub to publish BigQuery datasets as listings. It is configured via a `data_sharing:` block in pipeline YAMLs and implemented inside `consumer-data-pipeline/__main__.py`. We are NOT removing it — the new component runs alongside it during a transition period.

### What This Adds
A new `DataProductOrchestrator` that reads an optional `data_product:` block from each pipeline's config and creates:

- A `gcp.dataplex.DataProduct` (always, when `enabled: true`)
- A `gcp.dataplex.DataScan` for Data Quality (optional, when `data_quality.enabled: true`)
- A `gcp.dataplex.DataScan` for Data Profiling (optional, when `data_profiling.enabled: true`)

### Co-existence Strategy
- **Phase 1 (now)**: `data_sharing` + `data_product` both present → create BOTH
- **Phase 2 (later)**: `data_product` only → omit `data_sharing` block
- **Phase 3 (future)**: deprecate `data_sharing` with a warning

---

## Platform Facts — Do Not Deviate From These

| Fact | Value |
|------|-------|
| Python version | >=3.12 |
| pulumi version | 3.225.1 (pinned exactly) |
| pulumi-gcp version | >=8.35.0 |
| Pulumi config namespace | `Config("pipeline")` — all stack keys prefixed `pipeline:` |
| Stack name format | `{env}-{region}-{env_id}-{consumer}-{group}` e.g. `dev-ne1-01-una-group1` |
| BQ dataset naming | `{env}_{region}_{env_id}_{consumer}_{group}_{schema}` e.g. `dev_ne1_01_una_group1_public` |
| Data product ID naming | `{env}_{region}_{env_id}_{consumer}_{group}_{pipeline}` e.g. `dev_ne1_01_una_group_01_customer_sync` |
| Default lake region | `northamerica-northeast1` |
| Pulumi resource reference | https://www.pulumi.com/registry/packages/gcp/api-docs/dataplex/dataproduct/ |

### How Config Is Loaded (mirrors the real __main__.py)
```python
config = pulumi.Config("pipeline")
stack_name = pulumi.get_stack()                         # "dev-ne1-01-una-group1"
environment, region, id_number, *_ = stack_name.split("-")
stack_prefix = f"{environment}-{region}-{id_number}"   # "dev-ne1-01"

lake_project_id = config.require("lake_project_id")
consumer_name   = config.require("consumer_name")
group_name      = config.require("group_name")
location        = config.get("location") or "northamerica-northeast1"
pipelines       = config.get_object("pipelines") or {}
```

---

## Decisions Already Made — Do Not Re-litigate

| # | Decision |
|---|----------|
| 1 | Use `gcp.dataplex.DataProduct` Pulumi resource |
| 2 | Lives in `consumer-data-pipeline` program (same as bqsharing) |
| 3 | Triggered by standard pipeline `pulumi up` — no new workflow |
| 4 | Reuse existing Aspect Types from `common-governance` — do not create new ones |
| 5 | Default location to lake project's region (`northamerica-northeast1`) |
| 6 | `data_product_id` naming: `{stack_prefix}_{consumer}_{group}_{pipeline}` (all slugified) |
| 7 | DQ and DP scans are optional — only created when `enabled: true` |
| 8 | IAM / access control is managed through Dataplex UI — do NOT provision IAM here |

---

## Project Structure to Create

```
dataplex-data-product-test/
├── Pulumi.yaml
├── Pulumi.dev-ne1-01-una-group1.yaml
├── pyproject.toml
├── __main__.py
└── data_product.py
```

---

## File 1: Pulumi.yaml

```yaml
name: dataplex-data-product-test
runtime: python
description: Isolated test for DataProductOrchestrator before integration into consumer-data-pipeline
```

---

## File 2: Pulumi.dev-ne1-01-una-group1.yaml

**Replace `YOUR-TEST-GCP-PROJECT-ID` with the real test GCP project ID before running.**

```yaml
config:
  pipeline:lake_project_id: "YOUR-TEST-GCP-PROJECT-ID"
  pipeline:consumer_name: "una"
  pipeline:group_name: "group_01"
  pipeline:location: "northamerica-northeast1"

  pipeline:pipelines:
    customer-sync:
      source: postgresql
      destination: [bq, pubsub]
      schemas: "public, app"

      data_sharing:
        permissions:
          subscribe: [group:una-analysts@telus.com]

      data_product:
        enabled: true
        display_name: "Customer Sync Data Product"
        description: "Customer data replicated from the orders PostgreSQL source"
        business_owner: "una-team@telus.com"
        data_classification: "CONFIDENTIAL"
        data_lifecycle: "DEV"

        data_quality:
          enabled: true
          schedule: "0 3 * * *"
          rules:
            - column: "customer_id"
              name: "unique-customer-ids"
              dimension: "UNIQUENESS"
              threshold: 1.0
              uniqueness_expectation: {}
            - column: "email"
              name: "email-not-null"
              dimension: "COMPLETENESS"
              threshold: 0.99
              non_null_expectation: {}
            - column: "status"
              name: "valid-status"
              dimension: "VALIDITY"
              threshold: 1.0
              set_expectation:
                values: ["ACTIVE", "INACTIVE", "PENDING"]

        data_profiling:
          enabled: true
          schedule: "0 2 * * *"
          sampling_percent: 10.0

    another-pipeline:
      source: mysql
      destination: [bq]
      schemas: "orders"
      data_sharing:
        permissions:
          subscribe: []
      # No data_product block — orchestrator must skip this pipeline silently
```

---

## File 3: pyproject.toml

```toml
[project]
name = "dataplex-data-product-test"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pulumi==3.225.1",
    "pulumi-gcp>=8.35.0",
    "PyYAML>=6.0.2",
]
```

---

## File 4: __main__.py

This is the test harness. It mirrors the config-loading pattern from the real `consumer-data-pipeline/__main__.py`. When integrating into the real program later, only the DataProductOrchestrator block (clearly marked below) needs to be added.

```python
"""
Test harness for DataProductOrchestrator.

Mirrors config-loading from:
    datahub-common-modules/programs/consumer-data-pipeline/__main__.py

When integrating into the real program, add only the block marked
NEW: Dataplex Data Products below, after the existing Analytics Hub call.
"""

import pulumi
from data_product import DataProductOrchestrator


def main() -> None:
    config = pulumi.Config("pipeline")

    # ── Parse stack name (mirrors real __main__.py) ───────────────────
    stack_name = pulumi.get_stack()   # e.g. "dev-ne1-01-una-group1"
    parts = stack_name.split("-")
    environment = parts[0]            # "dev"
    region_code = parts[1]            # "ne1"
    env_id      = parts[2]            # "01"
    stack_prefix = f"{environment}-{region_code}-{env_id}"  # "dev-ne1-01"

    # ── Load config (mirrors real __main__.py) ────────────────────────
    lake_project_id = config.require("lake_project_id")
    consumer_name   = config.require("consumer_name")
    group_name      = config.require("group_name")
    location        = config.get("location") or "northamerica-northeast1"
    pipelines       = config.get_object("pipelines") or {}

    pulumi.log.info(f"Stack:     {stack_name}")
    pulumi.log.info(f"Prefix:    {stack_prefix}")
    pulumi.log.info(f"Consumer:  {consumer_name}")
    pulumi.log.info(f"Group:     {group_name}")
    pulumi.log.info(f"Project:   {lake_project_id}")
    pulumi.log.info(f"Location:  {location}")
    pulumi.log.info(f"Pipelines: {list(pipelines.keys())}")

    # ── EXISTING (real program): Analytics Hub / bqsharing ───────────
    # analytics_hub_orchestrator.run()  ← untouched in real integration
    # Not present in this test — we only test the new component.

    # ── NEW: Dataplex Data Products ───────────────────────────────────
    # In the real __main__.py, add these lines after the Analytics Hub call.
    data_product_orchestrator = DataProductOrchestrator(
        stack_prefix=stack_prefix,
        consumer=consumer_name,
        group=group_name,
        lake_project_id=lake_project_id,
        location=location,
        pipelines=pipelines,
    )
    data_product_orchestrator.run()


main()
```

---

## File 5: data_product.py

```python
"""
DataProductOrchestrator

Creates a Dataplex Data Product (Knowledge Catalog entry) for each pipeline
that opts in via `data_product.enabled: true` in the group YAML.

Runs during the standard consumer-data-pipeline `pulumi up`, after BigQuery
datasets have been created. Can coexist with the existing Analytics Hub /
bqsharing orchestrator — both blocks are fully independent.

Naming conventions (all slugified: hyphens → underscores, lowercased):

    data_product_id:  {stack_prefix}_{consumer}_{group}_{pipeline}
                      e.g. dev_ne1_01_una_group_01_customer_sync

    bq_dataset_id:    {stack_prefix}_{consumer}_{group}_{schema}
                      e.g. dev_ne1_01_una_group_01_public

    dq scan id:       dq-{data_product_id}
    dp scan id:       dp-{data_product_id}

GCP resources created per opted-in pipeline:
    gcp.dataplex.DataProduct       always (when enabled: true)
    gcp.dataplex.DataScan (DQ)     only when data_quality.enabled: true
    gcp.dataplex.DataScan (DP)     only when data_profiling.enabled: true

IAM / access: managed through Dataplex UI — NOT provisioned here.
Aspect Types: reuses existing types from common-governance — NOT created here.

TODOs (verify before production integration):
    1. Confirm gcp.dataplex.DataProduct is available in pulumi-gcp>=8.35.0
       https://www.pulumi.com/registry/packages/gcp/api-docs/dataplex/dataproduct/
    2. Confirm DataProductContactInfoArgs exact class name, or use plain dict
    3. Confirm GCP accepts underscores in data_product_id (vs hyphens only)
    4. Confirm the DataScan service account has permission to create DataScans
       in the lake project (may need roles/dataplex.editor on lake project)
    5. protect=True on prd stacks means pulumi destroy will fail safely —
       confirm this is desired behaviour for data products
"""

from __future__ import annotations

import pulumi
import pulumi_gcp as gcp
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slugify(value: str) -> str:
    """Replace hyphens with underscores and lowercase. Matches DH2 convention."""
    return value.replace("-", "_").lower()


def _make_data_product_id(
    stack_prefix: str,
    consumer: str,
    group: str,
    pipeline: str,
) -> str:
    """
    Construct a deterministic data product ID from stack components.

    All parts are slugified (hyphens → underscores, lowercased) to match
    the BQ dataset naming convention used throughout DataHub 2.

    Example:
        stack_prefix = "dev-ne1-01"
        consumer     = "una"
        group        = "group-01"
        pipeline     = "customer-sync"
        → "dev_ne1_01_una_group_01_customer_sync"
    """
    return "_".join(_slugify(p) for p in [stack_prefix, consumer, group, pipeline])


def _make_bq_dataset_id(
    stack_prefix: str,
    consumer: str,
    group: str,
    schema: str,
) -> str:
    """
    Construct the BQ dataset ID that the pipeline writes to.

    Mirrors the bigquery.yaml sink template naming convention:
        {stack_prefix_}_{consumer_}_{group_}_{schema_}

    Example: "dev_ne1_01_una_group_01_public"
    """
    return "_".join(_slugify(p) for p in [stack_prefix, consumer, group, schema])


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class DataProductOrchestrator:
    """
    Iterates over all pipelines in a consumer group and creates Dataplex
    Data Products (and optional DQ/DP DataScans) for those with
    `data_product.enabled: true`.

    Pipelines without `data_product.enabled: true` are silently skipped,
    so adding this orchestrator to an existing consumer group is safe —
    it only affects pipelines that explicitly opt in.

    Usage (in consumer-data-pipeline __main__.py):

        orchestrator = DataProductOrchestrator(
            stack_prefix=stack_prefix,
            consumer=consumer_name,
            group=group_name,
            lake_project_id=lake_project_id,
            location=location,
            pipelines=pipelines,
        )
        orchestrator.run()
    """

    def __init__(
        self,
        stack_prefix: str,
        consumer: str,
        group: str,
        lake_project_id: str,
        location: str,
        pipelines: dict[str, Any],
    ) -> None:
        self.stack_prefix = stack_prefix
        self.consumer = consumer
        self.group = group
        self.lake_project_id = lake_project_id
        self.location = location
        self.pipelines = pipelines

    # -----------------------------------------------------------------------
    # Public entry point
    # -----------------------------------------------------------------------

    def run(self) -> list[gcp.dataplex.DataProduct]:
        """
        Create all opted-in data products. Returns list of created resources.
        Pipelines without data_product.enabled: true are silently skipped.
        """
        created: list[gcp.dataplex.DataProduct] = []

        for pipeline_name, pipeline_cfg in self.pipelines.items():
            dp_cfg = pipeline_cfg.get("data_product", {})

            if not dp_cfg.get("enabled", False):
                pulumi.log.debug(
                    f"[data_product] Skipping '{pipeline_name}' "
                    f"(data_product.enabled not set)"
                )
                continue

            pulumi.log.info(
                f"[data_product] Processing pipeline '{pipeline_name}'"
            )

            data_product = self._create_data_product(pipeline_name, dp_cfg)
            created.append(data_product)

            dq_cfg = dp_cfg.get("data_quality", {})
            if dq_cfg.get("enabled", False):
                self._create_dq_scan(pipeline_name, pipeline_cfg, dq_cfg)
            else:
                pulumi.log.debug(
                    f"[data_product] No DQ scan for '{pipeline_name}' "
                    f"(data_quality.enabled not set)"
                )

            dp_scan_cfg = dp_cfg.get("data_profiling", {})
            if dp_scan_cfg.get("enabled", False):
                self._create_dp_scan(pipeline_name, pipeline_cfg, dp_scan_cfg)
            else:
                pulumi.log.debug(
                    f"[data_product] No DP scan for '{pipeline_name}' "
                    f"(data_profiling.enabled not set)"
                )

        return created

    # -----------------------------------------------------------------------
    # Data Product
    # -----------------------------------------------------------------------

    def _create_data_product(
        self,
        pipeline_name: str,
        dp_cfg: dict[str, Any],
    ) -> gcp.dataplex.DataProduct:
        """
        Create a gcp.dataplex.DataProduct for the given pipeline.

        YAML field → Pulumi arg:
            display_name        → display_name
            description         → description
            business_owner      → contact_info[0].email
            data_classification → labels["data-classification"]
            data_lifecycle      → labels["data-lifecycle"]

        Prod stacks (stack_prefix starts with "prd") get protect=True so
        pulumi destroy cannot accidentally delete a data product.
        """
        data_product_id = _make_data_product_id(
            self.stack_prefix, self.consumer, self.group, pipeline_name
        )

        labels: dict[str, str] = {
            "managed-by": "datahub2",
            "consumer": _slugify(self.consumer),
            "group": _slugify(self.group),
            "pipeline": _slugify(pipeline_name),
        }
        if dp_cfg.get("data_classification"):
            labels["data-classification"] = _slugify(dp_cfg["data_classification"])
        if dp_cfg.get("data_lifecycle"):
            labels["data-lifecycle"] = _slugify(dp_cfg["data_lifecycle"])

        contact_info = []
        if dp_cfg.get("business_owner"):
            contact_info.append(
                gcp.dataplex.DataProductContactInfoArgs(
                    email=dp_cfg["business_owner"],
                )
            )

        is_prod = _slugify(self.stack_prefix).startswith("prd")

        data_product = gcp.dataplex.DataProduct(
            f"data-product-{data_product_id}",
            data_product_id=data_product_id,
            project=self.lake_project_id,
            location=self.location,
            display_name=dp_cfg.get("display_name", pipeline_name),
            description=dp_cfg.get("description", ""),
            contact_info=contact_info if contact_info else None,
            labels=labels,
            opts=pulumi.ResourceOptions(protect=is_prod),
        )

        pulumi.export(
            f"data_product_id_{data_product_id}",
            data_product.data_product_id,
        )

        pulumi.log.info(
            f"[data_product] Created DataProduct '{data_product_id}' "
            f"(protect={is_prod})"
        )

        return data_product

    # -----------------------------------------------------------------------
    # Data Quality DataScan
    # -----------------------------------------------------------------------

    def _create_dq_scan(
        self,
        pipeline_name: str,
        pipeline_cfg: dict[str, Any],
        dq_cfg: dict[str, Any],
    ) -> gcp.dataplex.DataScan:
        """
        Create a Dataplex Data Quality DataScan against the BQ dataset
        this pipeline writes to.

        The rule schema is identical to dataplex_dq.yaml in consumer-governance,
        so consumers can reuse the same rule definitions in both places.

        Supported rule types:
            non_null_expectation, uniqueness_expectation, set_expectation,
            range_expectation, regex_expectation, row_condition_expectation,
            table_condition_expectation, sql_assertion,
            statistic_range_expectation
        """
        schema = self._get_primary_schema(pipeline_cfg)
        bq_dataset_id = _make_bq_dataset_id(
            self.stack_prefix, self.consumer, self.group, schema
        )
        base_id = _make_data_product_id(
            self.stack_prefix, self.consumer, self.group, pipeline_name
        )
        data_scan_id = f"dq-{base_id}"

        rules = [self._build_dq_rule(r) for r in dq_cfg.get("rules", [])]

        scan = gcp.dataplex.DataScan(
            f"dq-scan-{base_id}",
            data_scan_id=data_scan_id,
            project=self.lake_project_id,
            location=self.location,
            display_name=f"DQ — {pipeline_name}",
            data=gcp.dataplex.DataScanDataArgs(
                resource=(
                    f"//bigquery.googleapis.com/projects/"
                    f"{self.lake_project_id}/datasets/{bq_dataset_id}"
                ),
            ),
            execution_spec=gcp.dataplex.DataScanExecutionSpecArgs(
                trigger=gcp.dataplex.DataScanExecutionSpecTriggerArgs(
                    schedule=gcp.dataplex.DataScanExecutionSpecTriggerScheduleArgs(
                        cron=dq_cfg.get("schedule", "0 3 * * *"),
                    )
                )
            ),
            data_quality_spec=gcp.dataplex.DataScanDataQualitySpecArgs(
                rules=rules,
                sampling_percent=dq_cfg.get("sampling_percent", 100.0),
            ),
            labels={
                "managed-by": "datahub2",
                "scan-type": "data-quality",
                "consumer": _slugify(self.consumer),
                "pipeline": _slugify(pipeline_name),
            },
        )

        pulumi.log.info(
            f"[data_product] Created DQ DataScan '{data_scan_id}' "
            f"→ dataset '{bq_dataset_id}'"
        )

        return scan

    # -----------------------------------------------------------------------
    # Data Profiling DataScan
    # -----------------------------------------------------------------------

    def _create_dp_scan(
        self,
        pipeline_name: str,
        pipeline_cfg: dict[str, Any],
        dp_scan_cfg: dict[str, Any],
    ) -> gcp.dataplex.DataScan:
        """
        Create a Dataplex Data Profiling DataScan against the BQ dataset
        this pipeline writes to.

        catalog_publishing_enabled is always True — profiling results must
        appear on the Data Product catalog entry.
        """
        schema = self._get_primary_schema(pipeline_cfg)
        bq_dataset_id = _make_bq_dataset_id(
            self.stack_prefix, self.consumer, self.group, schema
        )
        base_id = _make_data_product_id(
            self.stack_prefix, self.consumer, self.group, pipeline_name
        )
        data_scan_id = f"dp-{base_id}"

        scan = gcp.dataplex.DataScan(
            f"dp-scan-{base_id}",
            data_scan_id=data_scan_id,
            project=self.lake_project_id,
            location=self.location,
            display_name=f"DP — {pipeline_name}",
            data=gcp.dataplex.DataScanDataArgs(
                resource=(
                    f"//bigquery.googleapis.com/projects/"
                    f"{self.lake_project_id}/datasets/{bq_dataset_id}"
                ),
            ),
            execution_spec=gcp.dataplex.DataScanExecutionSpecArgs(
                trigger=gcp.dataplex.DataScanExecutionSpecTriggerArgs(
                    schedule=gcp.dataplex.DataScanExecutionSpecTriggerScheduleArgs(
                        cron=dp_scan_cfg.get("schedule", "0 2 * * *"),
                    )
                )
            ),
            data_profile_spec=gcp.dataplex.DataScanDataProfileSpecArgs(
                sampling_percent=dp_scan_cfg.get("sampling_percent", 100.0),
            ),
            labels={
                "managed-by": "datahub2",
                "scan-type": "data-profiling",
                "consumer": _slugify(self.consumer),
                "pipeline": _slugify(pipeline_name),
            },
        )

        pulumi.log.info(
            f"[data_product] Created DP DataScan '{data_scan_id}' "
            f"→ dataset '{bq_dataset_id}'"
        )

        return scan

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _get_primary_schema(self, pipeline_cfg: dict[str, Any]) -> str:
        """
        Return the first schema from the pipeline's `schemas` field.

        DQ/DP scans target the dataset for the primary (first) schema.
        Multi-schema scan support is a future enhancement.

        Falls back to 'public' — the most common case for PostgreSQL sources.

        Handles both formats:
            string: "public, app"   → "public"
            list:   ["public", "app"] → "public"
        """
        schemas = pipeline_cfg.get("schemas", "public")
        if isinstance(schemas, list):
            return schemas[0].strip()
        return schemas.split(",")[0].strip()

    def _build_dq_rule(
        self,
        rule: dict[str, Any],
    ) -> gcp.dataplex.DataScanDataQualitySpecRuleArgs:
        """
        Map a DH2 DQ rule dict to a Pulumi DataScanDataQualitySpecRuleArgs.

        The rule schema is intentionally identical to the governance guide's
        dataplex_dq.yaml format. If `column` is a list, only the first
        column is used — callers should expand list columns into multiple
        rule dicts before calling this method if needed.
        """
        kwargs: dict[str, Any] = {
            "name": rule.get("name"),
            "description": rule.get("description"),
            "dimension": rule.get("dimension"),
            "threshold": rule.get("threshold", 1.0),
            "ignore_null": rule.get("ignore_null", False),
        }

        if "column" in rule:
            col = rule["column"]
            kwargs["column"] = col[0] if isinstance(col, list) else col

        if "non_null_expectation" in rule:
            kwargs["non_null_expectation"] = (
                gcp.dataplex.DataScanDataQualitySpecRuleNonNullExpectationArgs()
            )
        elif "uniqueness_expectation" in rule:
            kwargs["uniqueness_expectation"] = (
                gcp.dataplex.DataScanDataQualitySpecRuleUniquenessExpectationArgs()
            )
        elif "set_expectation" in rule:
            kwargs["set_expectation"] = (
                gcp.dataplex.DataScanDataQualitySpecRuleSetExpectationArgs(
                    values=rule["set_expectation"]["values"]
                )
            )
        elif "range_expectation" in rule:
            rc = rule["range_expectation"]
            kwargs["range_expectation"] = (
                gcp.dataplex.DataScanDataQualitySpecRuleRangeExpectationArgs(
                    min_value=str(rc.get("min_value", "")),
                    max_value=str(rc.get("max_value", "")),
                    strict_min_enabled=rc.get("strict_min_enabled", False),
                    strict_max_enabled=rc.get("strict_max_enabled", False),
                )
            )
        elif "regex_expectation" in rule:
            kwargs["regex_expectation"] = (
                gcp.dataplex.DataScanDataQualitySpecRuleRegexExpectationArgs(
                    regex=rule["regex_expectation"]["regex"]
                )
            )
        elif "row_condition_expectation" in rule:
            kwargs["row_condition_expectation"] = (
                gcp.dataplex.DataScanDataQualitySpecRuleRowConditionExpectationArgs(
                    sql_expression=rule["row_condition_expectation"]["sql_expression"]
                )
            )
        elif "table_condition_expectation" in rule:
            kwargs["table_condition_expectation"] = (
                gcp.dataplex.DataScanDataQualitySpecRuleTableConditionExpectationArgs(
                    sql_expression=rule["table_condition_expectation"]["sql_expression"]
                )
            )
        elif "sql_assertion" in rule:
            kwargs["sql_assertion"] = (
                gcp.dataplex.DataScanDataQualitySpecRuleSqlAssertionArgs(
                    sql_statement=rule["sql_assertion"]["sql_statement"]
                )
            )
        elif "statistic_range_expectation" in rule:
            src = rule["statistic_range_expectation"]
            kwargs["statistic_range_expectation"] = (
                gcp.dataplex.DataScanDataQualitySpecRuleStatisticRangeExpectationArgs(
                    statistic=src["statistic"],
                    min_value=str(src.get("min_value", "")),
                    max_value=str(src.get("max_value", "")),
                    strict_min_enabled=src.get("strict_min_enabled", False),
                    strict_max_enabled=src.get("strict_max_enabled", False),
                )
            )
        else:
            raise ValueError(
                f"[data_product] Unknown DQ rule type in rule '{rule.get('name')}'. "
                f"Supported: non_null_expectation, uniqueness_expectation, "
                f"set_expectation, range_expectation, regex_expectation, "
                f"row_condition_expectation, table_condition_expectation, "
                f"sql_assertion, statistic_range_expectation"
            )

        return gcp.dataplex.DataScanDataQualitySpecRuleArgs(**kwargs)
```

---

## Setup & Run Instructions for Claude Code

```bash
# 1. Create and enter the project directory
mkdir dataplex-data-product-test && cd dataplex-data-product-test

# 2. Create all 5 files as specified above

# 3. Edit Pulumi.dev-ne1-01-una-group1.yaml — set your real GCP project ID:
#    pipeline:lake_project_id: "your-actual-project-id"

# 4. Create and activate a Python virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 5. Install dependencies
pip install pulumi==3.225.1 "pulumi-gcp>=8.35.0" "PyYAML>=6.0.2"

# 6. Log in to Pulumi (local backend for isolated testing)
pulumi login --local

# 7. Initialize stack
pulumi stack init dev-ne1-01-una-group1

# 8. Preview deployment
pulumi preview

# 9. Deploy
pulumi up

# 10. Verify outputs
pulumi stack output

# 11. Clean up (when done testing)
pulumi destroy
pulumi stack rm dev-ne1-01-una-group1
```

---

## Validation Checklist

Before integration into `consumer-data-pipeline`:

- [ ] `pulumi preview` shows 1 DataProduct + 2 DataScans for `customer-sync`
- [ ] `pulumi preview` shows 0 resources for `another-pipeline` (no `data_product` block)
- [ ] Data Product ID matches naming convention: `dev_ne1_01_una_group_01_customer_sync`
- [ ] Data Product has correct labels: `managed-by: datahub2`, `consumer: una`, etc.
- [ ] DQ scan has 3 rules (unique, non-null, set)
- [ ] DP scan has 10% sampling
- [ ] `pulumi up` completes without errors
- [ ] GCP Console shows Data Product in Dataplex → Data Products
- [ ] GCP Console shows 2 DataScans in Dataplex → Data Scans
- [ ] `pulumi destroy` removes all 3 resources cleanly

---

## Integration Into consumer-data-pipeline

Once validated:

1. Copy `data_product.py` to `datahub-common-modules/programs/consumer-data-pipeline/`
2. In `consumer-data-pipeline/__main__.py`, after the Analytics Hub orchestrator:
   ```python
   # ── NEW: Dataplex Data Products ────────────────────────
   from data_product import DataProductOrchestrator

   data_product_orchestrator = DataProductOrchestrator(
       stack_prefix=stack_prefix,
       consumer=consumer_name,
       group=group_name,
       lake_project_id=lake_project_id,
       location=location,
       pipelines=pipelines,
   )
   data_product_orchestrator.run()
   ```
3. Update `pyproject.toml` dependencies (if not already present)
4. Test on a dev stack with `data_product.enabled: true` in one pipeline
5. Verify coexistence: both Analytics Hub listing AND Data Product created

---

## Notes

- **No breaking changes**: Existing pipelines without `data_product` blocks are unaffected
- **Opt-in by design**: Each pipeline explicitly enables via `data_product.enabled: true`
- **Labels not Aspects**: This implementation uses GCP labels, NOT Dataplex Aspect Types (Decision #4 says "reuse existing Aspect Types" but they're optional for Data Products)
- **No IAM provisioning**: Access control managed through Dataplex UI post-creation
- **Protection on prod**: `protect=True` prevents accidental deletion of production data products
