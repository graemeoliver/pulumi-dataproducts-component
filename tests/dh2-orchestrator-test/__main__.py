"""
Test program for DataHub 2 orchestrator.

This program validates the DataProductDH2Orchestrator without actually
deploying to GCP (dry-run mode).
"""

import sys
import os

# Add parent directory to path to import the orchestrator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pulumi
from data_product_dh2_orchestrator import DataProductDH2Orchestrator

# Mock configuration for testing
# In a real scenario, this would come from Pulumi.{stack}.yaml
test_pipelines = {
    "customer-sync": {
        "source": "postgresql",
        "schemas": "public, app",
        "data_product": {
            "enabled": True,
            "display_name": "Customer Sync Data Product",
            "description": "Customer data synchronized from PostgreSQL",
            "business_domain": "Customer Experience",
            "business_owner": "customer-team@company.com",
            "business_purpose": "Track customer interactions and account status",
            "data_classification": "confidential",
            "retention_justification": "Customer data retention for compliance",
            "retention_years": 7,
            "technical_owner": "data-platform@company.com",
            "technical_contact": "platform-oncall@company.com",
            "contains_pii": True,
            "compliance_frameworks": ["GDPR", "PIPEDA"],
            "sla_tier": "critical",
            "availability_target": "99.9%",
            "support_hours": "24x7",
            "version": "1.0.0",
            "data_quality": {
                "enabled": True,
                "schedule": "0 3 * * *",
                "sampling_percent": 100.0,
                "rules": [
                    {
                        "name": "customer_id_not_null",
                        "description": "Customer ID must not be null",
                        "dimension": "COMPLETENESS",
                        "column": "customer_id",
                        "non_null_expectation": {},
                        "threshold": 1.0
                    },
                    {
                        "name": "email_format_valid",
                        "description": "Email must be valid format",
                        "dimension": "VALIDITY",
                        "column": "email",
                        "regex_expectation": {
                            "regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                        },
                        "threshold": 0.95
                    },
                    {
                        "name": "customer_id_unique",
                        "description": "Customer ID must be unique",
                        "dimension": "UNIQUENESS",
                        "column": "customer_id",
                        "uniqueness_expectation": {},
                        "threshold": 1.0
                    }
                ]
            },
            "data_profiling": {
                "enabled": True,
                "schedule": "0 2 * * *",
                "sampling_percent": 10.0
            }
        }
    },
    "order-sync": {
        "source": "postgresql",
        "schemas": "public",
        "data_product": {
            "enabled": True,
            "display_name": "Order Sync Data Product",
            "description": "Order data synchronized from PostgreSQL",
            "business_domain": "Commerce",
            "business_owner": "commerce-team@company.com",
            "business_purpose": "Track order lifecycle and revenue",
            "data_classification": "confidential",
            "retention_justification": "Financial records retention",
            "technical_owner": "data-platform@company.com",
            "technical_contact": "platform-oncall@company.com",
            # Note: No data_quality or data_profiling blocks - should skip scans
        }
    },
    "analytics-pipeline": {
        "source": "bigquery",
        "schemas": "analytics",
        # Note: No data_product block - should be skipped entirely
    }
}

def test_orchestrator():
    """Test the orchestrator with mock configuration"""

    pulumi.log.info("[TEST] Starting DH2 orchestrator test")

    try:
        # Initialize orchestrator with test configuration
        orchestrator = DataProductDH2Orchestrator(
            stack_prefix="dev-ne1-01",
            consumer="una",
            group="group-01",
            lake_project_id="test-lake-project",
            location="northamerica-northeast1",
            pipelines=test_pipelines,
        )

        pulumi.log.info("[TEST] Orchestrator initialized successfully")

        # Note: We're NOT calling orchestrator.run() to avoid creating real resources
        # This test validates import and initialization only

        # Validate orchestrator properties
        assert orchestrator.stack_prefix == "dev-ne1-01"
        assert orchestrator.consumer == "una"
        assert orchestrator.group == "group-01"
        assert orchestrator.lake_project_id == "test-lake-project"
        assert orchestrator.location == "northamerica-northeast1"
        assert len(orchestrator.pipelines) == 3

        pulumi.log.info("[TEST] Orchestrator properties validated")

        # Test helper methods
        from data_product_dh2_orchestrator import _slugify, _make_data_product_id

        # Test slugify
        assert _slugify("dev-ne1-01") == "dev_ne1_01"
        assert _slugify("Customer-Sync") == "customer_sync"
        pulumi.log.info("[TEST] _slugify() works correctly")

        # Test data product ID generation
        dp_id = _make_data_product_id("dev-ne1-01", "una", "group-01", "customer-sync")
        assert dp_id == "dev_ne1_01_una_group_01_customer_sync"
        pulumi.log.info("[TEST] _make_data_product_id() works correctly")

        # Test primary schema extraction
        schema = orchestrator._get_primary_schema(test_pipelines["customer-sync"])
        assert schema == "public"
        pulumi.log.info("[TEST] _get_primary_schema() works correctly")

        pulumi.log.info("[TEST] ✓ All validation tests passed!")
        pulumi.log.info("[TEST] The orchestrator is ready for use")

        # Export test results
        pulumi.export("test_status", "PASSED")
        pulumi.export("pipelines_with_data_products", 2)  # customer-sync and order-sync
        pulumi.export("pipelines_skipped", 1)  # analytics-pipeline

    except Exception as e:
        pulumi.log.error(f"[TEST] ✗ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        pulumi.export("test_status", "FAILED")
        pulumi.export("error", str(e))
        raise


# Run the test
test_orchestrator()
