#!/usr/bin/env python3
"""
Script to convert args.snake_case to args.get("camelCase", default) format
"""

import re

# Mapping of snake_case to camelCase properties
PROPERTY_MAP = {
    'data_product_id': 'dataProductId',
    'display_name': 'displayName',
    'access_groups': 'accessGroups',
    'business_domain': 'businessDomain',
    'business_owner': 'businessOwner',
    'business_purpose': 'businessPurpose',
    'glossary_terms': 'glossaryTerms',
    'data_classification': 'dataClassification',
    'compliance_frameworks': 'complianceFrameworks',
    'contains_pii': 'containsPii',
    'retention_years': 'retentionYears',
    'retention_justification': 'retentionJustification',
    'technical_owner': 'technicalOwner',
    'technical_contact': 'technicalContact',
    'sla_tier': 'slaTier',
    'availability_target': 'availabilityTarget',
    'support_hours': 'supportHours',
    'bigquery_datasets': 'bigqueryDatasets',
    'gcs_buckets': 'gcsBuckets',
    'enable_data_quality_scans': 'enableDataQualityScans',
    'quality_scan_schedule': 'qualityScanSchedule',
    'quality_rules': 'qualityRules',
    'enable_monitoring': 'enableMonitoring',
    'alert_email': 'alertEmail',
    'cost_center': 'costCenter',
    'enable_cost_tracking': 'enableCostTracking',
    'upstream_data_products': 'upstreamDataProducts',
    'downstream_data_products': 'downstreamDataProducts',
    'transformation_jobs': 'transformationJobs',
    'pre_approved_service_accounts': 'preApprovedServiceAccounts',
    'additional_aspects': 'additionalAspects',
}

# Default values for optional properties
DEFAULTS = {
    'glossaryTerms': '[]',
    'complianceFrameworks': '[]',
    'containsPii': 'False',
    'retentionYears': '7',
    'slaTier': '"standard"',
    'availabilityTarget': '"99.9%"',
    'supportHours': '"business-hours"',
    'bigqueryDatasets': '[]',
    'gcsBuckets': '[]',
    'enableDataQualityScans': 'False',
    'qualityScanSchedule': '"0 2 * * *"',
    'qualityRules': 'None',
    'enableMonitoring': 'False',
    'alertEmail': 'None',
    'costCenter': 'None',
    'enableCostTracking': 'True',
    'version': '"1.0.0"',
    'changelog': '""',
    'upstreamDataProducts': '[]',
    'downstreamDataProducts': '[]',
    'transformationJobs': '[]',
    'preApprovedServiceAccounts': '[]',
    'tags': '{}',
    'additionalAspects': '{}',
}

def convert_file(input_file, output_file):
    with open(input_file, 'r') as f:
        content = f.read()

    # Replace args.property_name with args.get("propertyName", default) or args["propertyName"]
    for snake, camel in PROPERTY_MAP.items():
        pattern = rf'\bargs\.{snake}\b'
        if camel in DEFAULTS:
            replacement = f'args.get("{camel}", {DEFAULTS[camel]})'
        else:
            replacement = f'args["{camel}"]'
        content = re.sub(pattern, replacement, content)

    # Also handle direct property access without args prefix
    content = re.sub(r'\bargs\.project\b', 'args["project"]', content)
    content = re.sub(r'\bargs\.location\b', 'args["location"]', content)
    content = re.sub(r'\bargs\.description\b', 'args["description"]', content)
    content = re.sub(r'\bargs\.version\b', 'args.get("version", "1.0.0")', content)
    content = re.sub(r'\bargs\.changelog\b', 'args.get("changelog", "")', content)
    content = re.sub(r'\bargs\.tags\b', 'args.get("tags", {})', content)

    with open(output_file, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    import sys
    input_file = 'C:/projects/cubedev_source/gcp/dataproducts-component/dataproduct.py'
    output_file = 'C:/projects/cubedev_source/gcp/dataproducts-component/dataproduct_new.py'
    convert_file(input_file, output_file)
    print(f"Converted {input_file} to {output_file}")
