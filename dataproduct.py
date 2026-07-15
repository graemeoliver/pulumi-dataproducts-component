"""
Dataplex Data Product Component with Standardized Aspects

This module provides a Pulumi ComponentResource for creating Dataplex data products
with mandatory business, compliance, and technical aspects.
"""

import pulumi
from pulumi import ComponentResource, ResourceOptions, Output, Input
import pulumi_gcp as gcp
import json
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

class AspectConfig:
    """Configuration for a single aspect type"""
    def __init__(self, aspect_type_id: str, builder_method: str, description: str):
        self.aspect_type_id = aspect_type_id
        """The AspectType ID in GCP Dataplex"""
        self.builder_method = builder_method
        """Name of the method that builds this aspect's data"""
        self.description = description
        """Human-readable description of the aspect"""


# Registry of all aspects to attach to DataProducts
# To add a new aspect:
# 1. Create the AspectType in GCP (via dataproducts-aspect-types stack)
# 2. Add an AspectConfig entry here
# 3. Create a corresponding _build_<name>_aspect_data() method
ASPECT_REGISTRY = [
    AspectConfig(
        aspect_type_id="business-context",
        builder_method="_build_business_aspect_data",
        description="Business metadata including ownership and purpose"
    ),
    AspectConfig(
        aspect_type_id="data-classification",
        builder_method="_build_classification_aspect_data",
        description="Data classification and sensitivity metadata"
    ),
    AspectConfig(
        aspect_type_id="technical-ownership",
        builder_method="_build_ownership_aspect_data",
        description="Technical ownership and contact information"
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
    displayName: Input[str]
    """Human-readable name for the data product"""
    description: Input[str]
    """Detailed description of the data product"""
    accessGroups: Input[Dict[str, Any]]
    """Access control groups configuration"""

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
    - Google Groups specified in access_groups must already exist
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

        # Get and cache project number early (required for Entry creation)
        try:
            self._project_data = gcp.organizations.get_project(project_id=args["project"])
        except Exception as e:
            raise ValueError(f"Failed to get project number for project '{args['project']}': {e}")

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
        if args.get("enableDataQualityScans", False):
            self.quality_scans = self._setup_data_quality_scans(name, args, child_opts)

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
            'monitoring': self.monitoring,
            'version': args.get("version", defaults.DEFAULT_VERSION)
        })

    def _validate_args(self, args: DataProductArgs) -> None:
        """Validate required arguments and formats"""
        # Check required fields
        required_fields = [
            "dataProductId", "project", "location", "displayName", "description",
            "businessDomain", "businessOwner", "businessPurpose",
            "dataClassification", "retentionJustification",
            "technicalOwner", "technicalContact", "accessGroups"
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

    def _build_business_aspect_data(self, args: DataProductArgs) -> Dict[str, Any]:
        """
        Build business context aspect data.

        GCP Schema (dataproducts-aspect-types/Pulumi.yaml):
        - business_domain (string, required): Business domain this data product belongs to
        - business_owner (string, required): Email of the business owner
        - business_purpose (string, required): Business purpose of this data
        - glossary_terms (array, optional): Associated glossary terms
        """
        return {
            "business_domain": args["businessDomain"],
            "business_owner": args["businessOwner"],
            "business_purpose": args["businessPurpose"],
            "glossary_terms": args.get("glossaryTerms", [])
        }

    def _build_classification_aspect_data(self, args: DataProductArgs) -> Dict[str, Any]:
        """
        Build data classification aspect data.

        GCP Schema (dataproducts-aspect-types/Pulumi.yaml):
        - classification_level (string, required): public, internal, confidential, or restricted
        - contains_pii (bool, required): Whether data contains PII
        """
        return {
            "classification_level": args["dataClassification"],
            "contains_pii": args.get("containsPii", defaults.DEFAULT_CONTAINS_PII)
        }

    def _build_ownership_aspect_data(self, args: DataProductArgs) -> Dict[str, Any]:
        """
        Build technical ownership aspect data.

        GCP Schema (dataproducts-aspect-types/Pulumi.yaml):
        - technical_owner (string, required): Technical owner email
        - technical_contact (string, required): Technical contact email
        """
        return {
            "technical_owner": args["technicalOwner"],
            "technical_contact": args["technicalContact"]
        }

    def _build_aspect_key(self, aspect_type_id: str, args: DataProductArgs) -> str:
        """Build aspect key in the format projectNumber.location.aspectType"""
        return f"{self._project_data.number}.{args['location']}.{aspect_type_id}"

    def _get_lake_path(self, args: DataProductArgs) -> str:
        """Get the Dataplex lake path"""
        lake_name = args.get("lakeName", DEFAULT_LAKE_NAME)
        return f"projects/{args['project']}/locations/{args['location']}/lakes/{lake_name}"

    def _get_zone_path(self, args: DataProductArgs) -> str:
        """Get the Dataplex zone path"""
        lake_name = args.get("lakeName", DEFAULT_LAKE_NAME)
        zone_name = args.get("zoneName", DEFAULT_ZONE_NAME)
        return f"projects/{args['project']}/locations/{args['location']}/lakes/{lake_name}/zones/{zone_name}"

    def _build_all_aspects(self, args: DataProductArgs) -> List[Dict[str, Any]]:
        """
        Build all aspects from the registry.

        This method dynamically builds all aspects defined in ASPECT_REGISTRY by:
        1. Calling each aspect's builder method
        2. Creating the aspect_key
        3. Serializing the data to JSON

        Returns a list of aspect dictionaries ready to attach to an Entry.
        """
        aspects = []
        for aspect_config in ASPECT_REGISTRY:
            # Get the builder method by name and call it
            builder_method = getattr(self, aspect_config.builder_method)
            aspect_data = builder_method(args)

            # Build the aspect structure
            aspects.append({
                "aspect_key": self._build_aspect_key(aspect_config.aspect_type_id, args),
                "aspect": {
                    "data": json.dumps(aspect_data)
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
            f"in project {args['project']} ({self._project_data.number}), "
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
            entry_id=f"projects/{self._project_data.number}/locations/{args['location']}/dataProducts/{args['dataProductId']}",
            location=args["location"],
            project=self._project_data.number,
            entry_type=f"projects/{self._project_data.number}/locations/{args['location']}/entryTypes/table",
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

    def _attach_data_assets(self, name: str, args: DataProductArgs, opts: ResourceOptions) -> List[gcp.dataplex.Asset]:
        """Attach BigQuery datasets and GCS buckets as data assets"""
        assets = []

        lake_path = self._get_lake_path(args)
        zone_path = self._get_zone_path(args)

        for dataset_id in args.get("bigqueryDatasets", []):
            asset = gcp.dataplex.Asset(
                f"{name}-asset-bq-{dataset_id}",
                lake=lake_path,
                dataplex_zone=zone_path,
                location=args["location"],
                discovery_spec={
                    "enabled": True,
                    "schedule": "0 */12 * * *"
                },
                resource_spec={
                    "name": f"//bigquery.googleapis.com/projects/{args['project']}/datasets/{dataset_id}",
                    "type": "BIGQUERY_DATASET"
                },
                labels=self._build_cost_labels(args),
                opts=opts
            )
            assets.append(asset)

        for bucket_name in args.get("gcsBuckets", []):
            asset = gcp.dataplex.Asset(
                f"{name}-asset-gcs-{bucket_name}",
                lake=lake_path,
                dataplex_zone=zone_path,
                location=args["location"],
                discovery_spec={
                    "enabled": True,
                    "schedule": "0 */12 * * *"
                },
                resource_spec={
                    "name": f"//storage.googleapis.com/{bucket_name}",
                    "type": "STORAGE_BUCKET"
                },
                labels=self._build_cost_labels(args),
                opts=opts
            )
            assets.append(asset)

        return assets

    def _setup_data_quality_scans(self, name: str, args: DataProductArgs, opts: ResourceOptions) -> List[gcp.dataplex.Datascan]:
        """Create Dataplex data quality scans for attached datasets"""
        scans = []

        for dataset_id in args.get("bigqueryDatasets", []):
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
                        "schedule": {
                            "cron": args.get("qualityScanSchedule", "0 2 * * *")
                        }
                    }
                },
                data_quality_spec={
                    "rules": args.get("qualityRules", None) or self._default_quality_rules()
                },
                labels=self._build_cost_labels(args),
                opts=opts
            )
            scans.append(scan)

        return scans

    def _default_quality_rules(self) -> List[Dict[str, Any]]:
        """Default data quality rules"""
        return [
            {
                "dimension": "COMPLETENESS",
                "non_null_expectation": {}
            },
            {
                "dimension": "VALIDITY",
                "range_expectation": {
                    "min_value": "0"
                }
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

    def _setup_automated_access_requests(self, name: str, args: DataProductArgs, opts: ResourceOptions) -> List[Any]:
        """Automatically create access requests for pre-approved service accounts"""
        access_requests = []

        for sa in args.get("preApprovedServiceAccounts", []):
            for group_id in args["accessGroups"].keys():
                request = gcp.cloudrun.Command(
                    f"{name}-access-{sa.replace('@', '-at-').replace('.', '-')}-{group_id}",
                    create=f"""
                    curl -X POST \\
                      -H "Authorization: Bearer $(gcloud auth print-access-token)" \\
                      -H "Content-Type: application/json" \\
                      -d '{{"changeRequest": {{"justification": "Automated service account access via Pulumi", "dataProductAccessRequest": {{"parent": "projects/{args["project"]}/locations/{args["location"]}/dataProducts/{args["dataProductId"]}", "accessGroupId": "{group_id}", "requestedPrincipal": "serviceAccount:{sa}"}}}}}}' \\
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
