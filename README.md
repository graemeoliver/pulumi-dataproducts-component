# Pulumi Component: GCP Dataplex Data Products

**Version**: v0.0.23

A Pulumi component that creates standardized Dataplex data products with automated governance, Cloud Scheduler integration, and data quality management for Google Cloud Platform.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [What's New in v0.0.23](#-whats-new-in-v0023)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Component Features](#-component-features)
- [Usage Examples](#-usage-examples)
- [Configuration Reference](#-configuration-reference)
- [Setup Instructions](#-setup-instructions)
- [Adding Custom Aspect Types](#-adding-custom-aspect-types)
- [Cloud Scheduler Integration](#-cloud-scheduler-integration)
- [Architecture](#-architecture)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [Support](#-support)

---

## 🎯 Overview

The **DataProductWithAspects** component automates the creation and management of GCP Dataplex data products with:

✅ **Standardized Metadata** - Consistent business, compliance, and technical aspects
✅ **Cloud Scheduler Integration** - Automated quality scans with smart staging controls
✅ **Auto-Pause for Staging** - Prevents accidental costs in non-production environments
✅ **Data Quality Scans** - Automated checks with configurable retry policies
✅ **Cost Tracking** - Built-in labels for cost attribution
✅ **Extensible Aspect Registry** - Easy to add custom governance metadata

### Key Benefits

- **Time Savings**: 5 minutes to deploy vs. 2-4 hours of manual setup
- **Consistency**: Same standards across all data products
- **Governance**: Required metadata enforced automatically
- **Cost Control**: Auto-pause in staging, detailed cost labels
- **Quality**: Automated quality checks on schedule

---

## 🆕 What's New in v0.0.23

### Cloud Scheduler Integration
- **Centralized Scheduling**: All scans managed via Cloud Scheduler (not internal Dataplex scheduling)
- **Better Monitoring**: Comprehensive audit trail in Cloud Logging
- **Configurable Retries**: Exponential backoff with customizable parameters
- **OAuth Authentication**: Secure service account-based triggering

### Auto-Pause for Staging
- **Smart Detection**: Automatically pauses scheduler jobs for projects starting with `bi-stg`
- **Cost Savings**: Prevents accidental execution in staging environments
- **Override Capability**: Optional `schedulerPaused` parameter for explicit control

### Code Improvements
- **Aspect Registry System**: Centralized configuration for all aspect types
- **Helper Methods**: Cleaner, more maintainable code (49% reduction in main scheduler method)
- **Python Dataclasses**: Modern, Pythonic patterns

See [CHANGELOG-v0.0.23.md](CHANGELOG-v0.0.23.md) for complete details.

---

## 📋 Prerequisites

### Required
- **Pulumi CLI**: Version 3.0.0 or higher
- **Python**: Version 3.8 or higher (3.9+ recommended)
- **GCP Project**: With Dataplex API enabled
- **Service Account**: With `roles/dataplex.admin` and `roles/dataplex.datascans.runner`
- **Aspect Types**: Pre-created in Dataplex (see [Setup Instructions](#-setup-instructions))

### Optional
- **Cloud Scheduler API**: Enabled for automated scan scheduling
- **BigQuery API**: For dataset asset attachment
- **Cloud Storage API**: For bucket asset attachment

---

## 🚀 Quick Start

### 1. Install the Component

```yaml
# Pulumi.yaml
name: my-data-products
runtime: yaml

packages:
  dataproducts: github.com/graemeoliver/pulumi-dataproducts-component@v0.0.23
```

### 2. Create a Data Product

```yaml
resources:
  salesProduct:
    type: dataproducts:index:DataProductWithAspects
    properties:
      # Core Properties (Required)
      dataProductId: sales-analytics
      project: my-gcp-project
      location: northamerica-northeast1
      displayName: Sales Analytics
      description: Monthly sales data for reporting

      # Access Groups (Required)
      accessGroups:
        bi-admins:
          id: bi-admins
          displayName: BI Admins
          principal:
            googleGroup: bi-admins@company.com

      # Business Context (Required)
      businessDomain: Finance
      businessOwner: jane.smith@company.com
      businessPurpose: Monthly sales reporting and analysis

      # Compliance (Required)
      dataClassification: internal
      retentionJustification: Business reporting requirements

      # Technical (Required)
      technicalOwner: data-team@company.com
      technicalContact: platform-oncall@company.com

      # Optional: Data Quality
      enableDataQualityScans: true
      qualityScanSchedule: "0 2 * * *"  # 2 AM daily
      bigqueryDatasets:
        - sales_monthly
```

### 3. Deploy

```bash
pulumi up
```

---

## 🎨 Component Features

### Aspect Registry System

The component uses a centralized registry to manage all metadata aspects:

**Currently Registered Aspects** ([dataproduct.py:53-70](dataproduct.py#L53-L70)):
1. **Business Context** - Domain, owner, purpose, glossary terms
2. **Data Classification** - Sensitivity level and PII flag
3. **Technical Ownership** - Technical contacts and support info

All aspects are automatically attached to every data product.

### Cloud Scheduler Features

**Scheduler Jobs** ([dataproduct.py:560-601](dataproduct.py#L560-L601)):
- HTTP POST triggers to Dataplex API
- OAuth authentication with service accounts
- Configurable retry policies (3 retries, exponential backoff)
- Smart auto-pause for staging projects

**Auto-Pause Logic** ([dataproduct.py:434-465](dataproduct.py#L434-L465)):
1. If `schedulerPaused` explicitly set → use that value
2. Else if project starts with `bi-stg` → auto-pause
3. Else → enabled

### Data Quality Scans

**Automated Quality Checks**:
- Runs on configurable schedule
- Supports custom quality rules
- Integration with Cloud Scheduler
- Automatic retry on failure

### Cost Management

**Automatic Labels**:
- Data product ID
- Cost center
- Business domain
- Managed by Pulumi
- Version

---

## 💡 Usage Examples

### Example 1: Production Data Product (Default)

```yaml
resources:
  productionProduct:
    type: dataproducts:index:DataProductWithAspects
    properties:
      dataProductId: customer-analytics
      project: prod-analytics-123
      location: northamerica-northeast1
      displayName: Customer Analytics
      description: Customer behavior and segmentation data

      accessGroups:
        analytics-team:
          id: analytics-team
          displayName: Analytics Team
          principal:
            googleGroup: analytics@company.com

      businessDomain: Marketing
      businessOwner: marketing-lead@company.com
      businessPurpose: Customer segmentation and targeting
      glossaryTerms:
        - customer-lifetime-value
        - customer-segment

      dataClassification: confidential
      containsPii: true
      complianceFrameworks:
        - GDPR
        - PIPEDA
      retentionYears: 3
      retentionJustification: GDPR compliance requirement

      technicalOwner: data-platform@company.com
      technicalContact: platform-oncall@company.com
      slaTier: critical
      availabilityTarget: "99.9%"
      supportHours: "24x7"

      # Data Quality with Cloud Scheduler
      enableDataQualityScans: true
      qualityScanSchedule: "0 2 * * *"  # 2 AM daily
      bigqueryDatasets:
        - customer_analytics
        - customer_segments

      # Cost Tracking
      costCenter: marketing-ops
      version: "1.2.0"

outputs:
  productId: ${productionProduct.dataProductId}
  schedulerJobs: ${productionProduct.schedulerJobs}
```

**Result**: Scheduler jobs created in **ENABLED** state, scans run daily at 2 AM.

---

### Example 2: Staging Environment (Auto-Pause)

```yaml
resources:
  stagingProduct:
    type: dataproducts:index:DataProductWithAspects
    properties:
      dataProductId: staging-product
      project: bi-stg-analytics  # Project starts with bi-stg
      location: northamerica-northeast1
      displayName: Staging Product
      description: Test environment data product

      accessGroups:
        dev-team:
          id: dev-team
          displayName: Dev Team
          principal:
            googleGroup: developers@company.com

      businessDomain: Engineering
      businessOwner: dev-lead@company.com
      businessPurpose: Testing and development

      dataClassification: internal
      retentionJustification: Development lifecycle

      technicalOwner: dev-team@company.com
      technicalContact: dev-oncall@company.com

      enableDataQualityScans: true
      qualityScanSchedule: "0 2 * * *"
      bigqueryDatasets:
        - staging_dataset
```

**Result**: Scheduler jobs created in **PAUSED** state automatically (prevents accidental costs).

**To manually trigger**:
```bash
gcloud scheduler jobs run staging-product-dq-staging_dataset-scheduler \
    --location=northamerica-northeast1
```

---

### Example 3: Staging with Explicit Override

```yaml
resources:
  stagingProduct:
    type: dataproducts:index:DataProductWithAspects
    properties:
      dataProductId: staging-product-active
      project: bi-stg-test
      # ... other required fields ...

      enableDataQualityScans: true
      qualityScanSchedule: "0 3 * * *"

      # Override auto-pause (enable scheduler jobs)
      schedulerPaused: false

      bigqueryDatasets:
        - test_dataset
```

**Result**: Jobs created in **ENABLED** state despite `bi-stg` prefix.

---

### Example 4: Custom Scheduler Configuration

```yaml
resources:
  customProduct:
    type: dataproducts:index:DataProductWithAspects
    properties:
      # ... required fields ...

      enableDataQualityScans: true
      qualityScanSchedule: "0 */6 * * *"  # Every 6 hours

      # Cloud Scheduler Configuration
      schedulerTimeZone: "America/New_York"
      schedulerRetryCount: 5
      schedulerMaxRetryDuration: "600s"
      schedulerMinBackoffDuration: "10s"
      schedulerMaxBackoffDuration: "1800s"
      schedulerServiceAccount: "custom-scheduler@project.iam.gserviceaccount.com"

      bigqueryDatasets:
        - critical_dataset
```

---

### Example 5: Opt-Out of Cloud Scheduler (Legacy)

```yaml
resources:
  legacyProduct:
    type: dataproducts:index:DataProductWithAspects
    properties:
      # ... required fields ...

      enableDataQualityScans: true
      qualityScanSchedule: "0 2 * * *"

      # Use internal Dataplex scheduling instead of Cloud Scheduler
      useCloudSchedulerForScans: false

      bigqueryDatasets:
        - legacy_dataset
```

**Note**: Internal scheduling is legacy mode. Cloud Scheduler is recommended.

---

## 📖 Configuration Reference

### Complete Parameter List

#### **Core Properties** (Required)

| Parameter | Type | Description |
|-----------|------|-------------|
| `dataProductId` | `string` | Unique identifier for the data product (lowercase, hyphens only) |
| `project` | `string` | GCP project ID |
| `location` | `string` | GCP region (e.g., `northamerica-northeast1`) |
| `displayName` | `string` | Human-readable name for the data product |
| `description` | `string` | Detailed description of the data product |
| `accessGroups` | `map` | Access control groups (see Access Groups section) |

#### **Business Context** (Required)

| Parameter | Type | Description |
|-----------|------|-------------|
| `businessDomain` | `string` | Business domain (Finance, Marketing, Engineering, etc.) |
| `businessOwner` | `string` | Business owner email address |
| `businessPurpose` | `string` | Statement describing the business purpose |

#### **Compliance** (Required)

| Parameter | Type | Description |
|-----------|------|-------------|
| `dataClassification` | `string` | Classification level: `public`, `internal`, `confidential`, or `restricted` |
| `retentionJustification` | `string` | Justification for the data retention period |

#### **Technical Ownership** (Required)

| Parameter | Type | Description |
|-----------|------|-------------|
| `technicalOwner` | `string` | Technical owner email address |
| `technicalContact` | `string` | Technical contact email for support issues |

---

#### **Business Context** (Optional)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `glossaryTerms` | `list[string]` | `[]` | List of business glossary terms |

#### **Compliance** (Optional)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `complianceFrameworks` | `list[string]` | `[]` | Compliance frameworks (GDPR, SOX, PIPEDA, PCI-DSS, etc.) |
| `containsPii` | `bool` | `false` | Whether data contains personally identifiable information |
| `retentionYears` | `int` | `7` | Data retention period in years |

#### **Technical/SLA** (Optional)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `slaTier` | `string` | `"standard"` | SLA tier: `critical`, `standard`, or `low` |
| `availabilityTarget` | `string` | `"99.9%"` | Availability target percentage |
| `supportHours` | `string` | `"business-hours"` | Support hours (e.g., `24x7`, `business-hours`) |

#### **Data Assets** (Optional)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bigqueryDatasets` | `list[string]` | `[]` | BigQuery dataset IDs to attach as assets |
| `gcsBuckets` | `list[string]` | `[]` | GCS bucket names to attach as assets |

#### **Data Quality** (Optional)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enableDataQualityScans` | `bool` | `false` | Enable automated data quality scans |
| `qualityScanSchedule` | `string` | `"0 2 * * *"` | Cron schedule for quality scans (default: 2 AM daily) |
| `qualityRules` | `list[dict]` | `[]` | Custom data quality rules configuration |

#### **Cloud Scheduler** (Optional)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `useCloudSchedulerForScans` | `bool` | `true` | Use Cloud Scheduler instead of internal Dataplex scheduling |
| `schedulerTimeZone` | `string` | `"America/Toronto"` | IANA time zone for scheduler jobs |
| `schedulerServiceAccount` | `string` | `<compute-sa>` | Service account email for scheduler (default: compute SA) |
| `schedulerPaused` | `bool` | `auto` | Explicitly pause/enable jobs (default: auto-pause for `bi-stg*` projects) |
| `schedulerRetryCount` | `int` | `3` | Number of retry attempts for failed jobs |
| `schedulerMaxRetryDuration` | `string` | `"300s"` | Maximum total duration for retries |
| `schedulerMinBackoffDuration` | `string` | `"5s"` | Minimum backoff duration between retries |
| `schedulerMaxBackoffDuration` | `string` | `"3600s"` | Maximum backoff duration between retries |
| `schedulerMaxDoublings` | `int` | `5` | Maximum number of times to double the backoff |

#### **Monitoring** (Optional)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enableMonitoring` | `bool` | `false` | Enable monitoring and alerting |
| `alertEmail` | `string` | `null` | Email address for alert notifications |

#### **Cost Management** (Optional)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `costCenter` | `string` | `"unallocated"` | Cost center identifier for billing |
| `enableCostTracking` | `bool` | `true` | Enable cost tracking labels |

#### **Version Management** (Optional)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `version` | `string` | `"1.0.0"` | Version number for the data product |
| `changelog` | `string` | `""` | Changelog description |

#### **Data Lineage** (Optional)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `upstreamDataProducts` | `list[string]` | `[]` | List of upstream data product IDs |
| `downstreamDataProducts` | `list[string]` | `[]` | List of downstream data product IDs |
| `transformationJobs` | `list[string]` | `[]` | List of transformation job IDs |

#### **Access Automation** (Optional)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `preApprovedServiceAccounts` | `list[string]` | `[]` | Service accounts pre-approved for access |

#### **Other** (Optional)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ownerEmails` | `list[string]` | `[businessOwner, technicalOwner]` | List of owner email addresses |
| `lakeName` | `string` | `"default"` | Dataplex lake name |
| `zoneName` | `string` | `"default"` | Dataplex zone name |
| `tags` | `map[string]` | `{}` | Additional resource tags |
| `additionalAspects` | `map` | `{}` | Additional custom aspects (advanced) |

---

### Component Outputs

| Output | Type | Description |
|--------|------|-------------|
| `dataProductName` | `string` | Full GCP resource name of the data product |
| `dataProductId` | `string` | Data product ID |
| `aspectsApplied` | `int` | Number of aspects successfully applied |
| `schedulerJobs` | `list[Job]` | List of Cloud Scheduler jobs created |

---

## 🔧 Setup Instructions

### Step 1: Enable GCP APIs

```bash
gcloud services enable dataplex.googleapis.com \
    cloudscheduler.googleapis.com \
    bigquery.googleapis.com \
    storage.googleapis.com \
    --project=YOUR_PROJECT_ID
```

### Step 2: Create Aspect Types

The component requires three aspect types to be pre-created in Dataplex. Use the `dataproducts-aspect-types` stack or create manually:

**Automated Setup** (Recommended):
```bash
# Clone the aspect types stack
cd dataproducts-aspect-types
pulumi up
```

**Manual Setup**:
See the aspect registry in [dataproduct.py:53-70](dataproduct.py#L53-L70) for the three required aspect types:
1. `business-context`
2. `data-classification`
3. `technical-ownership`

### Step 3: Setup Cloud Scheduler IAM

Run the IAM setup script to grant the necessary permissions:

```bash
cd dataproducts-component
./scripts/setup-cloud-scheduler-iam.sh YOUR_PROJECT_ID

# Or with custom service account
./scripts/setup-cloud-scheduler-iam.sh YOUR_PROJECT_ID custom-sa@project.iam.gserviceaccount.com
```

This grants `roles/dataplex.datascans.runner` to the service account.

See [scripts/README.md](scripts/README.md) for detailed documentation.

### Step 4: Install Component

```yaml
# Pulumi.yaml
packages:
  dataproducts: github.com/graemeoliver/pulumi-dataproducts-component@v0.0.23
```

### Step 5: Deploy

```bash
pulumi preview  # Review changes
pulumi up       # Deploy
```

---

## 🎨 Adding Custom Aspect Types

The component uses a centralized **Aspect Registry** system to manage metadata aspects. Adding a new aspect type is straightforward:

### Step 1: Create the AspectType in GCP

First, create the AspectType resource in Dataplex (usually via the `dataproducts-aspect-types` stack):

```yaml
# In dataproducts-aspect-types stack
resources:
  myCustomAspect:
    type: gcp:dataplex:AspectType
    properties:
      aspectTypeId: my-custom-aspect
      project: ${project}
      location: ${location}
      displayName: My Custom Aspect
      description: Custom metadata for my use case
      metadataTemplate:
        name: my-custom-aspect
        type: record
        recordFields:
          - name: custom_field_1
            type: string
          - name: custom_field_2
            type: integer
```

Deploy the aspect type:
```bash
cd dataproducts-aspect-types
pulumi up
```

### Step 2: Add to Aspect Registry

Open [dataproduct.py](dataproduct.py) and add your aspect to the `ASPECT_REGISTRY` (lines 53-70):

```python
ASPECT_REGISTRY = [
    AspectConfig(
        aspect_type_id="business-context",
        builder_method="_build_business_context_aspect_data",
        description="Business domain, owner, purpose, and glossary terms"
    ),
    AspectConfig(
        aspect_type_id="data-classification",
        builder_method="_build_data_classification_aspect_data",
        description="Data sensitivity classification and PII flag"
    ),
    AspectConfig(
        aspect_type_id="technical-ownership",
        builder_method="_build_technical_ownership_aspect_data",
        description="Technical owner and contact information"
    ),
    # Add your new aspect here
    AspectConfig(
        aspect_type_id="my-custom-aspect",
        builder_method="_build_my_custom_aspect_data",
        description="Custom metadata for my use case"
    ),
]
```

### Step 3: Create Builder Method

Add the builder method referenced in the registry:

```python
def _build_my_custom_aspect_data(self, args: DataProductArgs) -> Dict[str, Any]:
    """
    Build data for my-custom-aspect.

    Returns:
        Dictionary with aspect data matching the AspectType schema
    """
    return {
        "custom_field_1": args.get("customField1", "default-value"),
        "custom_field_2": args.get("customField2", 0),
    }
```

### Step 4: Add Parameters to DataProductArgs (Optional)

If your aspect needs user-provided data, add parameters to `DataProductArgs` (lines 73-209):

```python
class DataProductArgs(TypedDict):
    # ... existing parameters ...

    # My Custom Aspect
    customField1: NotRequired[Input[str]]
    """Description of custom field 1"""
    customField2: NotRequired[Input[int]]
    """Description of custom field 2"""
```

### Step 5: Test

Create a test data product with your new aspect:

```yaml
resources:
  testProduct:
    type: dataproducts:index:DataProductWithAspects
    properties:
      # ... required fields ...

      # Your custom fields
      customField1: "test-value"
      customField2: 42
```

Deploy and verify:
```bash
pulumi up
```

### Example: Adding a "Data Sensitivity" Aspect

**1. Create AspectType** (in aspect-types stack):
```yaml
dataSensitivity:
  type: gcp:dataplex:AspectType
  properties:
    aspectTypeId: data-sensitivity
    project: ${project}
    location: ${location}
    metadataTemplate:
      name: data-sensitivity
      type: record
      recordFields:
        - name: sensitivity_level
          type: string
        - name: encryption_required
          type: boolean
```

**2. Add to Registry**:
```python
AspectConfig(
    aspect_type_id="data-sensitivity",
    builder_method="_build_data_sensitivity_aspect_data",
    description="Data sensitivity level and encryption requirements"
),
```

**3. Create Builder**:
```python
def _build_data_sensitivity_aspect_data(self, args: DataProductArgs) -> Dict[str, Any]:
    """Build data for data-sensitivity aspect"""
    return {
        "sensitivity_level": args.get("sensitivityLevel", "medium"),
        "encryption_required": args.get("encryptionRequired", True),
    }
```

**4. Add Parameters**:
```python
sensitivityLevel: NotRequired[Input[str]]
"""Sensitivity level: low, medium, high, critical"""
encryptionRequired: NotRequired[Input[bool]]
"""Whether encryption is required for this data"""
```

**That's it!** Your new aspect will be automatically applied to all data products.

---

## ☁️ Cloud Scheduler Integration

### Architecture

```
Cloud Scheduler Job → HTTP POST → Dataplex API → Trigger Datascan (on-demand)
        ↓                              ↓
  Cloud Logging               Dataplex Logging + Monitoring
```

### Features

**OAuth Authentication**: Service account-based authentication (no API keys)
**Retry Policies**: Configurable exponential backoff (default: 3 retries)
**Auto-Pause**: Smart detection of staging environments
**Centralized Management**: All jobs visible in Cloud Scheduler console

### Setup

See [Step 3: Setup Cloud Scheduler IAM](#step-3-setup-cloud-scheduler-iam) above.

### Monitoring

**View Scheduler Jobs**:
```bash
gcloud scheduler jobs list --location=northamerica-northeast1
```

**View Job Logs**:
```bash
gcloud scheduler jobs describe JOB_NAME --location=northamerica-northeast1
gcloud logging read "resource.type=cloud_scheduler_job"
```

**Manual Trigger**:
```bash
gcloud scheduler jobs run JOB_NAME --location=northamerica-northeast1
```

**Pause/Resume**:
```bash
# Pause
gcloud scheduler jobs pause JOB_NAME --location=northamerica-northeast1

# Resume
gcloud scheduler jobs resume JOB_NAME --location=northamerica-northeast1
```

See [CLOUD-SCHEDULER-IMPLEMENTATION.md](CLOUD-SCHEDULER-IMPLEMENTATION.md) for complete documentation.

---

## 🏗️ Architecture

### Component Structure

```
DataProductWithAspects Component
├── Data Product Resource (GCP Dataplex)
├── Aspects (Attached via Entry Resources)
│   ├── Business Context
│   ├── Data Classification
│   └── Technical Ownership
├── Data Assets (Optional)
│   ├── BigQuery Datasets
│   └── GCS Buckets
├── Data Quality Scans (Optional)
│   └── On-demand Datascans
└── Cloud Scheduler Jobs (Optional)
    └── HTTP POST triggers for scans
```

### Aspect Registry System

```python
ASPECT_REGISTRY = [
    AspectConfig(
        aspect_type_id="business-context",
        builder_method="_build_business_context_aspect_data",
        description="Business domain, owner, purpose, and glossary terms"
    ),
    # ... more aspects ...
]
```

All aspects in the registry are automatically:
1. Built using their builder method
2. Attached to the data product Entry
3. Validated against their AspectType schema

### File Structure

```
dataproducts-component/
├── dataproduct.py              # Main component implementation
├── defaults.py                 # Default values and constants
├── scripts/
│   ├── setup-cloud-scheduler-iam.sh   # IAM setup script
│   └── README.md                      # Scripts documentation
├── tests/                      # Component tests
├── CHANGELOG-v0.0.23.md       # Version changelog
├── CLOUD-SCHEDULER-IMPLEMENTATION.md  # Scheduler docs
├── AUTO-PAUSE-FEATURE.md      # Auto-pause docs
├── COMPONENT-OVERVIEW.md      # Plain language guide
└── README.md                  # This file
```

---

## 🧪 Testing

### Run Component Tests

```bash
cd dataproducts-component
python tests/test_aspect_registry.py
python tests/test_validation.py
```

### Test in Staging

```yaml
# Deploy to staging project (auto-paused)
resources:
  testProduct:
    type: dataproducts:index:DataProductWithAspects
    properties:
      dataProductId: test-product
      project: bi-stg-test  # Starts with bi-stg
      # ... other fields ...
```

```bash
pulumi up

# Verify job is paused
gcloud scheduler jobs describe test-product-dq-dataset-scheduler \
    --location=northamerica-northeast1 | grep state
# Expected: state: PAUSED

# Manually trigger for testing
gcloud scheduler jobs run test-product-dq-dataset-scheduler \
    --location=northamerica-northeast1
```

---

## 🔍 Troubleshooting

### Common Issues

**Issue**: "Permission denied" when creating scheduler jobs

**Solution**: Run the IAM setup script:
```bash
./scripts/setup-cloud-scheduler-iam.sh YOUR_PROJECT_ID
```

---

**Issue**: Scheduler jobs are paused in production

**Solution**: Check if project ID starts with `bi-stg`. If not intended for staging, explicitly set:
```yaml
schedulerPaused: false
```

---

**Issue**: AspectType not found

**Solution**: Ensure aspect types are created in Dataplex:
```bash
gcloud dataplex aspect-types list --location=northamerica-northeast1
```

See [Setup Instructions](#step-2-create-aspect-types).

---

**Issue**: Data quality scans not triggering

**Solution**:
1. Check scheduler job status: `gcloud scheduler jobs list`
2. View logs: `gcloud logging read "resource.type=cloud_scheduler_job"`
3. Verify IAM permissions on service account

---

### Debug Logging

Enable verbose Pulumi logging:
```bash
pulumi up --logtostderr -v=9
```

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

See [CODE-ELEGANCE-REVIEW.md](CODE-ELEGANCE-REVIEW.md) for code quality guidelines.

---

## 📄 License

Copyright © TELUS. All rights reserved.

---

## 📞 Support

### Documentation
- [COMPONENT-OVERVIEW.md](COMPONENT-OVERVIEW.md) - Plain language overview
- [CHANGELOG-v0.0.23.md](CHANGELOG-v0.0.23.md) - Version history
- [CLOUD-SCHEDULER-IMPLEMENTATION.md](CLOUD-SCHEDULER-IMPLEMENTATION.md) - Scheduler details
- [AUTO-PAUSE-FEATURE.md](AUTO-PAUSE-FEATURE.md) - Auto-pause guide

### Contact
For questions or issues, contact:
- **Data Platform Team**: data-platform@telus.com
- **Issues**: [GitHub Issues](https://github.com/graemeoliver/pulumi-dataproducts-component/issues)

---

**Version**: v0.0.23
**Last Updated**: 2026-07-16
**Status**: Production Ready ✅
