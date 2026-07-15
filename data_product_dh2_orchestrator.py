"""
DataHub 2 Data Product Orchestrator

Batch-creates Dataplex Data Products for consumer pipelines by reading from
Pulumi Config and using the DataProductWithAspects component.

This orchestrator enables the DataHub 2 workflow:
- Reads pipeline configurations from Pulumi.Config("pipeline")
- Iterates over all pipelines in a consumer group
- For each pipeline with data_product.enabled: true, creates:
  * A Dataplex Data Product (using DataProductWithAspects component)
  * Optional Data Quality DataScan (if data_quality.enabled)
  * Optional Data Profiling DataScan (if data_profiling.enabled)

Usage (in consumer-data-pipeline __main__.py):
    from data_product_dh2_orchestrator import DataProductDH2Orchestrator

    orchestrator = DataProductDH2Orchestrator(
        stack_prefix=stack_prefix,
        consumer=consumer_name,
        group=group_name,
        lake_project_id=lake_project_id,
        location=location,
        pipelines=pipelines,
    )
    orchestrator.run()

Configuration (in Pulumi.{stack}.yaml):
    config:
      pipeline:pipelines:
        customer-sync:
          source: postgresql
          schemas: "public, app"
          data_product:
            enabled: true
            display_name: "Customer Sync Data Product"
            description: "Customer data from PostgreSQL"
            business_owner: "team@company.com"
            data_classification: "confidential"
            data_quality:
              enabled: true
              schedule: "0 3 * * *"
              rules: [...]
            data_profiling:
              enabled: true
              schedule: "0 2 * * *"
              sampling_percent: 10.0
"""

from __future__ import annotations

import pulumi
import pulumi_gcp as gcp
from typing import Any

# Import the component and defaults
from dataproduct import DataProductWithAspects, DataProductArgs
import defaults


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

    Example: "dev_ne1_01_una_group_01_public"
    """
    return "_".join(_slugify(p) for p in [stack_prefix, consumer, group, schema])


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class DataProductDH2Orchestrator:
    """
    DataHub 2 orchestrator for batch-creating Dataplex Data Products.

    Reads pipeline configurations and uses the DataProductWithAspects component
    to create data products with standardized governance aspects.

    This orchestrator:
    - Enables gradual migration (opt-in per pipeline via data_product.enabled)
    - Coexists with Analytics Hub (bqsharing) - both can be present
    - Uses existing config structure (pipeline:pipelines)
    - Follows DH2 naming conventions
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
        """
        Initialize the orchestrator.

        Args:
            stack_prefix: Stack prefix like "dev-ne1-01"
            consumer: Consumer name like "una"
            group: Group name like "group-01"
            lake_project_id: GCP project ID for Dataplex resources
            location: GCP region (default: northamerica-northeast1)
            pipelines: Dict of pipeline configs from Pulumi.Config("pipeline")
        """
        self.stack_prefix = stack_prefix
        self.consumer = consumer
        self.group = group
        self.lake_project_id = lake_project_id
        self.location = location
        self.pipelines = pipelines

    # -----------------------------------------------------------------------
    # Public entry point
    # -----------------------------------------------------------------------

    def run(self) -> list[DataProductWithAspects]:
        """
        Create data products for all opted-in pipelines.

        Returns:
            List of created DataProductWithAspects components
        """
        created: list[DataProductWithAspects] = []

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

            # Create data product using the component
            data_product = self._create_data_product(pipeline_name, dp_cfg)
            created.append(data_product)

            # Create optional Data Quality scan
            dq_cfg = dp_cfg.get("data_quality", {})
            if dq_cfg.get("enabled", False):
                self._create_dq_scan(pipeline_name, pipeline_cfg, dq_cfg)
            else:
                pulumi.log.debug(
                    f"[data_product] No DQ scan for '{pipeline_name}' "
                    f"(data_quality.enabled not set)"
                )

            # Create optional Data Profiling scan
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
    # Data Product (uses component!)
    # -----------------------------------------------------------------------

    def _create_data_product(
        self,
        pipeline_name: str,
        dp_cfg: dict[str, Any],
    ) -> DataProductWithAspects:
        """
        Create a DataProductWithAspects component for the pipeline.

        Maps snake_case config to camelCase component args.
        """
        data_product_id = _make_data_product_id(
            self.stack_prefix, self.consumer, self.group, pipeline_name
        )

        # Map config to component args (snake_case → camelCase)
        args: DataProductArgs = {
            # Core properties (required by component)
            "dataProductId": data_product_id,
            "project": self.lake_project_id,
            "location": self.location,
            "displayName": dp_cfg.get("display_name", pipeline_name),
            "description": dp_cfg.get("description", f"Data product for {pipeline_name} pipeline"),

            # Access groups - simplified for DH2 (can be enhanced later)
            "accessGroups": {},

            # Business context (required)
            "businessDomain": dp_cfg.get("business_domain", defaults.DH2_DEFAULT_BUSINESS_DOMAIN),
            "businessOwner": dp_cfg.get("business_owner", defaults.DH2_DEFAULT_BUSINESS_OWNER),
            "businessPurpose": dp_cfg.get("business_purpose", f"Pipeline: {pipeline_name}"),

            # Compliance (required)
            "dataClassification": dp_cfg.get("data_classification", defaults.DH2_DEFAULT_DATA_CLASSIFICATION),
            "retentionJustification": dp_cfg.get(
                "retention_justification",
                f"Standard retention for {dp_cfg.get('data_classification', defaults.DH2_DEFAULT_DATA_CLASSIFICATION)} data"
            ),

            # Technical (required)
            "technicalOwner": dp_cfg.get("technical_owner", defaults.DH2_DEFAULT_TECHNICAL_OWNER),
            "technicalContact": dp_cfg.get("technical_contact", defaults.DH2_DEFAULT_TECHNICAL_CONTACT),
        }

        # Optional fields (only add if present in config)
        if "glossary_terms" in dp_cfg:
            args["glossaryTerms"] = dp_cfg["glossary_terms"]

        if "compliance_frameworks" in dp_cfg:
            args["complianceFrameworks"] = dp_cfg["compliance_frameworks"]

        if "contains_pii" in dp_cfg:
            args["containsPii"] = dp_cfg["contains_pii"]

        if "retention_years" in dp_cfg:
            args["retentionYears"] = dp_cfg["retention_years"]

        if "sla_tier" in dp_cfg:
            args["slaTier"] = dp_cfg["sla_tier"]

        if "availability_target" in dp_cfg:
            args["availabilityTarget"] = dp_cfg["availability_target"]

        if "support_hours" in dp_cfg:
            args["supportHours"] = dp_cfg["support_hours"]

        if "version" in dp_cfg:
            args["version"] = dp_cfg["version"]

        if "changelog" in dp_cfg:
            args["changelog"] = dp_cfg["changelog"]

        # Add DH2-specific tags
        args["tags"] = {
            "managed-by": "datahub2",
            "consumer": _slugify(self.consumer),
            "group": _slugify(self.group),
            "pipeline": _slugify(pipeline_name),
        }

        if dp_cfg.get("data_lifecycle"):
            args["tags"]["data-lifecycle"] = _slugify(dp_cfg["data_lifecycle"])

        # Create using the component!
        pulumi.log.info(
            f"[data_product] Creating DataProduct '{data_product_id}' "
            f"using DataProductWithAspects component"
        )

        return DataProductWithAspects(
            f"data-product-{data_product_id}",
            args=args,
        )

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
        Create a Dataplex Data Quality DataScan.

        Note: This creates the DataScan directly (not through component)
        as it's optional and specific to DH2 workflows.
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

        scan = gcp.dataplex.Datascan(
            f"dq-scan-{base_id}",
            data_scan_id=data_scan_id,
            project=self.lake_project_id,
            location=self.location,
            display_name=f"DQ — {pipeline_name}",
            data=gcp.dataplex.DatascanDataArgs(
                resource=(
                    f"//bigquery.googleapis.com/projects/"
                    f"{self.lake_project_id}/datasets/{bq_dataset_id}"
                ),
            ),
            execution_spec=gcp.dataplex.DatascanExecutionSpecArgs(
                trigger=gcp.dataplex.DatascanExecutionSpecTriggerArgs(
                    schedule=gcp.dataplex.DatascanExecutionSpecTriggerScheduleArgs(
                        cron=dq_cfg.get("schedule", defaults.DH2_DEFAULT_DQ_SCHEDULE),
                    )
                )
            ),
            data_quality_spec=gcp.dataplex.DatascanDataQualitySpecArgs(
                rules=rules,
                sampling_percent=dq_cfg.get("sampling_percent", defaults.DH2_DEFAULT_SAMPLING_PERCENT),
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
        Create a Dataplex Data Profiling DataScan.
        """
        schema = self._get_primary_schema(pipeline_cfg)
        bq_dataset_id = _make_bq_dataset_id(
            self.stack_prefix, self.consumer, self.group, schema
        )
        base_id = _make_data_product_id(
            self.stack_prefix, self.consumer, self.group, pipeline_name
        )
        data_scan_id = f"dp-{base_id}"

        scan = gcp.dataplex.Datascan(
            f"dp-scan-{base_id}",
            data_scan_id=data_scan_id,
            project=self.lake_project_id,
            location=self.location,
            display_name=f"DP — {pipeline_name}",
            data=gcp.dataplex.DatascanDataArgs(
                resource=(
                    f"//bigquery.googleapis.com/projects/"
                    f"{self.lake_project_id}/datasets/{bq_dataset_id}"
                ),
            ),
            execution_spec=gcp.dataplex.DatascanExecutionSpecArgs(
                trigger=gcp.dataplex.DatascanExecutionSpecTriggerArgs(
                    schedule=gcp.dataplex.DatascanExecutionSpecTriggerScheduleArgs(
                        cron=dp_scan_cfg.get("schedule", defaults.DH2_DEFAULT_DP_SCHEDULE),
                    )
                )
            ),
            data_profile_spec=gcp.dataplex.DatascanDataProfileSpecArgs(
                sampling_percent=dp_scan_cfg.get("sampling_percent", defaults.DH2_DEFAULT_SAMPLING_PERCENT),
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
        Return the first schema from the pipeline's schemas field.

        Handles both string and list formats:
            "public, app" → "public"
            ["public", "app"] → "public"
        """
        schemas = pipeline_cfg.get("schemas", defaults.DH2_DEFAULT_PRIMARY_SCHEMA)
        if isinstance(schemas, list):
            return schemas[0].strip()
        return schemas.split(",")[0].strip()

    def _build_dq_rule(
        self,
        rule: dict[str, Any],
    ) -> gcp.dataplex.DatascanDataQualitySpecRuleArgs:
        """
        Map a DH2 DQ rule dict to Pulumi DataScanDataQualitySpecRuleArgs.

        Supports all 9 rule types from the DH2 governance guide.
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
            kwargs["non_null_expectation"] = {}
        elif "uniqueness_expectation" in rule:
            kwargs["uniqueness_expectation"] = {}
        elif "set_expectation" in rule:
            kwargs["set_expectation"] = {
                "values": rule["set_expectation"]["values"]
            }
        elif "range_expectation" in rule:
            rc = rule["range_expectation"]
            kwargs["range_expectation"] = {
                "min_value": str(rc.get("min_value", "")),
                "max_value": str(rc.get("max_value", "")),
                "strict_min_enabled": rc.get("strict_min_enabled", False),
                "strict_max_enabled": rc.get("strict_max_enabled", False),
            }
        elif "regex_expectation" in rule:
            kwargs["regex_expectation"] = {
                "regex": rule["regex_expectation"]["regex"]
            }
        elif "row_condition_expectation" in rule:
            kwargs["row_condition_expectation"] = {
                "sql_expression": rule["row_condition_expectation"]["sql_expression"]
            }
        elif "table_condition_expectation" in rule:
            kwargs["table_condition_expectation"] = {
                "sql_expression": rule["table_condition_expectation"]["sql_expression"]
            }
        elif "sql_assertion" in rule:
            kwargs["sql_assertion"] = {
                "sql_statement": rule["sql_assertion"]["sql_statement"]
            }
        elif "statistic_range_expectation" in rule:
            src = rule["statistic_range_expectation"]
            kwargs["statistic_range_expectation"] = {
                "statistic": src["statistic"],
                "min_value": str(src.get("min_value", "")),
                "max_value": str(src.get("max_value", "")),
                "strict_min_enabled": src.get("strict_min_enabled", False),
                "strict_max_enabled": src.get("strict_max_enabled", False),
            }
        else:
            raise ValueError(
                f"[data_product] Unknown DQ rule type in rule '{rule.get('name')}'. "
                f"Supported: non_null_expectation, uniqueness_expectation, "
                f"set_expectation, range_expectation, regex_expectation, "
                f"row_condition_expectation, table_condition_expectation, "
                f"sql_assertion, statistic_range_expectation"
            )

        return gcp.dataplex.DatascanDataQualitySpecRuleArgs(**kwargs)
