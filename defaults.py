"""
defaults.py — Default configuration constants for the DataProductWithAspects component

This module centralizes all default values used across the component,
making them easy to find, update, and maintain.
"""

# ============================================================================
# Business Context Defaults
# ============================================================================

DEFAULT_BUSINESS_DOMAIN = "Data Platform"
"""Default business domain when not specified"""

DEFAULT_GLOSSARY_TERMS = []
"""Default glossary terms (empty list)"""


# ============================================================================
# Compliance Defaults
# ============================================================================

DEFAULT_DATA_CLASSIFICATION = "internal"
"""Default data classification level: public, internal, confidential, or restricted"""

DEFAULT_RETENTION_YEARS = 7
"""Default data retention period in years"""

DEFAULT_CONTAINS_PII = False
"""Default flag for whether data contains PII"""

DEFAULT_COMPLIANCE_FRAMEWORKS = []
"""Default list of compliance frameworks (e.g., GDPR, SOX, PIPEDA)"""


# ============================================================================
# System/Technical Defaults
# ============================================================================

DEFAULT_SLA_TIER = "standard"
"""Default SLA tier: critical, standard, or low"""

DEFAULT_AVAILABILITY_TARGET = "99.9%"
"""Default availability target percentage"""

DEFAULT_SUPPORT_HOURS = "business-hours"
"""Default support hours description"""


# ============================================================================
# Version Management Defaults
# ============================================================================

DEFAULT_VERSION = "1.0.0"
"""Default version number for new data products"""

DEFAULT_CHANGELOG = ""
"""Default changelog (empty string)"""


# ============================================================================
# Data Quality Defaults
# ============================================================================

DEFAULT_ENABLE_DATA_QUALITY_SCANS = False
"""Default flag for enabling data quality scans"""

DEFAULT_QUALITY_SCAN_SCHEDULE = "0 2 * * *"
"""Default cron schedule for quality scans (2 AM daily)"""

DEFAULT_ENABLE_MONITORING = False
"""Default flag for enabling monitoring"""

DEFAULT_ENABLE_COST_TRACKING = True
"""Default flag for enabling cost tracking labels"""


# ============================================================================
# Cloud Scheduler Defaults
# ============================================================================

DEFAULT_USE_CLOUD_SCHEDULER = True
"""Default flag for using Cloud Scheduler instead of internal Dataplex scheduling"""

DEFAULT_SCHEDULER_TIME_ZONE = "America/Toronto"
"""Default time zone for Cloud Scheduler jobs"""

DEFAULT_SCHEDULER_RETRY_COUNT = 3
"""Default number of retry attempts for failed scheduler jobs"""

DEFAULT_SCHEDULER_MAX_RETRY_DURATION = "300s"
"""Default maximum duration for retry attempts (5 minutes)"""

DEFAULT_SCHEDULER_MIN_BACKOFF_DURATION = "5s"
"""Default minimum backoff duration between retries"""

DEFAULT_SCHEDULER_MAX_BACKOFF_DURATION = "3600s"
"""Default maximum backoff duration between retries (1 hour)"""

DEFAULT_SCHEDULER_MAX_DOUBLINGS = 5
"""Default maximum number of times to double the backoff duration"""


# ============================================================================
# Aspect Type Templates
# ============================================================================

# Business Context Aspects (Mandatory)
ASPECT_TYPE_BUSINESS_CONTEXT = "projects/{project}/locations/{location}/aspectTypes/business-context"
ASPECT_TYPE_DOMAIN_CLASSIFICATION = "projects/{project}/locations/{location}/aspectTypes/domain-classification"

# Compliance Aspects (Mandatory)
ASPECT_TYPE_DATA_CLASSIFICATION = "projects/{project}/locations/{location}/aspectTypes/data-classification"
ASPECT_TYPE_COMPLIANCE_POLICY = "projects/{project}/locations/{location}/aspectTypes/compliance-policy"
ASPECT_TYPE_RETENTION_POLICY = "projects/{project}/locations/{location}/aspectTypes/retention-policy"

# System/Technical Aspects (Mandatory)
ASPECT_TYPE_OPERATIONAL_METADATA = "projects/{project}/locations/{location}/aspectTypes/operational-metadata"
ASPECT_TYPE_TECHNICAL_OWNERSHIP = "projects/{project}/locations/{location}/aspectTypes/technical-ownership"
ASPECT_TYPE_SLA_METADATA = "projects/{project}/locations/{location}/aspectTypes/sla-metadata"

# Optional Aspects
ASPECT_TYPE_DATA_LINEAGE = "projects/{project}/locations/{location}/aspectTypes/data-lineage"


# ============================================================================
# SLA Tier Response Times
# ============================================================================

SLA_RESPONSE_TIMES = {
    "critical": "15 minutes",
    "standard": "4 hours",
    "low": "24 hours"
}
"""Mapping of SLA tiers to response time targets"""


# ============================================================================
# DataHub 2 Orchestrator Defaults
# ============================================================================

DH2_DEFAULT_BUSINESS_DOMAIN = "DataHub2"
"""Default business domain for DH2 pipelines"""

DH2_DEFAULT_BUSINESS_OWNER = "data-platform@telus.com"
"""Default business owner for DH2 pipelines"""

DH2_DEFAULT_TECHNICAL_OWNER = "data-platform@telus.com"
"""Default technical owner for DH2 pipelines"""

DH2_DEFAULT_TECHNICAL_CONTACT = "platform-oncall@telus.com"
"""Default technical contact for DH2 pipelines"""

DH2_DEFAULT_DATA_CLASSIFICATION = "internal"
"""Default data classification for DH2 pipelines"""

DH2_DEFAULT_PRIMARY_SCHEMA = "public"
"""Default schema name when none specified"""

DH2_DEFAULT_DQ_SCHEDULE = "0 3 * * *"
"""Default schedule for DH2 data quality scans (3 AM daily)"""

DH2_DEFAULT_DP_SCHEDULE = "0 2 * * *"
"""Default schedule for DH2 data profiling scans (2 AM daily)"""

DH2_DEFAULT_SAMPLING_PERCENT = 100.0
"""Default sampling percentage for DH2 data quality scans"""
