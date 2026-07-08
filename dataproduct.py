"""
Dataplex Data Product Component with Standardized Aspects

This module provides a Pulumi ComponentResource for creating Dataplex data products
with mandatory business, compliance, and technical aspects.
"""

import pulumi
from pulumi import ComponentResource, ResourceOptions, Output
import pulumi_gcp as gcp
import json
from datetime import datetime


class CentralizedAspectTypes:
    """Centralized aspect type definitions"""

    # Business Context Aspects (Mandatory)
    BUSINESS_CONTEXT = "projects/{project}/locations/{location}/aspectTypes/business-context"
    DOMAIN_CLASSIFICATION = "projects/{project}/locations/{location}/aspectTypes/domain-classification"

    # Compliance Aspects (Mandatory)
    DATA_CLASSIFICATION = "projects/{project}/locations/{location}/aspectTypes/data-classification"
    COMPLIANCE_POLICY = "projects/{project}/locations/{location}/aspectTypes/compliance-policy"
    RETENTION_POLICY = "projects/{project}/locations/{location}/aspectTypes/retention-policy"

    # System/Technical Aspects (Mandatory)
    OPERATIONAL_METADATA = "projects/{project}/locations/{location}/aspectTypes/operational-metadata"
    TECHNICAL_OWNERSHIP = "projects/{project}/locations/{location}/aspectTypes/technical-ownership"
    SLA_METADATA = "projects/{project}/locations/{location}/aspectTypes/sla-metadata"

    # Optional Aspects
    DATA_LINEAGE = "projects/{project}/locations/{location}/aspectTypes/data-lineage"

    @staticmethod
    def format_aspect_type(aspect_type_template: str, project: str, location: str) -> str:
        """Format aspect type path with project and location"""
        return aspect_type_template.format(project=project, location=location)


class DataProductArgs:
    """Arguments for DataProductWithAspects component"""

    def __init__(self,
                 # Data Product Core Properties (Required)
                 data_product_id: str,
                 location: str,
                 project: str,
                 display_name: str,
                 description: str,
                 access_groups: dict,

                 # Mandatory Business Context Aspects (Required)
                 business_domain: str,
                 business_owner: str,
                 business_purpose: str,

                 # Mandatory Compliance Aspects (Required)
                 data_classification: str,  # e.g., "public", "internal", "confidential", "restricted"
                 retention_justification: str,

                 # Mandatory System/Technical Aspects (Required)
                 technical_owner: str,
                 technical_contact: str,

                 # Optional Business Context
                 glossary_terms: list = None,

                 # Optional Compliance
                 compliance_frameworks: list = None,  # e.g., ["GDPR", "PIPEDA", "SOC2"]
                 contains_pii: bool = False,
                 retention_years: int = 7,

                 # Optional System/Technical
                 sla_tier: str = "standard",  # "critical", "standard", "low"
                 availability_target: str = "99.9%",
                 support_hours: str = "business-hours",

                 # Data Assets
                 bigquery_datasets: list = None,  # List of dataset IDs to attach
                 gcs_buckets: list = None,  # List of bucket names to attach

                 # Data Quality
                 enable_data_quality_scans: bool = False,
                 quality_scan_schedule: str = "0 2 * * *",  # Daily at 2 AM
                 quality_rules: list = None,

                 # Monitoring
                 enable_monitoring: bool = False,
                 alert_email: str = None,

                 # Cost Management
                 cost_center: str = None,
                 enable_cost_tracking: bool = True,

                 # Version Management
                 version: str = "1.0.0",
                 changelog: str = "",

                 # Lineage
                 upstream_data_products: list = None,
                 downstream_data_products: list = None,
                 transformation_jobs: list = None,

                 # Access Automation
                 pre_approved_service_accounts: list = None,

                 # Optional
                 tags: dict = None,
                 additional_aspects: dict = None):

        # Core properties
        self.data_product_id = data_product_id
        self.location = location
        self.project = project
        self.display_name = display_name
        self.description = description
        self.access_groups = access_groups

        # Business context
        self.business_domain = business_domain
        self.business_owner = business_owner
        self.business_purpose = business_purpose
        self.glossary_terms = glossary_terms or []

        # Compliance
        self.data_classification = data_classification
        self.compliance_frameworks = compliance_frameworks or []
        self.contains_pii = contains_pii
        self.retention_years = retention_years
        self.retention_justification = retention_justification

        # System/Technical
        self.technical_owner = technical_owner
        self.technical_contact = technical_contact
        self.sla_tier = sla_tier
        self.availability_target = availability_target
        self.support_hours = support_hours

        # Data assets
        self.bigquery_datasets = bigquery_datasets or []
        self.gcs_buckets = gcs_buckets or []

        # Data quality
        self.enable_data_quality_scans = enable_data_quality_scans
        self.quality_scan_schedule = quality_scan_schedule
        self.quality_rules = quality_rules

        # Monitoring
        self.enable_monitoring = enable_monitoring
        self.alert_email = alert_email

        # Cost management
        self.cost_center = cost_center
        self.enable_cost_tracking = enable_cost_tracking

        # Version management
        self.version = version
        self.changelog = changelog

        # Lineage
        self.upstream_data_products = upstream_data_products or []
        self.downstream_data_products = downstream_data_products or []
        self.transformation_jobs = transformation_jobs or []

        # Access automation
        self.pre_approved_service_accounts = pre_approved_service_accounts or []

        # Optional
        self.tags = tags or {}
        self.additional_aspects = additional_aspects or {}


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

    def __init__(self,
                 name: str,
                 args: DataProductArgs,
                 opts: ResourceOptions = None):

        super().__init__('dataproducts:index:DataProductWithAspects', name, {}, opts)

        child_opts = ResourceOptions(parent=self)

        # Build cost tracking labels
        cost_labels = self._build_cost_labels(args)

        # Create the data product
        self.data_product = gcp.dataplex.DataProduct(
            f"{name}-product",
            data_product_id=args.data_product_id,
            location=args.location,
            project=args.project,
            display_name=args.display_name,
            description=args.description,
            labels={**args.tags, **cost_labels},
            opts=child_opts
        )

        # Apply mandatory aspects
        self.aspects = self._apply_mandatory_aspects(name, args, child_opts)

        # Apply optional lineage aspect
        if args.upstream_data_products or args.downstream_data_products or args.transformation_jobs:
            self.aspects['data-lineage'] = self._create_lineage_aspect(name, args, child_opts)

        # Apply any additional custom aspects
        if args.additional_aspects:
            for aspect_name, aspect_config in args.additional_aspects.items():
                self.aspects[aspect_name] = self._create_aspect(
                    f"{name}-{aspect_name}",
                    aspect_config["aspect_type"],
                    aspect_config["data"],
                    args.project,
                    args.location,
                    child_opts
                )

        # Attach data assets
        self.data_assets = self._attach_data_assets(name, args, child_opts)

        # Set up data quality scans
        self.quality_scans = []
        if args.enable_data_quality_scans:
            self.quality_scans = self._setup_data_quality_scans(name, args, child_opts)

        # Set up monitoring
        self.monitoring = {}
        if args.enable_monitoring:
            self.monitoring = self._setup_monitoring(name, args, child_opts)

        # Create automated access requests for pre-approved service accounts
        self.access_requests = []
        if args.pre_approved_service_accounts:
            self.access_requests = self._setup_automated_access_requests(name, args, child_opts)

        # Store version changelog if provided
        self.changelog_object = None
        if args.changelog:
            self.changelog_object = self._store_changelog(name, args, child_opts)

        self.register_outputs({
            'data_product_id': self.data_product.data_product_id,
            'data_product_name': self.data_product.name,
            'aspects': self.aspects,
            'data_assets': self.data_assets,
            'quality_scans': self.quality_scans,
            'monitoring': self.monitoring,
            'version': args.version
        })

    def _build_cost_labels(self, args: DataProductArgs) -> dict:
        """Build standardized cost tracking labels"""
        if not args.enable_cost_tracking:
            return {}

        return {
            "data-product-id": args.data_product_id.replace("_", "-"),
            "cost-center": (args.cost_center or "unallocated").replace("_", "-"),
            "business-domain": args.business_domain.replace("_", "-"),
            "managed-by": "pulumi",
            "version": args.version.replace(".", "-")
        }

    def _apply_mandatory_aspects(self, name: str, args: DataProductArgs, opts: ResourceOptions) -> dict:
        """Apply all mandatory aspects to the data product"""
        aspects = {}

        # Business Context Aspects
        aspects['business-context'] = self._create_aspect(
            f"{name}-business-context",
            CentralizedAspectTypes.BUSINESS_CONTEXT,
            {
                "business_domain": args.business_domain,
                "business_owner": args.business_owner,
                "business_purpose": args.business_purpose,
                "glossary_terms": args.glossary_terms
            },
            args.project,
            args.location,
            opts
        )

        aspects['domain-classification'] = self._create_aspect(
            f"{name}-domain-classification",
            CentralizedAspectTypes.DOMAIN_CLASSIFICATION,
            {
                "domain": args.business_domain,
                "classification_date": datetime.now().isoformat()
            },
            args.project,
            args.location,
            opts
        )

        # Compliance Aspects
        aspects['data-classification'] = self._create_aspect(
            f"{name}-data-classification",
            CentralizedAspectTypes.DATA_CLASSIFICATION,
            {
                "classification_level": args.data_classification,
                "contains_pii": args.contains_pii,
                "classified_by": args.technical_owner,
                "classification_date": datetime.now().isoformat()
            },
            args.project,
            args.location,
            opts
        )

        aspects['compliance-policy'] = self._create_aspect(
            f"{name}-compliance-policy",
            CentralizedAspectTypes.COMPLIANCE_POLICY,
            {
                "applicable_frameworks": args.compliance_frameworks,
                "contains_pii": args.contains_pii,
                "data_residency": "canada",
                "compliance_contact": args.business_owner
            },
            args.project,
            args.location,
            opts
        )

        aspects['retention-policy'] = self._create_aspect(
            f"{name}-retention-policy",
            CentralizedAspectTypes.RETENTION_POLICY,
            {
                "retention_period_years": args.retention_years,
                "retention_justification": args.retention_justification,
                "deletion_process": "automated",
                "policy_owner": args.business_owner
            },
            args.project,
            args.location,
            opts
        )

        # System/Technical Aspects
        aspects['technical-ownership'] = self._create_aspect(
            f"{name}-technical-ownership",
            CentralizedAspectTypes.TECHNICAL_OWNERSHIP,
            {
                "technical_owner": args.technical_owner,
                "technical_contact": args.technical_contact,
                "support_team": "dse-team@telus.com",
                "oncall_rotation": "pagerduty"
            },
            args.project,
            args.location,
            opts
        )

        aspects['operational-metadata'] = self._create_aspect(
            f"{name}-operational-metadata",
            CentralizedAspectTypes.OPERATIONAL_METADATA,
            {
                "deployment_environment": "production",
                "created_by": "pulumi-automation",
                "managed_by": "infrastructure-team",
                "version": args.version
            },
            args.project,
            args.location,
            opts
        )

        aspects['sla-metadata'] = self._create_aspect(
            f"{name}-sla-metadata",
            CentralizedAspectTypes.SLA_METADATA,
            {
                "sla_tier": args.sla_tier,
                "availability_target": args.availability_target,
                "support_hours": args.support_hours,
                "response_time_target": self._get_response_time(args.sla_tier)
            },
            args.project,
            args.location,
            opts
        )

        return aspects

    def _create_lineage_aspect(self, name: str, args: DataProductArgs, opts: ResourceOptions):
        """Create data lineage aspect"""
        return self._create_aspect(
            f"{name}-lineage",
            CentralizedAspectTypes.DATA_LINEAGE,
            {
                "upstream_sources": args.upstream_data_products,
                "downstream_consumers": args.downstream_data_products,
                "transformation_pipeline": args.transformation_jobs,
                "lineage_updated": datetime.now().isoformat()
            },
            args.project,
            args.location,
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

        for dataset_id in args.bigquery_datasets:
            asset = gcp.dataplex.Asset(
                f"{name}-asset-bq-{dataset_id}",
                lake=f"projects/{args.project}/locations/{args.location}/lakes/default",
                dataplex_zone=f"projects/{args.project}/locations/{args.location}/lakes/default/zones/default",
                location=args.location,
                discovery_spec={
                    "enabled": True,
                    "schedule": "0 */12 * * *"
                },
                resource_spec={
                    "name": f"//bigquery.googleapis.com/projects/{args.project}/datasets/{dataset_id}",
                    "type": "BIGQUERY_DATASET"
                },
                labels=self._build_cost_labels(args),
                opts=opts
            )
            assets.append(asset)

        for bucket_name in args.gcs_buckets:
            asset = gcp.dataplex.Asset(
                f"{name}-asset-gcs-{bucket_name}",
                lake=f"projects/{args.project}/locations/{args.location}/lakes/default",
                dataplex_zone=f"projects/{args.project}/locations/{args.location}/lakes/default/zones/default",
                location=args.location,
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

        for dataset_id in args.bigquery_datasets:
            scan = gcp.dataplex.Datascan(
                f"{name}-dq-{dataset_id}",
                data_scan_id=f"{args.data_product_id}-dq-{dataset_id}",
                location=args.location,
                project=args.project,
                data={
                    "resource": f"//bigquery.googleapis.com/projects/{args.project}/datasets/{dataset_id}"
                },
                execution_spec={
                    "trigger": {
                        "schedule": {
                            "cron": args.quality_scan_schedule
                        }
                    }
                },
                data_quality_spec={
                    "rules": args.quality_rules or self._default_quality_rules()
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

        if args.alert_email:
            notification_channel = gcp.monitoring.NotificationChannel(
                f"{name}-email-channel",
                type="email",
                labels={
                    "email_address": args.alert_email
                },
                display_name=f"{args.display_name} Alerts",
                opts=opts
            )

            monitoring['notification_channel'] = notification_channel

        return monitoring

    def _setup_automated_access_requests(self, name: str, args: DataProductArgs, opts: ResourceOptions) -> list:
        """Automatically create access requests for pre-approved service accounts"""
        access_requests = []

        for sa in args.pre_approved_service_accounts:
            for group_id in args.access_groups.keys():
                request = gcp.cloudrun.Command(
                    f"{name}-access-{sa.replace('@', '-at-').replace('.', '-')}-{group_id}",
                    create=f"""
                    curl -X POST \\
                      -H "Authorization: Bearer $(gcloud auth print-access-token)" \\
                      -H "Content-Type: application/json" \\
                      -d '{{"changeRequest": {{"justification": "Automated service account access via Pulumi", "dataProductAccessRequest": {{"parent": "projects/{args.project}/locations/{args.location}/dataProducts/{args.data_product_id}", "accessGroupId": "{group_id}", "requestedPrincipal": "serviceAccount:{sa}"}}}}}}' \\
                      "https://dataplex.googleapis.com/v1/projects/{args.project}/locations/{args.location}/dataProducts/{args.data_product_id}:requestAccess"
                    """,
                    opts=ResourceOptions(parent=self, depends_on=[self.data_product])
                )
                access_requests.append(request)

        return access_requests

    def _store_changelog(self, name: str, args: DataProductArgs, opts: ResourceOptions):
        """Store version changelog in GCS"""
        return gcp.storage.BucketObject(
            f"{name}-changelog",
            bucket=f"{args.project}-dataplex-changelogs",
            name=f"{args.data_product_id}/v{args.version}/CHANGELOG.md",
            content=args.changelog,
            opts=opts
        )

    def _get_response_time(self, sla_tier: str) -> str:
        """Get response time based on SLA tier"""
        response_times = {
            "critical": "15 minutes",
            "standard": "4 hours",
            "low": "24 hours"
        }
        return response_times.get(sla_tier, "4 hours")
