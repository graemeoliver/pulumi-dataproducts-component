# Actual Gap Analysis
## Comparison with `telus/pulumi-component-gcp-dataplex`

**Reference:** `/c/projects/cubedev_source/gcp/pulumi-component-gcp-dataplex`
**Current:** `/c/projects/cubedev_source/gcp/dataproducts-component`
**Date:** 2026-07-13

---

## Executive Summary

**Good News!** Your component is actually **VERY CLOSE** to the reference structure. The reference repo uses a **flat layout** (not the complex provider/sdk/ structure I initially assumed). You're approximately **85-90% aligned** already.

---

## Reference Repository Structure (ACTUAL)

```
pulumi-component-gcp-dataplex/
├── .gitignore                    # Standard Python gitignore
├── __main__.py                   # Component provider host (6 lines)
├── PulumiPlugin.yaml             # runtime: python
├── pyproject.toml                # Package metadata + flat-layout config
├── requirements.txt              # Dependencies
├── README.md                     # Comprehensive usage guide
├── dataplex_scan.py              # Main component (295 lines)
└── defaults.py                   # Constants (4 lines)

Total: 8 files, ~300 lines of code
```

---

## Your Current Structure

```
dataproducts-component/
├── .git/
├── .gitignore
├── __main__.py                   # Component provider host
├── PulumiPlugin.yaml
├── pyproject.toml
├── requirements.txt
├── README.md
├── dataproduct.py                # Main component (651 lines)
├── data_product_dh2_orchestrator.py  # Orchestrator (510 lines)
├── simple_test.py                # Simple test component
├── test_component.py             # Unit test
├── validate_code.py              # Validation script
├── VALIDATION_REPORT.md
├── MIGRATION_PLAN.md
├── claude.md
└── tests/
    ├── dh2-orchestrator-test/
    └── test_orchestrator_standalone.py

Total: ~15 files, ~1200 lines of component code
```

---

## Side-by-Side File Comparison

| File | Reference | Your Component | Match? | Notes |
|------|-----------|----------------|--------|-------|
| `.gitignore` | ✅ 210 lines | ✅ Present | ⚠️ | Need to verify completeness |
| `__main__.py` | ✅ 6 lines | ✅ 14 lines | ✅ | Functionally identical |
| `PulumiPlugin.yaml` | ✅ `runtime: python` | ✅ `runtime: python` | ✅ | Perfect match |
| `pyproject.toml` | ✅ With flat-layout | ✅ Basic | ⚠️ | Missing flat-layout config |
| `requirements.txt` | ✅ 2 lines | ✅ 2 lines | ✅ | Identical deps |
| `README.md` | ✅ 277 lines | ✅ 307 lines | ✅ | Both comprehensive |
| Component file | ✅ `dataplex_scan.py` | ✅ `dataproduct.py` | ✅ | Different functionality |
| Constants file | ✅ `defaults.py` | ❌ Missing | 🔴 | Should extract constants |
| `simple_test.py` | ❌ None | ✅ Present | ℹ️ | Extra (good for testing) |
| Test files | ❌ None | ✅ 2 test files | ℹ️ | Extra (good practice) |
| Docs | ❌ None | ✅ 3 MD files | ℹ️ | Extra (thorough) |

---

## Key Patterns from Reference

### 1. ✅ Flat Layout (MATCHES)

Both repos use a flat structure:
- No `provider/` directory
- No `sdk/` directory
- No `examples/` directory
- All code in root

**Your Status:** ✅ Already matches

---

### 2. ⚠️ pyproject.toml - Flat Layout Declaration

**Reference:**
```toml
[tool.setuptools]
py-modules = ["dataplex_scan", "defaults"]
```

**Your Current:**
```toml
# Missing this section!
```

**Impact:** Pulumi's `pip install .` may fail auto-discovery

**Fix Required:** Add `[tool.setuptools]` section

---

### 3. ⚠️ Minimal __main__.py

**Reference:**
```python
from pulumi.provider.experimental import component_provider_host
from dataplex_scan import DatasetDatascanSet

if __name__ == "__main__":
    component_provider_host(name="gcpcomponents", components=[DatasetDatascanSet])
```

**Your Current:**
```python
from pulumi.provider.experimental import component_provider_host
from dataproduct import DataProductWithAspects
from simple_test import SimpleTestComponent

if __name__ == "__main__":
    component_provider_host(
        name="dataproducts",
        components=[DataProductWithAspects, SimpleTestComponent]
    )
```

**Difference:** You register 2 components, reference registers 1

**Status:** ✅ Fine - extra component for testing is reasonable

---

### 4. ❌ Missing defaults.py

**Reference Pattern:**
```python
# defaults.py
DEFAULT_TABLE_LABEL = "data-quality"
```

**Your Current:** Constants scattered in code

**Recommendation:** Extract constants to `defaults.py`:
```python
# defaults.py
DEFAULT_SLA_TIER = "standard"
DEFAULT_RETENTION_YEARS = 7
DEFAULT_AVAILABILITY_TARGET = "99.9%"
DEFAULT_SUPPORT_HOURS = "business-hours"
DEFAULT_VERSION = "1.0.0"
```

---

### 5. ✅ TypedDict Usage

**Reference:** Extensive TypedDict definitions for schema validation

**Your Current:** Already using TypedDict in `DataProductArgs`

**Status:** ✅ Excellent match

---

### 6. ✅ Component Registration Pattern

**Reference:**
```python
super().__init__("gcpcomponents:index:DatasetDatascanSet", name, args, opts)
```

**Your Current:**
```python
super().__init__('dataproducts:index:DataProductWithAspects', name, {}, opts)
```

**Status:** ✅ Correct pattern

---

### 7. ⚠️ README Structure

**Reference README Sections:**
1. Title & Description
2. Prerequisites
3. Repository Structure (shows file tree!)
4. Component Overview
5. Component Inputs/Outputs
6. Usage Examples (minimal + full)
7. Deployment instructions
8. Required GCP Permissions
9. Development Guide
10. How It Works

**Your README:** Has most of these, missing:
- ❌ Repository Structure section with file tree
- ❌ Development Guide section
- ❌ How It Works section

---

### 8. ✅ .gitignore Completeness

**Reference:** Comprehensive 210-line .gitignore from GitHub Python template

**Your Current:** Need to verify

Let me check:
