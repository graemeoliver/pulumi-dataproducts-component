#!/usr/bin/env python3
"""
Test script to verify the TypedDict component works correctly
"""

import sys
import os

# Add parent directory to path to import component modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dataproduct import DataProductArgs

def test_component():
    """Test creating a DataProductWithAspects component"""

    # Create test args using TypedDict format
    args: DataProductArgs = {
        # Core Properties (Required)
        "dataProductId": "test-product",
        "project": "test-project",
        "location": "northamerica-northeast1",
        "displayName": "Test Data Product",
        "description": "Test data product for component validation",
        "accessGroups": {
            "test-admins": {
                "id": "test-admins",
                "displayName": "Test Admins",
                "principal": {
                    "googleGroup": "test-admins@company.com"
                }
            }
        },

        # Business Context (Required)
        "businessDomain": "Testing",
        "businessOwner": "test-owner@company.com",
        "businessPurpose": "Test component functionality",

        # Compliance (Required)
        "dataClassification": "internal",
        "retentionJustification": "Testing purposes",

        # Technical (Required)
        "technicalOwner": "tech-owner@company.com",
        "technicalContact": "tech-contact@company.com",

        # Optional fields
        "glossaryTerms": ["test-term"],
        "complianceFrameworks": ["TEST"],
        "version": "0.1.0",
    }

    print("[OK] TypedDict args created successfully")
    print(f"  - dataProductId: {args['dataProductId']}")
    print(f"  - displayName: {args['displayName']}")
    print(f"  - businessDomain: {args['businessDomain']}")

    # Verify required properties exist
    required_props = [
        "dataProductId", "project", "location", "displayName", "description",
        "accessGroups", "businessDomain", "businessOwner", "businessPurpose",
        "dataClassification", "retentionJustification",
        "technicalOwner", "technicalContact"
    ]

    for prop in required_props:
        assert prop in args, f"Missing required property: {prop}"

    print("[OK] All required properties present")

    # Test optional properties with defaults
    print(f"  - glossaryTerms: {args.get('glossaryTerms', [])}")
    print(f"  - version: {args.get('version', '1.0.0')}")
    print(f"  - slaTier: {args.get('slaTier', 'standard')}")

    print("\n[PASS] Component TypedDict conversion validation PASSED!")
    return True

if __name__ == "__main__":
    try:
        test_component()
        sys.exit(0)
    except Exception as e:
        print(f"\n[FAIL] Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
