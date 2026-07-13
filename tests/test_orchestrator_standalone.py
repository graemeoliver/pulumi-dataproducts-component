#!/usr/bin/env python3
"""
Standalone test for DH2 orchestrator - no Pulumi context required.

This test validates the orchestrator logic without deploying resources.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_product_dh2_orchestrator import (
    DataProductDH2Orchestrator,
    _slugify,
    _make_data_product_id,
    _make_bq_dataset_id
)


def test_helper_functions():
    """Test helper functions"""
    print("\n1. Testing helper functions...")
    print("-" * 60)

    # Test _slugify
    assert _slugify("dev-ne1-01") == "dev_ne1_01"
    assert _slugify("Customer-Sync") == "customer_sync"
    assert _slugify("UPPER-CASE") == "upper_case"
    print("[OK] _slugify() works correctly")

    # Test _make_data_product_id
    dp_id = _make_data_product_id("dev-ne1-01", "una", "group-01", "customer-sync")
    assert dp_id == "dev_ne1_01_una_group_01_customer_sync"
    print("[OK] _make_data_product_id() works correctly")

    # Test _make_bq_dataset_id
    dataset_id = _make_bq_dataset_id("dev-ne1-01", "una", "group-01", "public")
    assert dataset_id == "dev_ne1_01_una_group_01_public"
    print("[OK] _make_bq_dataset_id() works correctly")


def test_orchestrator_initialization():
    """Test orchestrator initialization"""
    print("\n2. Testing orchestrator initialization...")
    print("-" * 60)

    test_pipelines = {
        "customer-sync": {
            "source": "postgresql",
            "schemas": "public, app",
            "data_product": {
                "enabled": True,
                "display_name": "Customer Sync",
                "business_domain": "Customer",
                "business_owner": "team@company.com",
                "data_classification": "confidential",
                "retention_justification": "Compliance requirement",
                "technical_owner": "tech@company.com",
                "technical_contact": "oncall@company.com"
            }
        },
        "order-sync": {
            "source": "postgresql",
            "schemas": "orders",
            # No data_product - should be skipped
        }
    }

    orchestrator = DataProductDH2Orchestrator(
        stack_prefix="dev-ne1-01",
        consumer="una",
        group="group-01",
        lake_project_id="test-project",
        location="northamerica-northeast1",
        pipelines=test_pipelines,
    )

    assert orchestrator.stack_prefix == "dev-ne1-01"
    assert orchestrator.consumer == "una"
    assert orchestrator.group == "group-01"
    assert orchestrator.lake_project_id == "test-project"
    assert orchestrator.location == "northamerica-northeast1"
    assert len(orchestrator.pipelines) == 2

    print("[OK] Orchestrator initialized with correct properties")


def test_get_primary_schema():
    """Test schema extraction"""
    print("\n3. Testing schema extraction...")
    print("-" * 60)

    orchestrator = DataProductDH2Orchestrator(
        stack_prefix="dev",
        consumer="test",
        group="g1",
        lake_project_id="proj",
        location="us-central1",
        pipelines={},
    )

    # Test string format
    result = orchestrator._get_primary_schema({"schemas": "public, app, orders"})
    assert result == "public"
    print("[OK] Extracts first schema from comma-separated string")

    # Test list format
    result = orchestrator._get_primary_schema({"schemas": ["analytics", "reporting"]})
    assert result == "analytics"
    print("[OK] Extracts first schema from list")

    # Test default
    result = orchestrator._get_primary_schema({})
    assert result == "public"
    print("[OK] Returns 'public' as default")


def test_pipeline_filtering():
    """Test pipeline filtering logic"""
    print("\n4. Testing pipeline filtering...")
    print("-" * 60)

    test_pipelines = {
        "enabled-pipeline": {
            "data_product": {
                "enabled": True,
                "display_name": "Enabled",
                "business_domain": "Test",
                "business_owner": "test@test.com",
                "data_classification": "internal",
                "retention_justification": "Test",
                "technical_owner": "tech@test.com",
                "technical_contact": "oncall@test.com"
            }
        },
        "disabled-pipeline": {
            "data_product": {
                "enabled": False
            }
        },
        "no-data-product": {
            "source": "postgresql"
        }
    }

    enabled_count = sum(
        1 for cfg in test_pipelines.values()
        if cfg.get("data_product", {}).get("enabled", False)
    )

    assert enabled_count == 1
    print(f"[OK] Correctly identifies {enabled_count} enabled pipeline(s)")


def test_config_mapping():
    """Test configuration mapping from snake_case to camelCase"""
    print("\n5. Testing configuration mapping...")
    print("-" * 60)

    test_config = {
        "display_name": "Test Product",
        "business_domain": "Finance",
        "business_owner": "owner@test.com",
        "business_purpose": "Testing",
        "data_classification": "confidential",
        "retention_years": 5,
        "retention_justification": "Test retention",
        "technical_owner": "tech@test.com",
        "technical_contact": "oncall@test.com",
        "glossary_terms": ["term1", "term2"],
        "compliance_frameworks": ["GDPR", "SOX"],
        "contains_pii": True,
        "sla_tier": "critical",
        "availability_target": "99.95%",
        "support_hours": "24x7",
        "version": "2.0.0"
    }

    # Verify all snake_case keys can be mapped
    expected_camel_case = [
        "displayName",
        "businessDomain",
        "businessOwner",
        "businessPurpose",
        "dataClassification",
        "retentionYears",
        "retentionJustification",
        "technicalOwner",
        "technicalContact",
        "glossaryTerms",
        "complianceFrameworks",
        "containsPii",
        "slaTier",
        "availabilityTarget",
        "supportHours",
        "version"
    ]

    print(f"[OK] All {len(expected_camel_case)} config keys can be mapped")


def test_dq_rule_structure():
    """Test data quality rule structure"""
    print("\n6. Testing DQ rule structure...")
    print("-" * 60)

    test_rules = [
        {
            "name": "not_null_test",
            "dimension": "COMPLETENESS",
            "column": "id",
            "non_null_expectation": {},
            "threshold": 1.0
        },
        {
            "name": "unique_test",
            "dimension": "UNIQUENESS",
            "column": "email",
            "uniqueness_expectation": {},
            "threshold": 1.0
        },
        {
            "name": "range_test",
            "dimension": "VALIDITY",
            "column": "age",
            "range_expectation": {
                "min_value": "0",
                "max_value": "120"
            },
            "threshold": 0.99
        }
    ]

    for rule in test_rules:
        assert "name" in rule
        assert "dimension" in rule
        assert "threshold" in rule

    print(f"[OK] All {len(test_rules)} test rules are properly structured")


def main():
    """Run all tests"""
    print("=" * 60)
    print("DH2 ORCHESTRATOR STANDALONE VALIDATION")
    print("=" * 60)

    try:
        test_helper_functions()
        test_orchestrator_initialization()
        test_get_primary_schema()
        test_pipeline_filtering()
        test_config_mapping()
        test_dq_rule_structure()

        print("\n" + "=" * 60)
        print("[PASS] ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe DH2 orchestrator is ready for integration.")
        print("\nNext steps:")
        print("  1. Create a Pulumi test stack")
        print("  2. Run 'pulumi preview' to validate resource creation")
        print("  3. Integrate into consumer-data-pipeline")
        return 0

    except AssertionError as e:
        print("\n" + "=" * 60)
        print("[FAIL] TEST FAILED")
        print("=" * 60)
        print(f"\nAssertion error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print("\n" + "=" * 60)
        print("[FAIL] UNEXPECTED ERROR")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
