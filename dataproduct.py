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


class CentralizedAspectTypes:
    """Centralized aspect type definitions"""

    # Business Context Aspects (Mandatory)
    BUSINESS_CONTEXT = defaults.ASPECT_TYPE_BUSINESS_CONTEXT
    DOMAIN_CLASSIFICATION = defaults.ASPECT_TYPE_DOMAIN_CLASSIFICATION

    # Compliance Aspects (Mandatory)
    DATA_CLASSIFICATION = defaults.ASPECT_TYPE_DATA_CLASSIFICATION
    COMPLIANCE_POLICY = defaults.ASPECT_TYPE_COMPLIANCE_POLICY
    RETENTION_POLICY = defaults.ASPECT_TYPE_RETENTION_POLICY

    # System/Technical Aspects (Mandatory)
    OPERATIONAL_METADATA = defaults.ASPECT_TYPE_OPERATIONAL_METADATA
    TECHNICAL_OWNERSHIP = defaults.ASPECT_TYPE_TECHNICAL_OWNERSHIP
    SLA_METADATA = defaults.ASPECT_TYPE_SLA_METADATA

    # Optional Aspects
    DATA_LINEAGE = defaults.ASPECT_TYPE_DATA_LINEAGE

    @staticmethod
    def format_aspect_type(aspect_type_template: str, project: str, location: str) -> str:
        """Format aspect type path with project and location"""
        return aspect_type_template.format(project=project, location=location)


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

    def _create_data_product_entry(self, name: str, args: DataProductArgs, opts: ResourceOptions):
        """
        Create an Entry resource to attach aspects to the DataProduct.
        Based on the pattern from: https://github.com/telus/bi-syrax/blob/feat-dataplex-poc/stacks/data_products/Pulumi.yaml
        """
        # Build aspect data for the 3 AspectTypes we created

        # Business Context Aspect Data
        business_aspect_data = {
            "business_domain": args["businessDomain"],
            "business_owner": args["businessOwner"],
            "business_purpose": args["businessPurpose"],
            "glossary_terms": args.get("glossaryTerms", [])
        }

        # Data Classification Aspect Data
        from datetime import datetime
        classification_aspect_data = {
            "classification_level": args["dataClassification"],
            "contains_pii": args.get("containsPii", defaults.DEFAULT_CONTAINS_PII),
            "classified_by": args.get("classifiedBy", args["technicalOwner"]),
            "classification_date": args.get("classificationDate", datetime.now().strftime("%Y-%m-%d"))
        }

        # Technical Ownership Aspect Data
        ownership_aspect_data = {
            "technical_owner": args["technicalOwner"],
            "technical_contact": args["technicalContact"],
            "support_team": args.get("supportTeam", args["technicalContact"]),
            "oncall_rotation": args.get("oncallRotation", "N/A")
        }

        pulumi.log.info(
            f"[{name}] Creating Entry resource with 3 aspects. "
            f"Business domain: {args['businessDomain']}, Classification: {args['dataClassification']}"
        )

        # Get project number for entry_type and aspect_key (required format)
        project_data = gcp.organizations.get_project(project_id=args["project"])

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
            entry_id=f"projects/{project_data.number}/locations/{args['location']}/dataProducts/{args['dataProductId']}",
            location=args["location"],
            project=project_data.number,
            entry_type=f"projects/{project_data.number}/locations/{args['location']}/entryTypes/table",
            fully_qualified_name=self.data_product.name.apply(
                lambda n: f"dataplex:{args['project']}.{args['location']}.{args['dataProductId']}"
            ),
            aspects=[
                {
                    "aspect_key": f"{project_data.number}.{args['location']}.business-context",
                    "aspect": {
                        "data": json.dumps(business_aspect_data)
                    }
                },
                {
                    "aspect_key": f"{project_data.number}.{args['location']}.data-classification",
                    "aspect": {
                        "data": json.dumps(classification_aspect_data)
                    }
                },
                {
                    "aspect_key": f"{project_data.number}.{args['location']}.technical-ownership",
                    "aspect": {
                        "data": json.dumps(ownership_aspect_data)
                    }
                }
            ],
            opts=entry_opts
        )
        return entry

    def _build_cost_labels(self, args: DataProductArgs) -> dict:
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

    def _apply_mandatory_aspects(self, name: str, args: DataProductArgs, opts: ResourceOptions) -> dict:
        """Apply mandatory aspects to the data product (only the 3 that exist)"""
        aspects = {}

        # Business Context Aspect
        aspects['business-context'] = self._create_aspect(
            f"{name}-business-context",
            CentralizedAspectTypes.BUSINESS_CONTEXT,
            {
                "business_domain": args["businessDomain"],
                "business_owner": args["businessOwner"],
                "business_purpose": args["businessPurpose"]
            },
            args["project"],
            args["location"],
            opts
        )

        # Data Classification Aspect
        aspects['data-classification'] = self._create_aspect(
            f"{name}-data-classification",
            CentralizedAspectTypes.DATA_CLASSIFICATION,
            {
                "classification_level": args["dataClassification"],
                "contains_pii": args.get("containsPii", defaults.DEFAULT_CONTAINS_PII)
            },
            args["project"],
            args["location"],
            opts
        )

        # Technical Ownership Aspect
        aspects['technical-ownership'] = self._create_aspect(
            f"{name}-technical-ownership",
            CentralizedAspectTypes.TECHNICAL_OWNERSHIP,
            {
                "technical_owner": args["technicalOwner"],
                "technical_contact": args["technicalContact"]
            },
            args["project"],
            args["location"],
            opts
        )

        return aspects

    def _create_lineage_aspect(self, name: str, args: DataProductArgs, opts: ResourceOptions):
        """Create data lineage aspect"""
        return self._create_aspect(
            f"{name}-lineage",
            CentralizedAspectTypes.DATA_LINEAGE,
            {
                "upstream_sources": args.get("upstreamDataProducts", []),
                "downstream_consumers": args.get("downstreamDataProducts", []),
                "transformation_pipeline": args.get("transformationJobs", []),
                "lineage_updated": datetime.now().isoformat()
            },
            args["project"],
            args["location"],
            opts
        )

    def _create_aspect(self,
                      name: str,
                      aspect_type_template: str,
                      data: dict,
                      project: str,
                      location: str,
                      opts: ResourceOptions):
        """Helper to create an aspect using REST API"""

        aspect_type = CentralizedAspectTypes.format_aspect_type(aspect_type_template, project, location)

        # Using Command resource since Pulumi GCP doesn't fully support aspects on data products yet
        return gcp.cloudrun.Command(
            name,
            create=Output.all(
                self.data_product.name,
                aspect_type,
                data
            ).apply(lambda args: self._build_update_command(args[0], args[1], args[2])),
            delete=f"echo 'Aspect {name} removed with data product'",
            opts=opts
        )

    def _build_update_command(self, product_name: str, aspect_type: str, data: dict) -> str:
        """Build command to attach aspect to data product entry"""
        data_json = json.dumps(data).replace('"', '\\"')

        return f"""
        curl -X PATCH \\
          "https://dataplex.googleapis.com/v1/{product_name}?updateMask=aspects" \\
          -H "Authorization: Bearer $(gcloud auth print-access-token)" \\
          -H "Content-Type: application/json" \\
          -d '{{"aspects": {{"{aspect_type}": {{"aspectType": "{aspect_type}", "data": {data_json}}}}}}}'
        """

    def _attach_data_assets(self, name: str, args: DataProductArgs, opts: ResourceOptions) -> list:
        """Attach BigQuery datasets and GCS buckets as data assets"""
        assets = []

        for dataset_id in args.get("bigqueryDatasets", []):
            asset = gcp.dataplex.Asset(
                f"{name}-asset-bq-{dataset_id}",
                lake=f"projects/{args["project"]}/locations/{args["location"]}/lakes/default",
                dataplex_zone=f"projects/{args["project"]}/locations/{args["location"]}/lakes/default/zones/default",
                location=args["location"],
                discovery_spec={
                    "enabled": True,
                    "schedule": "0 */12 * * *"
                },
                resource_spec={
                    "name": f"//bigquery.googleapis.com/projects/{args["project"]}/datasets/{dataset_id}",
                    "type": "BIGQUERY_DATASET"
                },
                labels=self._build_cost_labels(args),
                opts=opts
            )
            assets.append(asset)

        for bucket_name in args.get("gcsBuckets", []):
            asset = gcp.dataplex.Asset(
                f"{name}-asset-gcs-{bucket_name}",
                lake=f"projects/{args["project"]}/locations/{args["location"]}/lakes/default",
                dataplex_zone=f"projects/{args["project"]}/locations/{args["location"]}/lakes/default/zones/default",
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

    def _setup_data_quality_scans(self, name: str, args: DataProductArgs, opts: ResourceOptions) -> list:
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

    def _default_quality_rules(self) -> list:
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

    def _setup_monitoring(self, name: str, args: DataProductArgs, opts: ResourceOptions) -> dict:
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

    def _setup_automated_access_requests(self, name: str, args: DataProductArgs, opts: ResourceOptions) -> list:
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
