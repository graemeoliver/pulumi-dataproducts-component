# DataProducts Component Tests

This directory contains test scripts for the DataProductWithAspects component and the DH2 orchestrator.

## Test Files

### Core Component Tests

#### `test_aspect_registry.py` ⭐ **NEW**
**Purpose**: Comprehensive validation of the Aspect Registry system (v0.0.22+)

**What it tests**:
- ASPECT_REGISTRY structure and validity
- AspectConfig objects are properly configured
- Builder methods exist and have correct signatures
- Aspect data structures match GCP schemas
- Schema compliance for each aspect type
- Legacy code has been removed

**Run**: `python tests/test_aspect_registry.py`

**Expected output**: All 9 test sections should pass, validating:
1. Registry structure (3 aspects currently)
2. Aspect type IDs (kebab-case format)
3. Builder methods exist
4. Method signatures (self, args) -> Dict[str, Any]
5. Aspect data is JSON-serializable
6. business-context schema (4 fields)
7. data-classification schema (2 fields - v0.0.22 cleaned up)
8. technical-ownership schema (2 fields - v0.0.22 cleaned up)
9. Legacy code removal verification

---

#### `validate_code.py` ✅ **UPDATED**
**Purpose**: Comprehensive validation of component code quality

**What it tests**:
- File structure (all required files present)
- dataproduct.py module:
  - ASPECT_REGISTRY is properly defined ✨ (updated for v0.0.22)
  - AspectConfig objects are valid ✨ (updated for v0.0.22)
  - Builder methods exist ✨ (updated for v0.0.22)
  - DataProductArgs has all required fields
  - Legacy code has been removed ✨ (updated for v0.0.22)
- data_product_dh2_orchestrator.py module
- DQ rule types support
- Git status

**Run**: `python tests/validate_code.py`

**Changes from previous versions**:
- Removed `CentralizedAspectTypes` checks
- Added `ASPECT_REGISTRY` validation
- Added `AspectConfig` validation
- Added legacy code detection

---

#### `test_component.py`
**Purpose**: Basic TypedDict argument validation

**What it tests**:
- Creating DataProductArgs with all required fields
- TypedDict structure is correct
- Optional fields with defaults

**Run**: `python tests/test_component.py`

---

### DH2 Orchestrator Tests

#### `test_orchestrator_standalone.py`
**Purpose**: Standalone validation of DH2 orchestrator logic (no Pulumi context needed)

**What it tests**:
- Helper functions (_slugify, _make_data_product_id, _make_bq_dataset_id)
- Orchestrator initialization
- Schema extraction (_get_primary_schema)
- Pipeline filtering logic
- Configuration mapping (snake_case → camelCase)
- Data quality rule structure

**Run**: `python tests/test_orchestrator_standalone.py`

**Note**: This test is for the DH2 orchestrator component, which is separate from the main DataProductWithAspects component.

---

#### `dh2-orchestrator-test/`
**Purpose**: Full integration test stack for DH2 orchestrator

**Contents**:
- `Pulumi.yaml`: Stack configuration
- `Pulumi.test.yaml`: Test configuration with sample pipelines
- `__main__.py`: Python program that uses the orchestrator
- `requirements.txt`: Python dependencies

**Run**:
```bash
cd tests/dh2-orchestrator-test
pulumi preview
```

---

## Running All Tests

To run all component tests sequentially:

```bash
cd /c/projects/cubedev_source/gcp/dataproducts-component

# Core component tests
python tests/test_aspect_registry.py
python tests/validate_code.py
python tests/test_component.py

# DH2 orchestrator tests
python tests/test_orchestrator_standalone.py
```

## Test Coverage

### Aspect Registry System (v0.0.22+)
✅ ASPECT_REGISTRY structure
✅ AspectConfig validation
✅ Builder method existence
✅ Builder method signatures
✅ Aspect data JSON serialization
✅ Schema compliance (business-context)
✅ Schema compliance (data-classification)
✅ Schema compliance (technical-ownership)
✅ Legacy code removal

### Component Arguments
✅ DataProductArgs TypedDict structure
✅ Required field validation
✅ Optional field defaults

### Code Quality
✅ File structure validation
✅ Module import checks
✅ DQ rule type support

### DH2 Orchestrator
✅ Helper function logic
✅ Initialization
✅ Schema extraction
✅ Pipeline filtering
✅ Configuration mapping
✅ DQ rule structure

## Adding Tests for New Aspects

When you add a new aspect to ASPECT_REGISTRY, add a test to `test_aspect_registry.py`:

```python
def test_<aspect_name>_aspect_schema():
    """Test <aspect-name> aspect matches expected schema"""
    print("\nN. Testing <aspect-name> aspect schema...")
    print("-" * 60)

    test_args: DataProductArgs = {
        # ... required fields ...
        # ... your aspect-specific fields ...
    }

    class MockComponent:
        def __init__(self):
            class ProjectData:
                number = "999999"
            self._project_data = ProjectData()

    mock = MockComponent()
    builder = getattr(DataProductWithAspects, '_build_<aspect_name>_aspect_data')
    aspect_data = builder(mock, test_args)

    # Check required fields from GCP schema
    assert "field1" in aspect_data
    assert "field2" in aspect_data

    # Verify field count (prevents schema drift)
    assert len(aspect_data) == 2, \
        f"Expected exactly 2 fields, got {len(aspect_data)}: {list(aspect_data.keys())}"

    print("[OK] <aspect-name> aspect schema is correct")
```

Then add it to the `main()` function call list.

## Continuous Integration

These tests can be run in CI/CD pipelines before deployment:

```bash
#!/bin/bash
# Run all tests and exit with non-zero on failure

set -e  # Exit on first failure

echo "Running aspect registry tests..."
python tests/test_aspect_registry.py

echo "Running code validation..."
python tests/validate_code.py

echo "Running component tests..."
python tests/test_component.py

echo "Running orchestrator tests..."
python tests/test_orchestrator_standalone.py

echo "All tests passed!"
```

## Test Data

Test files use these standard test values:
- **Project**: `test-project`, `test-proj`
- **Location**: `northamerica-northeast1`, `us-central1`
- **DataProduct ID**: `test-product`, `test-data-product-001`
- **Business Domain**: `Engineering`, `Finance`, `Test`
- **Classification**: `internal`, `confidential`
- **Emails**: `owner@example.com`, `tech@example.com`, `contact@example.com`

## Troubleshooting

### Import Errors
If you get import errors, ensure you're running from the component root:
```bash
cd /c/projects/cubedev_source/gcp/dataproducts-component
python tests/test_aspect_registry.py
```

### Missing Aspects
If `test_aspect_registry.py` fails with "Expected aspect 'X' not found", check that:
1. The aspect exists in ASPECT_REGISTRY in dataproduct.py
2. The aspect_type_id matches exactly (case-sensitive)

### Builder Method Not Found
If you get "Builder method not found", check that:
1. The method exists in the DataProductWithAspects class
2. The method name in AspectConfig matches exactly
3. The method has the correct signature: `(self, args: DataProductArgs) -> Dict[str, Any]`

## Version History

### v0.0.22 (Current)
- ✨ Added `test_aspect_registry.py` for aspect registry validation
- ✅ Updated `validate_code.py` to test aspect registry instead of CentralizedAspectTypes
- 🧹 Removed tests for legacy `CentralizedAspectTypes`
- ✅ Added schema compliance tests for cleaned-up aspects

### v0.0.21 and earlier
- Used `CentralizedAspectTypes` for aspect management
- Had additional fields in aspects that were removed in v0.0.22
