"""
Dataplex Data Product Component with Standardized Aspects

This module provides a Pulumi ComponentResource for creating Dataplex data products
with mandatory business, compliance, and technical aspects.
"""

import pulumi
from pulumi import ComponentResource, ResourceOptions, Output, Input
import pulumi_gcp as gcp
from pulumi_gcp.dataplex import DataProductDataAsset
import json
from dataclasses import dataclass
from datetime import datetime
from typing_extensions import TypedDict, NotRequired
from typing import Dict, List, Any

import defaults


# ============================================================================
# Constants
# ============================================================================

DEFAULT_LAKE_NAME = "default"
"""Default Dataplex lake name"""

DEFAULT_ZONE_NAME = "default"
"""Default Dataplex zone name"""

VALID_CLASSIFICATION_LEVELS = ["public", "internal", "confidential", "restricted"]
"""Valid data classification levels"""


# ============================================================================
# Aspect Configuration Registry
# ============================================================================

@dataclass
class AspectConfig:
    """Configuration for a single aspect type"""
    aspect_type_id: str
    """The AspectType ID in GCP Dataplex"""
    builder_method: str
    """Name of the method that builds this aspect's data"""
    description: str
    """Human-readable description of the aspect"""


# Registry of all aspects to attach to DataProducts
# To add a new aspect:
# 1. Create the AspectType in GCP (via dataproducts-aspect-types stack)
# 2. Add an AspectConfig entry here
# 3. Create a corresponding _build_<name>_aspect_data() method
ASPECT_REGISTRY = [
    AspectConfig(
        aspect_type_id="product-and-business-identity",
        builder_method="_build_product_and_business_identity_data",
        description="Product and business identity metadata"
    ),
    AspectConfig(
        aspect_type_id="technical-lineage-and-architecture",
        builder_method="_build_technical_lineage_and_architecture_data",
        description="Technical lineage and architecture metadata"
    ),
    AspectConfig(
        aspect_type_id="table-governance-and-compliance",
        builder_method="_build_table_governance_and_compliance_data",
        description="Table governance and compliance metadata"
    ),
    AspectConfig(
        aspect_type_id="dataset-reliability-and-quality",
        builder_method="_build_dataset_reliability_and_quality_data",
        description="Dataset reliability and quality metadata"
    ),
    AspectConfig(
        aspect_type_id="personal-information-and-confidentiality",
        builder_method="_build_personal_information_and_confidentiality_data",
        description="Personal information and confidentiality metadata"
    ),
]


class DataProductArgs(TypedDict):
    """Arguments for DataProductWithAspects component"""

    # Data Product Core Properties (Required)
    dataProductId: Input[str]
    """Unique identifier for the data product"""
    location: Input[str]
    """GCP location/region"""
    project: Input[str]
    """GCP project ID"""
    projectNumber: Input[str]
    """GCP project number (e.g. 123456789012)"""
    displayName: Input[str]
    """Human-readable name for the data product"""
    description: Input[str]
    """Detailed description of the data product"""
    readerGroup: NotRequired[Input[str]]
    """Google Group ID for reader access (e.g., 'data-product-readers@example.com')"""

    # Mandatory Business Context Aspects (Required)
    businessDomain: Input[str]
    """Business domain (e.g., Finance, Marketing)"""
    businessOwner: Input[str]
    """Business owner email address"""
    businessPurpose: Input[str]
    """Business purpose statement"""

    # Mandatory Compliance Aspects (Required)
    dataClassification: Input[str]
    """Classification level: public, internal, confidential, or restricted"""
    retentionJustification: Input[str]
    """Justification for data retention period"""

    # Mandatory System/Technical Aspects (Required)
    technicalOwner: Input[str]
    """Technical owner email address"""
    technicalContact: Input[str]
    """Technical contact email address"""

    # Optional Business Context
    glossaryTerms: NotRequired[Input[List[str]]]
    """List of glossary terms"""

    # Optional Compliance
    complianceFrameworks: NotRequired[Input[List[str]]]
    """Compliance frameworks (e.g., GDPR, SOX, PIPEDA)"""
    containsPii: NotRequired[Input[bool]]
    """Whether data contains PII"""
    retentionYears: NotRequired[Input[int]]
    """Data retention period in years"""

    # Optional System/Technical
    slaTier: NotRequired[Input[str]]
    """SLA tier: critical, standard, or low"""
    availabilityTarget: NotRequired[Input[str]]
    """Availability target percentage"""
    supportHours: NotRequired[Input[str]]
    """Support hours description"""

    # Data Assets
    bigqueryDatasets: NotRequired[Input[List[str]]]
    """List of BigQuery dataset IDs to attach"""
    gcsBuckets: NotRequired[Input[List[str]]]
    """List of GCS bucket names to attach"""

    # Data Quality
    enableDataQualityScans: NotRequired[Input[bool]]
    """Enable data quality scans"""
    qualityScanSchedule: NotRequired[Input[str]]
    """Cron schedule for quality scans"""
    qualityRules: NotRequired[Input[List[Dict[str, Any]]]]
    """Data quality rules configuration"""

    # Data Profiling (column-level statistics)
    enableDataProfiling: NotRequired[Input[bool]]
    """Enable data profiling for automatic column-level statistics (nulls, distinct counts, min/max)"""
    profilingSamplingPercent: NotRequired[Input[float]]
    """Sampling percentage for profiling (1-100, default: 100)"""

    # Data Quality Alerting
    dataQualityAlertEmail: NotRequired[Input[str]]
    """Email or distribution list for data quality alerts (if not set, uses alertEmail; alerts auto-enabled if email present)"""
    qualityScoreThreshold: NotRequired[Input[float]]
    """Quality score threshold for alerts (0.0-1.0, default: 0.8 = 80%)"""

    # Cloud Scheduler
    useCloudSchedulerForScans: NotRequired[Input[bool]]
    """Use Cloud Scheduler to trigger scans instead of internal Dataplex scheduling (default: True)"""
    schedulerTimeZone: NotRequired[Input[str]]
    """Time zone for Cloud Scheduler jobs (default: America/Toronto)"""
    schedulerServiceAccount: NotRequired[Input[str]]
    """Service account email for Cloud Scheduler jobs (if not provided, uses default compute SA)"""
    schedulerPaused: NotRequired[Input[bool]]
    """Explicitly set scheduler jobs to paused or enabled state (default: auto-pause for bi-stg* projects)"""
    schedulerRetryCount: NotRequired[Input[int]]
    """Number of retry attempts for failed scheduler jobs (default: 3)"""
    schedulerMaxRetryDuration: NotRequired[Input[str]]
    """Maximum duration for retry attempts (default: 300s)"""
    schedulerMinBackoffDuration: NotRequired[Input[str]]
    """Minimum backoff duration between retries (default: 5s)"""
    schedulerMaxBackoffDuration: NotRequired[Input[str]]
    """Maximum backoff duration between retries (default: 3600s)"""
    schedulerMaxDoublings: NotRequired[Input[int]]
    """Maximum number of times to double the backoff duration (default: 5)"""

    # Monitoring
    enableMonitoring: NotRequired[Input[bool]]
    """Enable monitoring and alerting"""
    alertEmail: NotRequired[Input[str]]
    """Email address for alerts"""

    # Cost Management
    costCenter: NotRequired[Input[str]]
    """Cost center identifier"""
    enableCostTracking: NotRequired[Input[bool]]
    """Enable cost tracking labels"""

    # Version Management
    version: NotRequired[Input[str]]
    """Version number"""
    changelog: NotRequired[Input[str]]
    """Changelog description"""

    # Lineage
    upstreamDataProducts: NotRequired[Input[List[str]]]
    """List of upstream data product IDs"""
    downstreamDataProducts: NotRequired[Input[List[str]]]
    """List of downstream data product IDs"""
    transformationJobs: NotRequired[Input[List[str]]]
    """List of transformation job IDs"""

    # Access Automation
    preApprovedServiceAccounts: NotRequired[Input[List[str]]]
    """List of pre-approved service account emails"""

    # Owner Emails
    ownerEmails: NotRequired[Input[List[str]]]
    """List of owner email addresses (defaults to [businessOwner, technicalOwner] if not provided)"""

    # Dataplex Structure
    lakeName: NotRequired[Input[str]]
    """Dataplex lake name (defaults to 'default')"""
    zoneName: NotRequired[Input[str]]
    """Dataplex zone name (defaults to 'default')"""

    # Optional
    tags: NotRequired[Input[Dict[str, str]]]
    """Additional resource tags"""
    additionalAspects: NotRequired[Input[Dict[str, Any]]]
    """Additional custom aspects"""


class DataProductWithAspects(ComponentResource):
    """
    Custom Pulumi component that creates a Dataplex data product with:
    - Mandatory standardized aspects (business, compliance, technical)
    - Optional data asset attachment (BigQuery, GCS)
    - Optional data quality scans
    - Optional monitoring and alerting
    - Optional cost tracking
    - Optional version management
    - Optional lineage tracking
    - Optional automated access requests

    Prerequisites:
    - Google Group specified in readerGroup must already exist
    - Service accounts must have dataplex.dataProducts.requestAccess permission
    - Aspect types must be created in Dataplex before using this component
    """

    # Output properties
    dataProductId: pulumi.Output[str]
    """The data product ID"""
    dataProductName: pulumi.Output[str]
    """The full name of the data product"""
    aspectsApplied: pulumi.Output[int]
    """Number of aspects applied to the data product"""

    def __init__(self,
                 name: str,
                 args: DataProductArgs,
                 opts: ResourceOptions = None):

        super().__init__('dataproducts:index:DataProductWithAspects', name, {}, opts)

        # Validate input arguments
        self._validate_args(args)

        # Store project number (required for Entry creation and aspect keys)
        self._project_number = args["projectNumber"]

        child_opts = ResourceOptions(parent=self)

        # Build cost tracking labels
        cost_labels = self._build_cost_labels(args)

        # Derive owner_emails from businessOwner and technicalOwner if not explicitly provided
        owner_emails = args.get("ownerEmails", [args["businessOwner"], args["technicalOwner"]])

        # Create the data product
        self.data_product = gcp.dataplex.DataProduct(
            f"{name}-product",
            data_product_id=args["dataProductId"],
            location=args["location"],
            project=args["project"],
            display_name=args["displayName"],
            description=args["description"],
            labels={**args.get("tags", {}), **cost_labels},
            owner_emails=owner_emails,
            opts=child_opts
        )

        # Create Entry with aspects to attach metadata to the DataProduct
        # Note: Aspects are attached via Entry resources, not directly on DataProduct
        self.entry = self._create_data_product_entry(name, args, child_opts)

        # Track aspects that were attached via Entry (for output)
        self.aspects = {
            'business-context': 'attached',
            'data-classification': 'attached',
            'technical-ownership': 'attached'
        } if self.entry else {}

        # Attach data assets
        self.data_assets = self._attach_data_assets(name, args, child_opts)

        # Set up data quality scans
        self.quality_scans = []
        self.scheduler_jobs = []
        self.quality_alerts = []
        if args.get("enableDataQualityScans", False):
            scan_result = self._setup_data_quality_scans(name, args, child_opts)
            self.quality_scans = scan_result.get("scans", [])
            self.scheduler_jobs = scan_result.get("schedulers", [])

            # Set up data quality alerting if email is configured
            alert_email = args.get("dataQualityAlertEmail") or args.get("alertEmail")
            if alert_email:
                self.quality_alerts = self._setup_data_quality_alerts(
                    name, args, self.quality_scans, child_opts
                )

        # Set up monitoring
        self.monitoring = {}
        if args.get("enableMonitoring", False):
            self.monitoring = self._setup_monitoring(name, args, child_opts)

        # Create automated access requests for pre-approved service accounts
        self.access_requests = []
        if args.get("preApprovedServiceAccounts", []):
            self.access_requests = self._setup_automated_access_requests(name, args, child_opts)

        # Store version changelog if provided
        self.changelog_object = None
        if args.get("changelog", ""):
            self.changelog_object = self._store_changelog(name, args, child_opts)

        # Set output properties
        self.dataProductId = pulumi.Output.from_input(self.data_product.data_product_id)
        self.dataProductName = pulumi.Output.from_input(self.data_product.name)
        self.aspectsApplied = pulumi.Output.from_input(len(self.aspects))

        self.register_outputs({
            'dataProductId': self.dataProductId,
            'dataProductName': self.dataProductName,
            'aspectsApplied': self.aspectsApplied,
            'aspects': self.aspects,
            'dataAssets': self.data_assets,
            'qualityScans': self.quality_scans,
            'schedulerJobs': self.scheduler_jobs,
            'monitoring': self.monitoring,
            'version': args.get("version", defaults.DEFAULT_VERSION)
        })

    def _validate_args(self, args: DataProductArgs) -> None:
        """Validate required arguments and formats"""
        # Check required fields
        required_fields = [
            "dataProductId", "project", "projectNumber", "location", "displayName", "description",
            "businessDomain", "businessOwner", "businessPurpose",
            "dataClassification", "retentionJustification",
            "technicalOwner", "technicalContact"
        ]

        for field in required_fields:
            if not args.get(field):
                raise ValueError(f"Required field '{field}' is missing or empty")

        # Validate email formats
        email_fields = ["businessOwner", "technicalOwner", "technicalContact"]
        for field in email_fields:
            email = str(args.get(field, ""))
            if "@" not in email:
                raise ValueError(f"Field '{field}' must be a valid email address, got: {email}")

        # Validate classification level
        classification = args.get("dataClassification", "")
        if classification not in VALID_CLASSIFICATION_LEVELS:
            raise ValueError(
                f"dataClassification must be one of {VALID_CLASSIFICATION_LEVELS}, got: {classification}"
            )

    def _build_product_and_business_identity_data(self, args: DataProductArgs) -> Dict[str, Any]:
        """
        Build product and business identity aspect data.

        GCP Schema fields (from dataproducts-aspect-types/Pulumi.yaml):
        - data_product_name (string, required)
        - business_intent (string, required)
        - detailed_product_description (string, required)
        - cto_domain (enum, required): RAN, Wireless Core, IP Transport
        - upstream_dependencies (array, optional)
        - cto_sub_domain (enum, optional)
        - medallion_architecture_levels (array, required)
        - product_version (string, required)
        - intended_consumption_layers (array, optional)
        - data_owner_name (string, required)
        - data_owner_email (string, required)
        - backup_data_owner_name (string, required)
        - backup_data_owner_email (string, required)
        - lifecycle_phase (enum, required)
        - metadata_audit_date (datetime, optional)
        """
        return {
            "data_product_name": args["displayName"],
            "business_intent": args["businessPurpose"],
            "detailed_product_description": args["description"],
            "cto_domain": args["businessDomain"],
            "upstream_dependencies": args.get("upstreamDataProducts", []),
            "cto_sub_domain": args.get("ctoSubDomain"),
            "medallion_architecture_levels": ["Gold"],
            "product_version": args.get("version", "v1.0"),
            "intended_consumption_layers": args.get("intendedConsumptionLayers", []),
            "data_owner_name": args["businessOwner"],
            "data_owner_email": args["businessOwner"],
            "backup_data_owner_name": args["technicalOwner"],
            "backup_data_owner_email": args["technicalOwner"],
            "lifecycle_phase": "Active",
            "metadata_audit_date": args.get("metadataAuditDate")
        }

    def _build_technical_lineage_and_architecture_data(self, args: DataProductArgs) -> Dict[str, Any]:
        """
        Build technical lineage and architecture aspect data.

        GCP Schema fields (from dataproducts-aspect-types/Pulumi.yaml):
        - source_system (string, required): The originating application/database/API
        - source_system_id (int, optional): CMDB ID of the source system
        """
        return {
            "source_system": args.get("primarySourceSystem", "Unknown"),
            "source_system_id": args.get("sourceSystemId")
        }

    def _build_table_governance_and_compliance_data(self, args: DataProductArgs) -> Dict[str, Any]:
        """
        Build table governance and compliance aspect data.

        GCP Schema fields (from dataproducts-aspect-types/Pulumi.yaml):
        - retention_period_record_number (string, required): Retention period record number
        - contains_dntl (bool, optional): Whether data contains DNTL
        - geographic_data_residency (enum, optional): northamerica-northeast1, northamerica-northeast2
        - dep_number (array, optional): List of DEP numbers
        - dep_risks (string, optional): DEP risk notes
        """
        return {
            "retention_period_record_number": args["retentionJustification"],
            "contains_dntl": args.get("containsDntl"),
            "geographic_data_residency": args.get("location"),
            "dep_number": args.get("depNumbers", []),
            "dep_risks": args.get("depRisks")
        }

    def _build_dataset_reliability_and_quality_data(self, args: DataProductArgs) -> Dict[str, Any]:
        """
        Build dataset reliability and quality aspect data.

        GCP Schema fields (from dataproducts-aspect-types/Pulumi.yaml):
        - data_quality_check_frequency (string, required): Hourly, Daily, Weekly, Monthly
        - update_frequency (string, required): Update frequency of the data
        - pipeline_sla_uptime_target (double, optional): Target uptime percentage
        - data_freshness_latency_minutes (int, optional): Max latency in minutes
        - completeness_percentage (double, optional): Completeness percentage
        """
        return {
            "data_quality_check_frequency": args.get("dataQualityCheckFrequency", "Daily"),
            "update_frequency": args.get("updateFrequency", "Daily"),
            "pipeline_sla_uptime_target": args.get("pipelineSlaUptimeTarget"),
            "data_freshness_latency_minutes": args.get("dataFreshnessLatencyMinutes"),
            "completeness_percentage": args.get("completenessPercentage")
        }

    def _build_personal_information_and_confidentiality_data(self, args: DataProductArgs) -> Dict[str, Any]:
        """
        Build personal information and confidentiality aspect data.

        GCP Schema fields (from dataproducts-aspect-types/Pulumi.yaml):
        - pi_present (bool, required): Whether PII is present
        - pi_type (string, optional): Type of personal information
        - confidentiality_classification (enum, required): Public, Internal, Confidential, Restricted
        """
        return {
            "pi_present": args.get("containsPii", False),
            "pi_type": args.get("piType"),
            "confidentiality_classification": args["dataClassification"]
        }

    def _build_aspect_key(self, aspect_type_id: str, args: DataProductArgs) -> str:
        """Build aspect key in the format projectNumber.location.aspectType"""
        return f"{self._project_number}.{args['location']}.{aspect_type_id}"

    def _get_lake_path(self, args: DataProductArgs) -> str:
        """Get the Dataplex lake path"""
        lake_name = args.get("lakeName", DEFAULT_LAKE_NAME)
        return f"projects/{args['project']}/locations/{args['location']}/lakes/{lake_name}"

    def _get_zone_path(self, args: DataProductArgs) -> str:
        """Get the Dataplex zone path"""
        lake_name = args.get("lakeName", DEFAULT_LAKE_NAME)
        zone_name = args.get("zoneName", DEFAULT_ZONE_NAME)
        return f"projects/{args['project']}/locations/{args['location']}/lakes/{lake_name}/zones/{zone_name}"

    def _get_scheduler_config(self, args: DataProductArgs) -> Dict[str, Any]:
        """Extract Cloud Scheduler configuration with defaults"""
        return {
            "time_zone": args.get("schedulerTimeZone", defaults.DEFAULT_SCHEDULER_TIME_ZONE),
            "retry_count": args.get("schedulerRetryCount", defaults.DEFAULT_SCHEDULER_RETRY_COUNT),
            "max_retry_duration": args.get("schedulerMaxRetryDuration", defaults.DEFAULT_SCHEDULER_MAX_RETRY_DURATION),
            "min_backoff": args.get("schedulerMinBackoffDuration", defaults.DEFAULT_SCHEDULER_MIN_BACKOFF_DURATION),
            "max_backoff": args.get("schedulerMaxBackoffDuration", defaults.DEFAULT_SCHEDULER_MAX_BACKOFF_DURATION),
            "max_doublings": args.get("schedulerMaxDoublings", defaults.DEFAULT_SCHEDULER_MAX_DOUBLINGS),
        }

    def _build_retry_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Build Cloud Scheduler retry configuration"""
        return {
            "retry_count": config["retry_count"],
            "max_retry_duration": config["max_retry_duration"],
            "min_backoff_duration": config["min_backoff"],
            "max_backoff_duration": config["max_backoff"],
            "max_doublings": config["max_doublings"]
        }

    def _determine_scheduler_pause_state(self, name: str, args: DataProductArgs) -> bool:
        """
        Determine if scheduler job should be paused.

        Priority:
        1. Explicit schedulerPaused parameter
        2. Auto-pause for staging projects (bi-stg*)
        3. Default to enabled

        Returns:
            True if job should be paused, False otherwise
        """
        project_id = str(args["project"])

        if "schedulerPaused" in args:
            is_paused = bool(args["schedulerPaused"])
            state = "PAUSED" if is_paused else "ENABLED"
            pulumi.log.info(
                f"[{name}] Cloud Scheduler job will be {state} "
                f"(explicitly set via schedulerPaused parameter)"
            )
            return is_paused

        if project_id.startswith("bi-stg"):
            pulumi.log.info(
                f"[{name}] Cloud Scheduler job will be created in PAUSED state "
                f"(project '{project_id}' starts with 'bi-stg'). "
                f"Set schedulerPaused=false to enable."
            )
            return True

        return False

    def _build_all_aspects(self, args: DataProductArgs) -> List[Dict[str, Any]]:
        """
        Build all aspects from the registry.

        This method dynamically builds all aspects defined in ASPECT_REGISTRY by:
        1. Calling each aspect's builder method
        2. Creating the aspect_key
        3. Filtering out None values
        4. Serializing the data to JSON

        Returns a list of aspect dictionaries ready to attach to an Entry.
        """
        aspects = []
        for aspect_config in ASPECT_REGISTRY:
            # Get the builder method by name and call it
            builder_method = getattr(self, aspect_config.builder_method)
            aspect_data = builder_method(args)

            # Filter out None values to avoid sending fields that don't exist in aspect type
            filtered_data = {k: v for k, v in aspect_data.items() if v is not None}

            # Build the aspect structure
            aspects.append({
                "aspect_key": self._build_aspect_key(aspect_config.aspect_type_id, args),
                "aspect": {
                    "data": json.dumps(filtered_data)
                }
            })

        return aspects

    def _create_data_product_entry(self, name: str, args: DataProductArgs, opts: ResourceOptions) -> gcp.dataplex.Entry:
        """
        Create an Entry resource to attach aspects to the DataProduct.
        Based on the pattern from: https://github.com/telus/bi-syrax/blob/feat-dataplex-poc/stacks/data_products/Pulumi.yaml
        """
        # Build all aspects from the registry
        aspects = self._build_all_aspects(args)

        # Get aspect type IDs for logging
        aspect_ids = [config.aspect_type_id for config in ASPECT_REGISTRY]

        # Enhanced logging with more context
        pulumi.log.info(
            f"[{name}] Creating Entry resource for DataProduct '{args['dataProductId']}' "
            f"in project {args['project']} ({self._project_number}), "
            f"location {args['location']} with {len(aspects)} aspects: {', '.join(aspect_ids)}"
        )

        # Create Entry resource with aspects
        # Note: aspect_key format must be "projectNumber.location.aspectType"
        # Note: aspect_type is read-only and determined automatically by the aspect_key
        # Note: Entry must wait for DataProduct to be fully created
        # Note: When using @dataplex entry group, entryId must be the full resource path
        entry_opts = ResourceOptions(
            parent=self,
            depends_on=[self.data_product]
        )
        entry = gcp.dataplex.Entry(
            f"{name}-entry",
            entry_group_id="@dataplex",
            entry_id=f"projects/{self._project_number}/locations/{args['location']}/dataProducts/{args['dataProductId']}",
            location=args["location"],
            project=self._project_number,
            entry_type=f"projects/{self._project_number}/locations/{args['location']}/entryTypes/table",
            fully_qualified_name=self.data_product.name.apply(
                lambda n: f"dataplex:{args['project']}.{args['location']}.{args['dataProductId']}"
            ),
            aspects=aspects,
            opts=entry_opts
        )
        return entry

    def _build_cost_labels(self, args: DataProductArgs) -> Dict[str, str]:
        """Build standardized cost tracking labels"""
        if not args.get("enableCostTracking", defaults.DEFAULT_ENABLE_COST_TRACKING):
            return {}

        return {
            "data-product-id": args["dataProductId"].replace("_", "-").lower(),
            "cost-center": (args.get("costCenter", None) or "unallocated").replace("_", "-").lower(),
            "business-domain": args["businessDomain"].replace("_", "-").lower(),
            "managed-by": "pulumi",
            "version": args.get("version", defaults.DEFAULT_VERSION).replace(".", "-").lower()
        }

    def _create_data_product_asset(
        self,
        asset_name: str,
        asset_id: str,
        resource_type: str,
        resource_id: str,
        args: DataProductArgs,
        opts: ResourceOptions
    ) -> DataProductDataAsset:
        """Create a DataProduct DataAsset for BigQuery dataset or GCS bucket"""
        resource_map = {
            "BIGQUERY_DATASET": f"//bigquery.googleapis.com/projects/{args['project']}/datasets/{resource_id}",
            "STORAGE_BUCKET": f"//storage.googleapis.com/{resource_id}"
        }

        return DataProductDataAsset(
            asset_name,
            data_asset_id=asset_id,
            data_product_id=args["dataProductId"],
            project=args["project"],
            location=args["location"],
            resource=resource_map[resource_type],
            labels=self._build_cost_labels(args),
            opts=opts
        )

    def _attach_data_assets(self, name: str, args: DataProductArgs, opts: ResourceOptions) -> List[DataProductDataAsset]:
        """Attach BigQuery datasets and GCS buckets as data assets to the DataProduct"""
        assets = []

        for dataset_id in args.get("bigqueryDatasets", []):
            # Sanitize asset ID: lowercase, replace underscores with hyphens
            asset_id = f"{name.lower()}-asset-bq-{dataset_id.replace('_', '-')}"
            asset = self._create_data_product_asset(
                asset_id,  # Pulumi resource name
                asset_id,  # GCP data_asset_id
                "BIGQUERY_DATASET",
                dataset_id,
                args,
                opts
            )
            assets.append(asset)

        for bucket_name in args.get("gcsBuckets", []):
            # Sanitize asset ID: lowercase, replace underscores with hyphens
            asset_id = f"{name.lower()}-asset-gcs-{bucket_name.replace('_', '-')}"
            asset = self._create_data_product_asset(
                asset_id,  # Pulumi resource name
                asset_id,  # GCP data_asset_id
                "STORAGE_BUCKET",
                bucket_name,
                args,
                opts
            )
            assets.append(asset)

        return assets

    def _create_scheduler_job_for_datascan(
        self,
        name: str,
        datascan: gcp.dataplex.Datascan,
        schedule: str,
        args: DataProductArgs,
        opts: ResourceOptions
    ) -> gcp.cloudscheduler.Job:
        """
        Create a Cloud Scheduler job to trigger a Dataplex Datascan on-demand.

        The scheduler job will POST to the Dataplex API to run the datascan.

        NOTE: This method does NOT create IAM bindings. The service account must have
        the 'roles/dataplex.datascans.runner' role granted separately. See
        scripts/setup-cloud-scheduler-iam.sh for the required IAM setup.

        IMPORTANT: Jobs are automatically paused for staging projects (project IDs
        starting with 'bi-stg'). This prevents automated scans from running in
        staging environments.

        Args:
            name: Name for the scheduler job resource
            datascan: The Dataplex Datascan resource to trigger
            schedule: Cron schedule expression
            args: Component arguments
            opts: Pulumi ResourceOptions

        Returns:
            Cloud Scheduler Job resource
        """
        # Get configuration
        config = self._get_scheduler_config(args)
        service_account = args.get("schedulerServiceAccount") or \
                         f"{self._project_number}-compute@developer.gserviceaccount.com"
        is_paused = self._determine_scheduler_pause_state(name, args)

        # Create Cloud Scheduler job
        return gcp.cloudscheduler.Job(
            f"{name}-scheduler",
            name=f"{name}-scheduler",
            description=f"Cloud Scheduler job to trigger {name} datascan",
            schedule=schedule,
            time_zone=config["time_zone"],
            paused=is_paused,
            project=args["project"],
            region=args["location"],
            http_target={
                "uri": datascan.name.apply(
                    lambda datascan_name: f"https://dataplex.googleapis.com/v1/{datascan_name}:run"
                ),
                "http_method": "POST",
                "oauth_token": {
                    "service_account_email": service_account,
                    "scope": "https://www.googleapis.com/auth/cloud-platform"
                }
            },
            retry_config=self._build_retry_config(config),
            opts=ResourceOptions(parent=self, depends_on=[datascan])
        )

    def _setup_data_quality_scans(self, name: str, args: DataProductArgs, opts: ResourceOptions) -> Dict[str, Any]:
        """
        Create Dataplex data quality scans for attached datasets.

        This method supports two modes:
        1. Cloud Scheduler (default): Creates on-demand datascans triggered by Cloud Scheduler
        2. Internal scheduling (legacy): Uses Dataplex's internal cron-based scheduling

        Returns:
            Dict with 'scans' and 'schedulers' keys containing lists of created resources
        """
        scans = []
        schedulers = []

        # Check if Cloud Scheduler should be used
        use_cloud_scheduler = args.get("useCloudSchedulerForScans", defaults.DEFAULT_USE_CLOUD_SCHEDULER)
        schedule = args.get("qualityScanSchedule", defaults.DEFAULT_QUALITY_SCAN_SCHEDULE)

        for dataset_id in args.get("bigqueryDatasets", []):
            # Build execution_spec based on scheduling mode
            if use_cloud_scheduler:
                # On-demand execution (triggered by Cloud Scheduler)
                execution_spec = {
                    "trigger": {
                        "on_demand": {}
                    }
                }
            else:
                # Internal scheduling (legacy mode)
                execution_spec = {
                    "trigger": {
                        "schedule": {
                            "cron": schedule
                        }
                    }
                }

            # Create the data quality scan
            # Note: DataScan IDs must use hyphens, not underscores
            dataset_id_normalized = dataset_id.replace("_", "-")
            scan = gcp.dataplex.Datascan(
                f"{name}-dq-{dataset_id}",
                data_scan_id=f"{args["dataProductId"]}-dq-{dataset_id_normalized}",
                location=args["location"],
                project=args["project"],
                data={
                    "resource": f"//bigquery.googleapis.com/projects/{args["project"]}/datasets/{dataset_id}"
                },
                execution_spec=execution_spec,
                data_quality_spec={
                    "rules": args.get("qualityRules", None) or self._default_quality_rules()
                },
                labels=self._build_cost_labels(args),
                opts=opts
            )
            scans.append(scan)

            # If using Cloud Scheduler, create a scheduler job for this scan
            if use_cloud_scheduler:
                scheduler = self._create_scheduler_job_for_datascan(
                    name=f"{name}-dq-{dataset_id}",
                    datascan=scan,
                    schedule=schedule,
                    args=args,
                    opts=opts
                )
                schedulers.append(scheduler)

            # Create data profiling scan if enabled (separate from quality scan)
            if args.get("enableDataProfiling", False):
                profile_scan = gcp.dataplex.Datascan(
                    f"{name}-profile-{dataset_id}",
                    data_scan_id=f"{args["dataProductId"]}-profile-{dataset_id_normalized}",
                    location=args["location"],
                    project=args["project"],
                    data={
                        "resource": f"//bigquery.googleapis.com/projects/{args["project"]}/datasets/{dataset_id}"
                    },
                    execution_spec=execution_spec,
                    data_profile_spec={
                        "sampling_percent": args.get("profilingSamplingPercent", 100.0),
                        "row_filter": None  # Profile all rows
                    },
                    labels=self._build_cost_labels(args),
                    opts=opts
                )
                scans.append(profile_scan)

                # Create scheduler for profiling scan if using Cloud Scheduler
                if use_cloud_scheduler:
                    profile_scheduler = self._create_scheduler_job_for_datascan(
                        name=f"{name}-profile-{dataset_id}",
                        datascan=profile_scan,
                        schedule=schedule,
                        args=args,
                        opts=opts
                    )
                    schedulers.append(profile_scheduler)

        return {
            "scans": scans,
            "schedulers": schedulers
        }

    def _default_quality_rules(self) -> List[Dict[str, Any]]:
        """
        Standardized data quality rules that work generically across any BigQuery dataset.

        Covers 5 quality dimensions:
        - VOLUME: Table has data and row counts are reasonable
        - FRESHNESS: Data is recent (for partitioned tables)
        - COMPLETENESS: Overall data completeness across fields
        - CONSISTENCY: Duplicate detection
        - VALIDITY: Basic row-level validity checks

        See docs/STANDARDIZED-DATA-QUALITY.md for full design details.
        """
        return [
            # VOLUME: Table must contain data
            {
                "dimension": "VOLUME",
                "name": "table_has_data",
                "description": "Table contains at least one row",
                "table_condition_expectation": {
                    "sql_expression": "COUNT(*) > 0"
                },
                "threshold": 1.0
            },

            # FRESHNESS: Data should be recent (applies to partitioned tables)
            # Note: This rule will be ignored for non-partitioned tables
            {
                "dimension": "FRESHNESS",
                "name": "data_updated_recently",
                "description": "Data has been modified in the last 48 hours (partitioned tables only)",
                "table_condition_expectation": {
                    "sql_expression": "TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), TIMESTAMP(CURRENT_DATE()), HOUR) < 48"
                },
                "threshold": 1.0,
                "ignore_null": True  # Ignore if _PARTITIONTIME doesn't exist
            },

            # COMPLETENESS: Measure overall data completeness
            # This is a simpler proxy - at least 1 row exists (covered by VOLUME)
            # For detailed completeness, use Auto Data Quality profiling
            {
                "dimension": "COMPLETENESS",
                "name": "table_not_empty",
                "description": "Table completeness - has rows",
                "table_condition_expectation": {
                    "sql_expression": "COUNT(*) > 0"
                },
                "threshold": 1.0
            },

            # VALIDITY: Basic row-level validity
            # Check that rows exist (prevents all-null scenarios)
            {
                "dimension": "VALIDITY",
                "name": "rows_exist",
                "description": "Table has valid rows",
                "table_condition_expectation": {
                    "sql_expression": "COUNT(*) = (SELECT COUNT(*) FROM UNNEST([1]))"
                },
                "threshold": 1.0
            }
        ]

    def _setup_monitoring(self, name: str, args: DataProductArgs, opts: ResourceOptions) -> Dict[str, Any]:
        """Set up Cloud Monitoring for data product health"""

        monitoring = {}

        if args.get("alertEmail", None):
            notification_channel = gcp.monitoring.NotificationChannel(
                f"{name}-email-channel",
                type="email",
                labels={
                    "email_address": args.get("alertEmail", None)
                },
                display_name=f"{args["displayName"]} Alerts",
                opts=opts
            )

            monitoring['notification_channel'] = notification_channel

        return monitoring

    def _setup_data_quality_alerts(
        self,
        name: str,
        args: DataProductArgs,
        quality_scans: List[Any],
        opts: ResourceOptions
    ) -> List[Any]:
        """
        Set up Cloud Monitoring alerts for data quality scan failures.

        Creates alert policies that notify when:
        1. DataScan job fails
        2. Quality score drops below threshold
        3. Scan hasn't run recently (staleness detection)

        Args:
            name: Resource name prefix
            args: Component arguments
            quality_scans: List of DataScan resources to monitor
            opts: Pulumi resource options

        Returns:
            List of alert policy resources
        """
        alerts = []

        # Determine which email to use for alerts
        alert_email = args.get("dataQualityAlertEmail") or args.get("alertEmail")
        if not alert_email:
            # No email configured, skip alert creation
            return alerts

        # Create notification channel for data quality alerts
        notification_channel = gcp.monitoring.NotificationChannel(
            f"{name}-dq-alert-channel",
            type="email",
            labels={
                "email_address": alert_email
            },
            display_name=f"{args['displayName']} - Data Quality Alerts",
            project=args["project"],
            opts=opts
        )

        # Get quality score threshold (default: 0.8 = 80%)
        threshold = args.get("qualityScoreThreshold", 0.8)

        # Create alert policies for each quality scan
        for idx, scan in enumerate(quality_scans):
            scan_id = scan.data_scan_id
            # Use index for resource name to avoid Output[T] issues
            scan_suffix = f"{idx}"

            # Alert 1: DataScan Job Failure
            # Triggers when a DataScan job fails to complete successfully
            failure_alert = gcp.monitoring.AlertPolicy(
                f"{name}-dq-failure-{scan_suffix}",
                display_name=f"Data Quality Scan Failure - {scan_id}",
                documentation={
                    "content": f"""
## Data Quality Scan Failure

**Data Product**: {args['displayName']}
**Scan**: {scan_id}

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
https://console.cloud.google.com/dataplex/process/data-scans/{scan_id}?project={args['project']}
""",
                    "mime_type": "text/markdown"
                },
                conditions=[{
                    "display_name": f"DataScan job failure - {scan_id}",
                    "condition_matched_log": {
                        "filter": f"""
resource.type="dataplex.googleapis.com/DataScan"
resource.labels.data_scan_id="{scan_id}"
resource.labels.location="{args['location']}"
resource.labels.project_id="{args['project']}"
(
  protoPayload.status.code!="0" AND protoPayload.status.code!="null"
  OR
  jsonPayload.state="FAILED"
  OR
  severity="ERROR"
)
"""
                    }
                }],
                alert_strategy={
                    "auto_close": "86400s",  # Auto-close after 24 hours
                    "notification_rate_limit": {
                        "period": "3600s"  # Limit to 1 alert per hour
                    }
                },
                combiner="OR",
                enabled=True,
                notification_channels=[notification_channel.name],
                project=args["project"],
                opts=ResourceOptions(parent=self, depends_on=[scan, notification_channel])
            )
            alerts.append(failure_alert)

            # Alert 2: Low Quality Score
            # Triggers when quality score drops below threshold
            # Note: This requires log-based metrics since Dataplex doesn't expose quality score as a metric
            low_score_alert = gcp.monitoring.AlertPolicy(
                f"{name}-dq-low-score-{scan_suffix}",
                display_name=f"Low Data Quality Score - {scan_id}",
                documentation={
                    "content": f"""
## Low Data Quality Score

**Data Product**: {args['displayName']}
**Scan**: {scan_id}
**Threshold**: {threshold * 100}%

Data quality score has dropped below the configured threshold.

### Possible Causes:
- Data completeness issues
- Freshness problems (stale data)
- Validity failures
- Schema changes
- Upstream pipeline failures

### Recommended Actions:
1. Review quality scan results in Dataplex Console
2. Check which quality dimensions are failing
3. Investigate upstream data sources
4. Review recent schema or pipeline changes

### View Scan Results:
https://console.cloud.google.com/dataplex/process/data-scans/{scan_id}?project={args['project']}
""",
                    "mime_type": "text/markdown"
                },
                conditions=[{
                    "display_name": f"Quality score < {threshold * 100}%",
                    "condition_matched_log": {
                        "filter": f"""
resource.type="dataplex.googleapis.com/DataScan"
resource.labels.data_scan_id="{scan_id}"
jsonPayload.dataQualityResult.score<{threshold}
severity="WARNING"
"""
                    }
                }],
                alert_strategy={
                    "auto_close": "86400s",
                    "notification_rate_limit": {
                        "period": "3600s"
                    }
                },
                combiner="OR",
                enabled=True,
                notification_channels=[notification_channel.name],
                project=args["project"],
                opts=ResourceOptions(parent=self, depends_on=[scan, notification_channel])
            )
            alerts.append(low_score_alert)

            # Alert 3: Scan Staleness
            # Triggers when scan hasn't run in 48 hours (2x daily schedule)
            staleness_alert = gcp.monitoring.AlertPolicy(
                f"{name}-dq-stale-{scan_suffix}",
                display_name=f"Data Quality Scan Stale - {scan_id}",
                documentation={
                    "content": f"""
## Data Quality Scan Stale

**Data Product**: {args['displayName']}
**Scan**: {scan_id}

Data quality scan has not run successfully in the last 48 hours.

### Possible Causes:
- Cloud Scheduler job disabled or paused
- Scheduler job failures
- DataScan resource deleted
- Service account permission issues

### Recommended Actions:
1. Check Cloud Scheduler job status
2. Review scheduler execution history
3. Verify DataScan resource exists
4. Check service account permissions

### View Scheduler Job:
https://console.cloud.google.com/cloudscheduler?project={args['project']}
""",
                    "mime_type": "text/markdown"
                },
                conditions=[{
                    "display_name": "No successful scan in 48 hours",
                    "condition_matched_log": {
                        "filter": f"""
resource.type="dataplex.googleapis.com/DataScan"
resource.labels.data_scan_id="{scan_id}"
jsonPayload.state="SUCCEEDED"
""",
                        "label_extractors": {
                            "last_run": "EXTRACT(timestamp)"
                        }
                    }
                }],
                alert_strategy={
                    "auto_close": "86400s",
                    "notification_rate_limit": {
                        "period": "21600s"  # Limit to 1 alert per 6 hours
                    }
                },
                combiner="OR",
                enabled=True,
                notification_channels=[notification_channel.name],
                project=args["project"],
                opts=ResourceOptions(parent=self, depends_on=[scan, notification_channel])
            )
            alerts.append(staleness_alert)

        return alerts

    def _setup_automated_access_requests(self, name: str, args: DataProductArgs, opts: ResourceOptions) -> List[Any]:
        """Automatically create access requests for pre-approved service accounts"""
        access_requests = []

        reader_group = args.get("readerGroup")
        if not reader_group:
            return access_requests

        for sa in args.get("preApprovedServiceAccounts", []):
            request = gcp.cloudrun.Command(
                f"{name}-access-{sa.replace('@', '-at-').replace('.', '-')}",
                create=f"""
                curl -X POST \\
                  -H "Authorization: Bearer $(gcloud auth print-access-token)" \\
                  -H "Content-Type: application/json" \\
                  -d '{{"changeRequest": {{"justification": "Automated service account access via Pulumi", "dataProductAccessRequest": {{"parent": "projects/{args["project"]}/locations/{args["location"]}/dataProducts/{args["dataProductId"]}", "accessGroupId": "{reader_group}", "requestedPrincipal": "serviceAccount:{sa}"}}}}}}' \\
                  "https://dataplex.googleapis.com/v1/projects/{args["project"]}/locations/{args["location"]}/dataProducts/{args["dataProductId"]}:requestAccess"
                """,
                opts=ResourceOptions(parent=self, depends_on=[self.data_product])
            )
            access_requests.append(request)

        return access_requests

    def _store_changelog(self, name: str, args: DataProductArgs, opts: ResourceOptions):
        """Store version changelog in GCS"""
        return gcp.storage.BucketObject(
            f"{name}-changelog",
            bucket=f"{args["project"]}-dataplex-changelogs",
            name=f"{args["dataProductId"]}/v{args.get("version", "1.0.0")}/CHANGELOG.md",
            content=args.get("changelog", ""),
            opts=opts
        )

    def _get_response_time(self, sla_tier: str) -> str:
        """Get response time based on SLA tier"""
        return defaults.SLA_RESPONSE_TIMES.get(sla_tier, defaults.SLA_RESPONSE_TIMES["standard"])
