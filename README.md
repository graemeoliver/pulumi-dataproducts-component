# Pulumi Component: GCP Dataplex Data Products

This Pulumi component creates Dataplex data products with standardized governance aspects for Google Cloud Platform.

## 📋 Prerequisites

- **Pulumi CLI**: Version 3.0.0 or higher
- **Python**: Version 3.8 or higher
- **GCP Project**: With appropriate permissions to create Dataplex resources
- **Service Account**: With necessary IAM roles (see Required Permissions below)
- **Aspect Types**: Must be pre-created in Dataplex (see Setup section)

## 🎯 Component Overview

This repository provides a Pulumi component for creating standardized Dataplex data products with mandatory governance aspects.

### DataProductWithAspects Component

The `DataProductWithAspects` component is a comprehensive Pulumi resource that creates a Dataplex data product with:

**Mandatory Aspects (Automatically Applied):**
- **Business Context**: Domain, owner, purpose, glossary terms
- **Data Classification**: Classification level (public/internal/confidential/restricted)
- **Compliance Policy**: Frameworks, PII flag, compliance requirements
- **Retention Policy**: Retention period and justification
- **Technical Ownership**: Technical owner and contact information
- **Operational Metadata**: Version, changelog, deployment info
- **SLA Metadata**: Tier, availability target, support hours

**Optional Features:**
- **Data Asset Attachment**: Link BigQuery datasets and GCS buckets
- **Data Lineage**: Track upstream/downstream dependencies
- **Data Quality Scans**: Configure automated quality checks
- **Monitoring & Alerting**: Set up alerts for data issues
- **Cost Tracking**: Enable cost center labeling
- **Access Automation**: Pre-approve service accounts

**Typical Use Case:**
Create a governed data product for analytics with automatic application of all mandatory governance aspects, ensuring compliance and standardization across your organization.

---

## 🚀 Usage Example

### Basic Example

```yaml
name: my-data-products
runtime: yaml

packages:
  dataproducts: https://github.com/graemeoliver/pulumi-dataproducts-component@v0.0.2

resources:
  revenueAnalytics:
    type: dataproducts:index:DataProductWithAspects
    properties:
      # Core Properties (Required)
      dataProductId: revenue-analytics-product
      project: my-gcp-project
      location: northamerica-northeast1
      displayName: Revenue Analytics
      description: Revenue and order analytics for business intelligence

      # Access Groups (Required)
      accessGroups:
        bi-admins:
          id: bi-admins
          displayName: BI Admins
          principal:
            googleGroup: bi-admins@company.com

      # Business Context (Required)
      businessDomain: Finance
      businessOwner: finance-team@company.com
      businessPurpose: Track revenue streams and order patterns
      glossaryTerms:
        - total-revenue
        - average-order-value

      # Compliance (Required)
      dataClassification: confidential
      complianceFrameworks:
        - SOX
        - PCI-DSS
      containsPii: false
      retentionYears: 7
      retentionJustification: Financial records retention policy

      # Technical (Required)
      technicalOwner: data-platform@company.com
      technicalContact: platform-oncall@company.com
      slaTier: critical
      availabilityTarget: 99.9%
      supportHours: 24x7

      # Optional: Data Assets
      bigqueryDatasets:
        - revenue_analytics
        - order_metrics

      # Optional: Version Management
      version: 1.0.0
      changelog: Initial release

outputs:
  productName: ${revenueAnalytics.dataProductName}
  productId: ${revenueAnalytics.dataProductId}
  aspectsApplied: ${revenueAnalytics.aspectsApplied}
```

---

## 📦 Installation Methods

### Method 1: Via GitHub Release (Recommended)

```yaml
packages:
  dataproducts: https://github.com/graemeoliver/pulumi-dataproducts-component@v0.0.2
```

### Method 2: Via Local Path (Development)

```bash
git clone https://github.com/graemeoliver/pulumi-dataproducts-component.git
```

```yaml
packages:
  dataproducts: file://path/to/pulumi-dataproducts-component
```

### Method 3: Via Specific Branch

```yaml
packages:
  dataproducts: https://github.com/graemeoliver/pulumi-dataproducts-component@main
```

---

## 🔧 Setup

### 1. Create Aspect Types in Dataplex

Before using this component, you must create the required aspect types in your GCP project:

```bash
# Business Context Aspects
gcloud dataplex aspect-types create business-context \
  --project=YOUR_PROJECT \
  --location=YOUR_LOCATION \
  --display-name="Business Context"

gcloud dataplex aspect-types create domain-classification \
  --project=YOUR_PROJECT \
  --location=YOUR_LOCATION \
  --display-name="Domain Classification"

# Compliance Aspects
gcloud dataplex aspect-types create data-classification \
  --project=YOUR_PROJECT \
  --location=YOUR_LOCATION \
  --display-name="Data Classification"

gcloud dataplex aspect-types create compliance-policy \
  --project=YOUR_PROJECT \
  --location=YOUR_LOCATION \
  --display-name="Compliance Policy"

gcloud dataplex aspect-types create retention-policy \
  --project=YOUR_PROJECT \
  --location=YOUR_LOCATION \
  --display-name="Retention Policy"

# Technical Aspects
gcloud dataplex aspect-types create technical-ownership \
  --project=YOUR_PROJECT \
  --location=YOUR_LOCATION \
  --display-name="Technical Ownership"

gcloud dataplex aspect-types create operational-metadata \
  --project=YOUR_PROJECT \
  --location=YOUR_LOCATION \
  --display-name="Operational Metadata"

gcloud dataplex aspect-types create sla-metadata \
  --project=YOUR_PROJECT \
  --location=YOUR_LOCATION \
  --display-name="SLA Metadata"

# Optional Aspects
gcloud dataplex aspect-types create data-lineage \
  --project=YOUR_PROJECT \
  --location=YOUR_LOCATION \
  --display-name="Data Lineage"
```

### 2. Create Virtual Environment

```bash
cd pulumi-dataproducts-component
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 📚 Component Inputs

### Required Inputs

| Property | Type | Description |
|----------|------|-------------|
| `dataProductId` | string | Unique identifier for the data product |
| `project` | string | GCP project ID |
| `location` | string | GCP location/region |
| `displayName` | string | Human-readable name |
| `description` | string | Detailed description |
| `accessGroups` | map | Access control groups (Google Groups) |
| `businessDomain` | string | Business domain (e.g., "Finance", "Marketing") |
| `businessOwner` | string | Business owner email |
| `businessPurpose` | string | Business purpose statement |
| `dataClassification` | string | Classification level (public/internal/confidential/restricted) |
| `retentionJustification` | string | Justification for retention period |
| `technicalOwner` | string | Technical owner email |
| `technicalContact` | string | Technical contact email |

### Optional Inputs

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `glossaryTerms` | list[string] | [] | List of glossary terms |
| `complianceFrameworks` | list[string] | [] | Compliance frameworks (GDPR, SOX, etc.) |
| `containsPii` | boolean | false | Whether data contains PII |
| `retentionYears` | integer | 7 | Data retention period in years |
| `slaTier` | string | "standard" | SLA tier (critical/standard/low) |
| `availabilityTarget` | string | "99.9%" | Availability target percentage |
| `supportHours` | string | "business-hours" | Support hours |
| `bigqueryDatasets` | list[string] | [] | BigQuery datasets to attach |
| `gcsBuckets` | list[string] | [] | GCS buckets to attach |
| `enableDataQualityScans` | boolean | false | Enable quality scans |
| `enableMonitoring` | boolean | false | Enable monitoring |
| `version` | string | "1.0.0" | Version number |
| `tags` | map[string] | {} | Additional tags |

### Component Outputs

| Output | Type | Description |
|--------|------|-------------|
| `dataProductName` | string | Full name of the data product |
| `dataProductId` | string | Data product ID |
| `aspectsApplied` | integer | Number of aspects applied |

---

##  Required Permissions

The service account used by Pulumi must have these IAM roles:

- `roles/dataplex.admin` - To create data products and aspects
- `roles/iam.serviceAccountUser` - To impersonate service accounts (if needed)

---

## 🏗️ Component Architecture

```
DataProductWithAspects Component
├── Data Product Resource
├── Mandatory Aspects (8)
│   ├── Business Context
│   ├── Domain Classification
│   ├── Data Classification
│   ├── Compliance Policy
│   ├── Retention Policy
│   ├── Technical Ownership
│   ├── Operational Metadata
│   └── SLA Metadata
├── Optional Aspects
│   └── Data Lineage
├── Data Assets (optional)
│   ├── BigQuery Datasets
│   └── GCS Buckets
└── Quality Scans (optional)
```

---

## 🤝 Contributing

Contributions are welcome! Please submit pull requests or open issues for any improvements.

---

## 📝 License

Copyright © TELUS. All rights reserved.

---

## 📞 Support

For questions or issues, please contact the Data Platform team at data-platform@telus.com
