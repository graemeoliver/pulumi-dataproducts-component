#!/usr/bin/env python3
"""
Comprehensive validation script for the dataproducts component.

Checks for:
- Code quality issues
- Potential runtime errors
- Configuration problems
- Best practices
"""

import sys
import os
from typing import List, Tuple

# Add parent directory to path to import component modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def check_dataproduct_module() -> List[Tuple[str, str]]:
    """Validate dataproduct.py for common issues"""
    issues = []

    try:
        from dataproduct import DataProductWithAspects, DataProductArgs, ASPECT_REGISTRY, AspectConfig

        # Check ASPECT_REGISTRY is properly defined
        if not isinstance(ASPECT_REGISTRY, list):
            issues.append(('ERROR', 'ASPECT_REGISTRY must be a list'))
        elif len(ASPECT_REGISTRY) == 0:
            issues.append(('ERROR', 'ASPECT_REGISTRY is empty'))
        else:
            print(f"[OK] dataproduct.py: ASPECT_REGISTRY defined with {len(ASPECT_REGISTRY)} aspects")

            # Check each AspectConfig
            for idx, aspect_config in enumerate(ASPECT_REGISTRY):
                if not isinstance(aspect_config, AspectConfig):
                    issues.append(('ERROR', f'ASPECT_REGISTRY[{idx}] is not an AspectConfig instance'))
                else:
                    # Check required attributes
                    if not hasattr(aspect_config, 'aspect_type_id'):
                        issues.append(('ERROR', f'AspectConfig {idx} missing aspect_type_id'))
                    if not hasattr(aspect_config, 'builder_method'):
                        issues.append(('ERROR', f'AspectConfig {idx} missing builder_method'))

                    # Check builder method exists
                    if hasattr(aspect_config, 'builder_method'):
                        if not hasattr(DataProductWithAspects, aspect_config.builder_method):
                            issues.append(('ERROR', f'Builder method not found: {aspect_config.builder_method}'))
                        else:
                            print(f"[OK] dataproduct.py: Aspect '{aspect_config.aspect_type_id}' -> {aspect_config.builder_method}")

        # Check DataProductArgs has required fields
        required_annotations = [
            'dataProductId', 'location', 'project', 'displayName', 'description',
            'accessGroups', 'businessDomain', 'businessOwner', 'businessPurpose',
            'dataClassification', 'retentionJustification', 'technicalOwner', 'technicalContact'
        ]

        if hasattr(DataProductArgs, '__annotations__'):
            annotations = DataProductArgs.__annotations__
            for field in required_annotations:
                if field not in annotations:
                    issues.append(('ERROR', f'Missing required field in DataProductArgs: {field}'))

        print("[OK] dataproduct.py: All required fields present in DataProductArgs")

        # Check that legacy code has been removed
        legacy_items = ['CentralizedAspectTypes', '_apply_mandatory_aspects', '_create_aspect']
        for item in legacy_items:
            # Check class attributes
            if hasattr(DataProductWithAspects, item):
                issues.append(('WARNING', f'Legacy code still present: {item}'))

    except ImportError as e:
        issues.append(('ERROR', f'Failed to import dataproduct: {e}'))
    except Exception as e:
        issues.append(('ERROR', f'Unexpected error in dataproduct validation: {e}'))

    return issues


def check_orchestrator_module() -> List[Tuple[str, str]]:
    """Validate data_product_dh2_orchestrator.py for common issues"""
    issues = []

    try:
        from data_product_dh2_orchestrator import DataProductDH2Orchestrator

        # Check required methods exist
        required_methods = ['__init__', 'run', '_create_data_product', '_create_dq_scan', '_create_dp_scan']

        for method in required_methods:
            if not hasattr(DataProductDH2Orchestrator, method):
                issues.append(('ERROR', f'Missing required method: {method}'))

        print("[OK] data_product_dh2_orchestrator.py: All required methods present")

        # Check constructor signature
        init_params = DataProductDH2Orchestrator.__init__.__code__.co_varnames
        expected_params = ['self', 'stack_prefix', 'consumer', 'group', 'lake_project_id', 'location', 'pipelines']

        for param in expected_params:
            if param not in init_params:
                issues.append(('WARNING', f'Missing expected parameter in __init__: {param}'))

        print("[OK] data_product_dh2_orchestrator.py: Constructor signature validated")

    except ImportError as e:
        issues.append(('ERROR', f'Failed to import orchestrator: {e}'))
    except Exception as e:
        issues.append(('ERROR', f'Unexpected error in orchestrator validation: {e}'))

    return issues


def check_git_status() -> List[Tuple[str, str]]:
    """Check git repository status"""
    import subprocess
    issues = []

    try:
        result = subprocess.run(['git', 'status', '--porcelain'],
                              capture_output=True, text=True, check=True)

        if result.stdout.strip():
            issues.append(('INFO', 'There are uncommitted changes'))
            print("[INFO] Git: Uncommitted changes detected")
        else:
            print("[OK] Git: Working tree is clean")

    except subprocess.CalledProcessError:
        issues.append(('WARNING', 'Not a git repository or git not available'))
    except Exception as e:
        issues.append(('WARNING', f'Could not check git status: {e}'))

    return issues


def check_file_structure() -> List[Tuple[str, str]]:
    """Check if all expected files are present"""
    import os
    issues = []

    # Check from parent directory (component root)
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    expected_files = [
        'dataproduct.py',
        'data_product_dh2_orchestrator.py',
        '__main__.py',
        'simple_test.py',
        'defaults.py',
        'requirements.txt',
        'pyproject.toml',
        'PulumiPlugin.yaml',
        'README.md',
        '.gitignore'
    ]

    for file in expected_files:
        file_path = os.path.join(parent_dir, file)
        if not os.path.exists(file_path):
            issues.append(('WARNING', f'Expected file not found: {file}'))
        else:
            print(f"[OK] File exists: {file}")

    return issues


def validate_dq_rule_types() -> List[Tuple[str, str]]:
    """Validate that all DQ rule types from docs are supported"""
    import os
    issues = []

    # Read the orchestrator file from parent directory
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    orchestrator_file = os.path.join(parent_dir, 'data_product_dh2_orchestrator.py')

    try:
        with open(orchestrator_file, 'r') as f:
            content = f.read()

        expected_rules = [
            'non_null_expectation',
            'uniqueness_expectation',
            'set_expectation',
            'range_expectation',
            'regex_expectation',
            'row_condition_expectation',
            'table_condition_expectation',
            'sql_assertion',
            'statistic_range_expectation'
        ]

        for rule in expected_rules:
            if rule not in content:
                issues.append(('WARNING', f'DQ rule type may not be supported: {rule}'))
            else:
                print(f"[OK] DQ rule type supported: {rule}")

    except Exception as e:
        issues.append(('ERROR', f'Failed to validate DQ rules: {e}'))

    return issues


def main():
    """Run all validation checks"""
    print("=" * 60)
    print("DATAPRODUCTS COMPONENT VALIDATION")
    print("=" * 60)
    print()

    all_issues = []

    print("1. Checking file structure...")
    print("-" * 60)
    all_issues.extend(check_file_structure())
    print()

    print("2. Validating dataproduct.py module...")
    print("-" * 60)
    all_issues.extend(check_dataproduct_module())
    print()

    print("3. Validating data_product_dh2_orchestrator.py module...")
    print("-" * 60)
    all_issues.extend(check_orchestrator_module())
    print()

    print("4. Validating DQ rule types...")
    print("-" * 60)
    all_issues.extend(validate_dq_rule_types())
    print()

    print("5. Checking git status...")
    print("-" * 60)
    all_issues.extend(check_git_status())
    print()

    # Print summary
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    errors = [i for i in all_issues if i[0] == 'ERROR']
    warnings = [i for i in all_issues if i[0] == 'WARNING']
    infos = [i for i in all_issues if i[0] == 'INFO']

    if errors:
        print(f"\n[!] ERRORS ({len(errors)}):")
        for _, msg in errors:
            print(f"  - {msg}")

    if warnings:
        print(f"\n[!] WARNINGS ({len(warnings)}):")
        for _, msg in warnings:
            print(f"  - {msg}")

    if infos:
        print(f"\n[i] INFO ({len(infos)}):")
        for _, msg in infos:
            print(f"  - {msg}")

    if not all_issues:
        print("\n[PASS] ALL CHECKS PASSED!")
        print("The component appears to be in good shape.")
    elif not errors:
        print("\n[PASS] NO CRITICAL ERRORS")
        print("The component should work, but consider addressing warnings.")
    else:
        print("\n[FAIL] VALIDATION FAILED")
        print("Please fix the errors above before deploying.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
