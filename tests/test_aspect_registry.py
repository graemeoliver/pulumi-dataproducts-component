#!/usr/bin/env python3
"""
Test script for the Aspect Registry system.

Validates:
- ASPECT_REGISTRY structure
- AspectConfig objects
- Builder methods exist and are callable
- Aspect data structure and schema compliance
- Dynamic aspect building
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dataproduct import (
    DataProductWithAspects,
    DataProductArgs,
    ASPECT_REGISTRY,
    AspectConfig
)
import defaults


def test_aspect_registry_structure():
    """Test that ASPECT_REGISTRY is properly structured"""
    print("\n1. Testing ASPECT_REGISTRY structure...")
    print("-" * 60)

    assert isinstance(ASPECT_REGISTRY, list), "ASPECT_REGISTRY must be a list"
    assert len(ASPECT_REGISTRY) > 0, "ASPECT_REGISTRY cannot be empty"

    print(f"[OK] ASPECT_REGISTRY is a list with {len(ASPECT_REGISTRY)} aspects")

    # Check each AspectConfig
    for idx, aspect_config in enumerate(ASPECT_REGISTRY):
        assert isinstance(aspect_config, AspectConfig), \
            f"Item {idx} must be an AspectConfig instance"

        # Check required attributes
        assert hasattr(aspect_config, 'aspect_type_id'), \
            f"AspectConfig {idx} missing aspect_type_id"
        assert hasattr(aspect_config, 'builder_method'), \
            f"AspectConfig {idx} missing builder_method"
        assert hasattr(aspect_config, 'description'), \
            f"AspectConfig {idx} missing description"

        # Check values are non-empty strings
        assert isinstance(aspect_config.aspect_type_id, str) and aspect_config.aspect_type_id, \
            f"AspectConfig {idx} aspect_type_id must be non-empty string"
        assert isinstance(aspect_config.builder_method, str) and aspect_config.builder_method, \
            f"AspectConfig {idx} builder_method must be non-empty string"
        assert isinstance(aspect_config.description, str) and aspect_config.description, \
            f"AspectConfig {idx} description must be non-empty string"

        print(f"[OK] AspectConfig {idx}: {aspect_config.aspect_type_id} - {aspect_config.description}")

    print(f"[OK] All {len(ASPECT_REGISTRY)} AspectConfig objects are valid")


def test_aspect_type_ids():
    """Test that aspect type IDs match expected GCP format"""
    print("\n2. Testing aspect type IDs...")
    print("-" * 60)

    expected_aspects = [
        "business-context",
        "data-classification",
        "technical-ownership"
    ]

    actual_aspect_ids = [config.aspect_type_id for config in ASPECT_REGISTRY]

    for expected in expected_aspects:
        assert expected in actual_aspect_ids, \
            f"Expected aspect '{expected}' not found in ASPECT_REGISTRY"
        print(f"[OK] Found required aspect: {expected}")

    # Check format (should be kebab-case)
    for aspect_id in actual_aspect_ids:
        assert '-' in aspect_id or aspect_id.islower(), \
            f"Aspect ID '{aspect_id}' should use kebab-case format"

    print(f"[OK] All aspect IDs follow proper naming convention")


def test_builder_methods_exist():
    """Test that all builder methods referenced in the registry exist"""
    print("\n3. Testing builder methods exist...")
    print("-" * 60)

    # Create a mock instance to test method existence
    # We can't actually instantiate DataProductWithAspects without Pulumi context
    # So we check the class itself

    for aspect_config in ASPECT_REGISTRY:
        method_name = aspect_config.builder_method

        assert hasattr(DataProductWithAspects, method_name), \
            f"Builder method '{method_name}' not found on DataProductWithAspects class"

        method = getattr(DataProductWithAspects, method_name)
        assert callable(method), \
            f"Builder method '{method_name}' is not callable"

        print(f"[OK] Builder method exists and is callable: {method_name}")

    print(f"[OK] All {len(ASPECT_REGISTRY)} builder methods verified")


def test_builder_method_signatures():
    """Test that builder methods have correct signature"""
    print("\n4. Testing builder method signatures...")
    print("-" * 60)

    import inspect

    for aspect_config in ASPECT_REGISTRY:
        method = getattr(DataProductWithAspects, aspect_config.builder_method)
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())

        # Should have 'self' and 'args' parameters
        assert 'self' in params, \
            f"{aspect_config.builder_method} missing 'self' parameter"
        assert 'args' in params, \
            f"{aspect_config.builder_method} missing 'args' parameter"

        # Check return annotation if present
        if sig.return_annotation != inspect.Signature.empty:
            # Should return Dict[str, Any]
            print(f"[OK] {aspect_config.builder_method} has type hints")

        print(f"[OK] {aspect_config.builder_method} signature: {sig}")

    print(f"[OK] All builder method signatures are valid")


def test_aspect_data_structure():
    """Test that builder methods return valid aspect data"""
    print("\n5. Testing aspect data structure...")
    print("-" * 60)

    # Create test args
    test_args: DataProductArgs = {
        "dataProductId": "test-product",
        "project": "test-project",
        "location": "northamerica-northeast1",
        "displayName": "Test Product",
        "description": "Test description",
        "accessGroups": {},
        "businessDomain": "Engineering",
        "businessOwner": "owner@example.com",
        "businessPurpose": "Testing",
        "dataClassification": "internal",
        "retentionJustification": "Test retention",
        "technicalOwner": "tech@example.com",
        "technicalContact": "contact@example.com",
        "glossaryTerms": ["term1", "term2"],
        "containsPii": False
    }

    # Test each builder by calling it directly
    # We need to create a minimal mock object with _project_data
    class MockComponent:
        def __init__(self):
            class ProjectData:
                number = "123456789"
            self._project_data = ProjectData()

    mock = MockComponent()

    for aspect_config in ASPECT_REGISTRY:
        # Bind the method to our mock instance
        builder = getattr(DataProductWithAspects, aspect_config.builder_method)
        aspect_data = builder(mock, test_args)

        # Validate structure
        assert isinstance(aspect_data, dict), \
            f"{aspect_config.builder_method} must return a dict"

        assert len(aspect_data) > 0, \
            f"{aspect_config.builder_method} returned empty dict"

        # Check that data can be JSON serialized
        try:
            json_str = json.dumps(aspect_data)
            assert len(json_str) > 0
        except Exception as e:
            raise AssertionError(
                f"{aspect_config.builder_method} returned data that cannot be JSON serialized: {e}"
            )

        print(f"[OK] {aspect_config.builder_method} returns valid JSON-serializable dict")
        print(f"     Keys: {list(aspect_data.keys())}")

    print(f"[OK] All builder methods return valid aspect data")


def test_business_aspect_schema():
    """Test business-context aspect matches expected schema"""
    print("\n6. Testing business-context aspect schema...")
    print("-" * 60)

    test_args: DataProductArgs = {
        "dataProductId": "test",
        "project": "test-proj",
        "location": "us-central1",
        "displayName": "Test",
        "description": "Test",
        "accessGroups": {},
        "businessDomain": "Finance",
        "businessOwner": "owner@test.com",
        "businessPurpose": "Financial reporting",
        "dataClassification": "confidential",
        "retentionJustification": "Legal requirement",
        "technicalOwner": "tech@test.com",
        "technicalContact": "contact@test.com",
        "glossaryTerms": ["revenue", "expenses"]
    }

    class MockComponent:
        def __init__(self):
            class ProjectData:
                number = "999999"
            self._project_data = ProjectData()

    mock = MockComponent()
    builder = getattr(DataProductWithAspects, '_build_business_aspect_data')
    aspect_data = builder(mock, test_args)

    # Check required fields from GCP schema
    assert "business_domain" in aspect_data
    assert "business_owner" in aspect_data
    assert "business_purpose" in aspect_data

    # Check values
    assert aspect_data["business_domain"] == "Finance"
    assert aspect_data["business_owner"] == "owner@test.com"
    assert aspect_data["business_purpose"] == "Financial reporting"

    # Check optional fields
    assert "glossary_terms" in aspect_data
    assert aspect_data["glossary_terms"] == ["revenue", "expenses"]

    print("[OK] business-context aspect schema is correct")


def test_classification_aspect_schema():
    """Test data-classification aspect matches expected schema"""
    print("\n7. Testing data-classification aspect schema...")
    print("-" * 60)

    test_args: DataProductArgs = {
        "dataProductId": "test",
        "project": "test-proj",
        "location": "us-central1",
        "displayName": "Test",
        "description": "Test",
        "accessGroups": {},
        "businessDomain": "Test",
        "businessOwner": "owner@test.com",
        "businessPurpose": "Test",
        "dataClassification": "confidential",
        "retentionJustification": "Test",
        "technicalOwner": "tech@test.com",
        "technicalContact": "contact@test.com",
        "containsPii": True
    }

    class MockComponent:
        def __init__(self):
            class ProjectData:
                number = "999999"
            self._project_data = ProjectData()

    mock = MockComponent()
    builder = getattr(DataProductWithAspects, '_build_classification_aspect_data')
    aspect_data = builder(mock, test_args)

    # Check required fields from GCP schema (v0.0.22 - only these 2 fields)
    assert "classification_level" in aspect_data
    assert "contains_pii" in aspect_data

    # Verify no extra fields (schema was cleaned up in v0.0.22)
    assert len(aspect_data) == 2, \
        f"Expected exactly 2 fields, got {len(aspect_data)}: {list(aspect_data.keys())}"

    # Check values
    assert aspect_data["classification_level"] == "confidential"
    assert aspect_data["contains_pii"] is True

    print("[OK] data-classification aspect schema is correct (v0.0.22)")


def test_ownership_aspect_schema():
    """Test technical-ownership aspect matches expected schema"""
    print("\n8. Testing technical-ownership aspect schema...")
    print("-" * 60)

    test_args: DataProductArgs = {
        "dataProductId": "test",
        "project": "test-proj",
        "location": "us-central1",
        "displayName": "Test",
        "description": "Test",
        "accessGroups": {},
        "businessDomain": "Test",
        "businessOwner": "owner@test.com",
        "businessPurpose": "Test",
        "dataClassification": "internal",
        "retentionJustification": "Test",
        "technicalOwner": "tech-owner@test.com",
        "technicalContact": "tech-contact@test.com"
    }

    class MockComponent:
        def __init__(self):
            class ProjectData:
                number = "999999"
            self._project_data = ProjectData()

    mock = MockComponent()
    builder = getattr(DataProductWithAspects, '_build_ownership_aspect_data')
    aspect_data = builder(mock, test_args)

    # Check required fields from GCP schema (v0.0.22 - only these 2 fields)
    assert "technical_owner" in aspect_data
    assert "technical_contact" in aspect_data

    # Verify no extra fields (schema was cleaned up in v0.0.22)
    assert len(aspect_data) == 2, \
        f"Expected exactly 2 fields, got {len(aspect_data)}: {list(aspect_data.keys())}"

    # Check values
    assert aspect_data["technical_owner"] == "tech-owner@test.com"
    assert aspect_data["technical_contact"] == "tech-contact@test.com"

    print("[OK] technical-ownership aspect schema is correct (v0.0.22)")


def test_no_legacy_code():
    """Ensure legacy aspect code has been removed"""
    print("\n9. Testing for removed legacy code...")
    print("-" * 60)

    # These should NOT exist in the codebase anymore
    legacy_items = [
        'CentralizedAspectTypes',
        '_apply_mandatory_aspects',
        '_create_lineage_aspect',
        '_create_aspect',
        '_build_update_command'
    ]

    for item in legacy_items:
        assert not hasattr(DataProductWithAspects, item), \
            f"Legacy code still exists: {item} should have been removed"
        print(f"[OK] Confirmed removed: {item}")

    print("[OK] All legacy code has been removed")


def main():
    """Run all aspect registry tests"""
    print("=" * 60)
    print("ASPECT REGISTRY SYSTEM VALIDATION")
    print("=" * 60)

    try:
        test_aspect_registry_structure()
        test_aspect_type_ids()
        test_builder_methods_exist()
        test_builder_method_signatures()
        test_aspect_data_structure()
        test_business_aspect_schema()
        test_classification_aspect_schema()
        test_ownership_aspect_schema()
        test_no_legacy_code()

        print("\n" + "=" * 60)
        print("[PASS] ALL ASPECT REGISTRY TESTS PASSED!")
        print("=" * 60)
        print("\nThe aspect registry system is working correctly.")
        print(f"\nCurrent aspects in registry: {len(ASPECT_REGISTRY)}")
        for config in ASPECT_REGISTRY:
            print(f"  - {config.aspect_type_id}: {config.description}")
        print("\nTo add a new aspect, follow the 3-step process:")
        print("  1. Create AspectType in dataproducts-aspect-types/Pulumi.yaml")
        print("  2. Add AspectConfig to ASPECT_REGISTRY in dataproduct.py")
        print("  3. Create _build_<name>_aspect_data() method in dataproduct.py")
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
