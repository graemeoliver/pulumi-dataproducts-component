# DataProductWithAspects Component - Overview

## What Is This?

The **DataProductWithAspects** component is an automated tool that creates and manages data products in Google Cloud Platform (GCP). Think of it as a "one-click setup" for properly documented and organized data assets in the cloud.

Instead of manually creating and configuring multiple cloud resources, this component does it all for you in a consistent, standardized way.

---

## What Problem Does It Solve?

### Before This Component

When organizations wanted to create a data product in GCP, they had to:
1. ✋ Manually create the data product in GCP Dataplex
2. ✋ Manually add metadata about who owns it, what it's for, and how sensitive it is
3. ✋ Manually set up data quality scans to check the data
4. ✋ Manually configure schedules for when scans should run
5. ✋ Keep track of all these pieces separately
6. ✋ Hope everyone follows the same standards

**Result**: Inconsistent documentation, missing metadata, hard to find who owns what, and lots of manual work.

### With This Component

You write one simple configuration file, and the component automatically:
- ✅ Creates the data product
- ✅ Adds all required metadata (standardized)
- ✅ Sets up data quality scans
- ✅ Configures automated scheduling
- ✅ Organizes everything properly
- ✅ Ensures consistency across all data products

**Result**: Consistent, well-documented data products with minimal effort.

---

## What Does It Create?

When you use this component, it automatically creates and configures these things in GCP:

### 1. **Data Product** 📦
- A container that represents your data asset
- Has a unique ID and descriptive name
- Organized in a structured way in Google Cloud

### 2. **Metadata (Aspects)** 📝
Three types of standardized information attached to every data product:

#### Business Context
- **What**: What domain does this belong to? (Finance, Marketing, Engineering, etc.)
- **Who**: Who owns this from a business perspective?
- **Why**: What's the business purpose of this data?
- **Terms**: Related business glossary terms

#### Data Classification
- **Sensitivity**: Is this public, internal, confidential, or restricted?
- **Privacy**: Does it contain personally identifiable information (PII)?

#### Technical Ownership
- **Owner**: Who maintains this technically?
- **Contact**: Who to reach for technical issues?

### 3. **Data Quality Scans** 🔍
Automated checks that run regularly to verify:
- Data completeness (no missing values where there shouldn't be)
- Data validity (values are within expected ranges)
- Custom rules you define

### 4. **Cloud Scheduler Jobs** ⏰
Automated timers that trigger data quality scans on a schedule:
- **Default**: Runs at 2 AM daily
- **Configurable**: Can run hourly, daily, weekly, etc.
- **Smart**: Automatically paused in staging environments to save money
- **Reliable**: Retries automatically if something fails

### 5. **Data Assets** (Optional) 💾
Links to actual data storage:
- BigQuery datasets (database tables)
- Google Cloud Storage buckets (file storage)

### 6. **Monitoring** (Optional) 📊
- Alerts when something goes wrong
- Email notifications to designated contacts

---

## Key Features

### 1. Standardized Metadata
Every data product has the same required information:
- Business owner and purpose
- Data classification level
- Technical contacts
- No more "who owns this?" questions

### 2. Automatic Documentation
All metadata is:
- ✅ Stored in GCP Dataplex
- ✅ Searchable
- ✅ Version-controlled
- ✅ Always up-to-date

### 3. Smart Scheduling
- **Production**: Scans run automatically on schedule
- **Staging**: Scans are paused by default (saves money, prevents accidents)
- **Flexible**: Override defaults when needed

### 4. Data Quality Checks
Automatically runs tests to ensure:
- Data meets quality standards
- Problems are caught early
- Quality history is tracked over time

### 5. Cost Management
- Adds labels to track costs by:
  - Data product
  - Cost center
  - Business domain
  - Version

### 6. Easy to Use
- Define everything in one configuration file
- Deploy with a single command
- Update by changing the config and redeploying

---

## How It Works (Simple Example)

### Step 1: Write Configuration
You create a simple configuration file:

```yaml
My Sales Data Product:
  ID: sales-data-product
  Description: Monthly sales data for reporting

  Business Info:
    Domain: Finance
    Owner: jane.smith@company.com
    Purpose: Monthly sales reporting and analysis

  Classification:
    Level: Internal
    Contains PII: No

  Technical Info:
    Owner: data-team@company.com
    Contact: platform-oncall@company.com

  Data Quality:
    Enable Scans: Yes
    Schedule: Daily at 2 AM
    Datasets:
      - sales_monthly
      - sales_weekly
```

### Step 2: Deploy
Run one command:
```bash
pulumi up
```

### Step 3: Done! ✅
The component automatically creates:
- ✅ Data product in GCP Dataplex
- ✅ All metadata attached
- ✅ Data quality scans configured
- ✅ Scheduler jobs set up
- ✅ Everything organized and documented

---

## Who Uses This?

### Data Engineers
- Quickly create standardized data products
- Don't worry about missing metadata
- Automated quality checks

### Data Governance Teams
- Ensure all data products have required metadata
- Consistent classification standards
- Easy to audit and track

### Business Stakeholders
- Easy to find who owns what data
- Clear documentation of data purpose
- Understand data sensitivity levels

### Platform Teams
- Reduce manual setup work
- Consistent infrastructure
- Cost tracking built-in

---

## Real-World Benefits

### Time Savings
- **Before**: 2-4 hours to manually set up a data product with all metadata and scans
- **After**: 5 minutes to write config, 1 command to deploy

### Consistency
- **Before**: Every team did it differently, metadata often incomplete or missing
- **After**: Same standards everywhere, all required metadata always present

### Quality
- **Before**: Manual quality checks, if done at all
- **After**: Automatic quality checks on every data product

### Visibility
- **Before**: Hard to find who owns data or what it's for
- **After**: All information searchable in one place

### Cost Control
- **Before**: Hard to track costs per data product
- **After**: Automatic cost labels on everything

---

## Common Scenarios

### Scenario 1: New Data Product
**Need**: Create a new monthly sales report data product

**Without Component**:
1. Create data product in GCP console
2. Manually add metadata fields
3. Set up quality scan
4. Configure scheduler
5. Add cost labels
6. Document everything
**Time**: 2-4 hours

**With Component**:
1. Copy existing config
2. Change names and settings
3. Run `pulumi up`
**Time**: 5-10 minutes

---

### Scenario 2: Staging Environment
**Need**: Test changes in staging without running expensive scans

**Without Component**:
- Manually remember to pause scans
- Risk forgetting and wasting money
- Manual process every time

**With Component**:
- Automatically detects staging projects
- Pauses scheduler jobs automatically
- Still allows manual testing when needed
- No risk of accidental costs

---

### Scenario 3: Compliance Audit
**Need**: Prove all data products are properly classified

**Without Component**:
- Check each data product manually
- Hope metadata was entered correctly
- Find missing information
- Update manually

**With Component**:
- All data products have standardized metadata
- Required fields cannot be skipped
- Single source of truth
- Easy to generate reports

---

## What You Need to Know

### Requirements
1. **Google Cloud Project**: Where the data product will live
2. **Pulumi**: Tool used to deploy the component
3. **Configuration File**: Describes what you want to create
4. **Permissions**: Ability to create resources in GCP

### Skills Needed
- Basic understanding of YAML or configuration files
- Knowledge of your data (what it is, who owns it, etc.)
- Access to run deployment commands

**No coding required** - just fill in configuration values!

---

## Configuration Options

### Required Information
Every data product must have:
- ✅ Unique ID
- ✅ Display name and description
- ✅ Business domain
- ✅ Business owner email
- ✅ Business purpose
- ✅ Data classification level
- ✅ Retention justification
- ✅ Technical owner email
- ✅ Technical contact email

### Optional Features
You can also configure:
- BigQuery datasets to attach
- GCS buckets to attach
- Data quality scan rules
- Scan schedule
- Monitoring alerts
- Cost center tracking
- Version information
- And more...

---

## Smart Features Explained

### 1. Auto-Pause for Staging
**What**: Scheduler jobs are automatically paused in staging projects

**Why**: Prevents accidental costs from scans running in test environments

**How It Works**:
- Component detects project names starting with "bi-stg"
- Automatically pauses scheduler jobs
- Can still trigger scans manually for testing
- Can override if needed

**Example**:
- Project "bi-stg-analytics" → Scans paused ✅
- Project "prod-analytics" → Scans enabled ✅

---

### 2. Retry Logic
**What**: Failed scans automatically retry with smart backoff

**Why**: Temporary network issues shouldn't cause permanent failures

**How It Works**:
- First retry: Wait 5 seconds
- Second retry: Wait longer (exponential backoff)
- Third retry: Wait even longer
- Maximum 3 retries, then alert

---

### 3. Cost Tracking Labels
**What**: Automatic labels on all resources for cost attribution

**Why**: Understand what each data product costs

**What Gets Labeled**:
- Data product ID
- Cost center
- Business domain
- Managed by (always "pulumi")
- Version

**Benefit**: Filter GCP billing by data product to see exact costs

---

### 4. Centralized Scheduling
**What**: All scan schedules in Cloud Scheduler (not scattered)

**Why**: One place to see, manage, and monitor all scheduled jobs

**Benefits**:
- Easy to pause/resume jobs
- Clear audit trail
- Centralized monitoring
- Better retry policies

---

## Example Use Cases

### Use Case 1: Customer Data
```
Data Product: Customer Master Data
Classification: Confidential (contains PII)
Scans: Daily quality checks
Purpose: Customer database for CRM
Owner: Customer Success team
```

### Use Case 2: Sales Reports
```
Data Product: Monthly Sales Reports
Classification: Internal
Scans: Weekly quality checks
Purpose: Executive reporting
Owner: Finance team
```

### Use Case 3: Public Data
```
Data Product: Product Catalog
Classification: Public
Scans: Daily quality checks
Purpose: External website data
Owner: Marketing team
```

---

## Monitoring and Alerting

### What Gets Monitored
- Data quality scan results
- Scan failures
- Schedule execution
- Configuration changes

### How You're Notified
- Email alerts (if configured)
- Cloud Logging entries
- Cloud Monitoring metrics
- GCP console notifications

### What You Can Track
- Scan success/failure rate
- Data quality trends over time
- Resource costs
- Metadata completeness

---

## Common Questions

### Q: Do I need to be a programmer?
**A**: No! You just need to fill in configuration values. The component handles all the technical details.

### Q: What if I make a mistake?
**A**: You can update the configuration and redeploy. The component will update the data product with the new values.

### Q: Can I customize the quality checks?
**A**: Yes! You can define custom quality rules based on your data requirements.

### Q: How much does it cost?
**A**: Small cost for Cloud Scheduler jobs (~$0.10/job/month). First 3 jobs are free. Data quality scans cost is based on data scanned.

### Q: Can I use this for sensitive data?
**A**: Yes! You set the classification level. The component supports: public, internal, confidential, and restricted.

### Q: What happens to existing data products?
**A**: You can import existing data products and have the component manage them going forward.

### Q: Can I disable features I don't need?
**A**: Yes! All optional features can be turned off. Only core metadata is required.

---

## Version History

### Current Version: v0.0.23

**Major Features**:
- ✅ Cloud Scheduler integration
- ✅ Auto-pause for staging environments
- ✅ Standardized aspect registry
- ✅ Configurable retry policies
- ✅ Cost tracking labels
- ✅ Data quality scans
- ✅ Monitoring and alerting

**What's New in v0.0.23**:
- Cloud Scheduler instead of internal scheduling (better monitoring)
- Smart auto-pause for staging projects (cost savings)
- Improved code structure (easier to maintain)
- Comprehensive documentation

---

## Getting Started

### Step 1: Prerequisites
- GCP project created
- Pulumi installed
- Access to create resources

### Step 2: Install Component
```bash
# Add to your Pulumi project
pulumi plugin install resource dataproducts v0.0.23
```

### Step 3: Create Configuration
Copy an example configuration and modify for your needs

### Step 4: Set Up IAM (One-Time)
```bash
# Grant permissions for Cloud Scheduler
./scripts/setup-cloud-scheduler-iam.sh YOUR-PROJECT-ID
```

### Step 5: Deploy
```bash
pulumi up
```

### Step 6: Verify
Check GCP console to see your data product with all metadata!

---

## Support and Documentation

### Full Documentation
- [CHANGELOG-v0.0.23.md](CHANGELOG-v0.0.23.md) - Recent changes
- [CLOUD-SCHEDULER-IMPLEMENTATION.md](CLOUD-SCHEDULER-IMPLEMENTATION.md) - Scheduler details
- [AUTO-PAUSE-FEATURE.md](AUTO-PAUSE-FEATURE.md) - Auto-pause guide
- [REFACTORING-SUMMARY.md](REFACTORING-SUMMARY.md) - Technical improvements

### Quick Start Guides
- [scripts/README.md](scripts/README.md) - IAM setup and troubleshooting
- Component tests - Examples of valid configurations

### Need Help?
1. Check documentation files
2. Review example configurations
3. Run validation tests
4. Contact platform team

---

## Summary

### What This Component Does
Creates and manages GCP data products with:
- ✅ Standardized metadata
- ✅ Automated quality checks
- ✅ Smart scheduling
- ✅ Cost tracking
- ✅ Consistent organization

### Why Use It
- ⚡ Save time (minutes instead of hours)
- 📋 Ensure consistency (same standards everywhere)
- 💰 Track costs (automatic labels)
- 🔍 Improve quality (automated checks)
- 📊 Better governance (required metadata)
- 🚀 Easy deployment (one command)

### Who Benefits
- **Data Engineers**: Less manual work, standardized setup
- **Governance Teams**: Consistent compliance, easy audits
- **Business Users**: Clear ownership, better documentation
- **Platform Teams**: Reduced support burden, cost visibility

---

## Next Steps

1. **Review** the documentation
2. **Try** an example configuration
3. **Deploy** your first data product
4. **Monitor** the results
5. **Scale** to more data products

**Remember**: This component does the hard work for you. You just provide the information about your data, and it handles the rest!

---

**Version**: v0.0.23
**Last Updated**: 2026-07-15
**Status**: Production Ready
