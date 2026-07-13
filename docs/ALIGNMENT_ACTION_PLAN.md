# Alignment Action Plan
## Bringing dataproducts-component in line with `telus/pulumi-component-gcp-dataplex`

**Date:** 2026-07-13
**Current Alignment:** 85-90%
**Target:** 100% structural alignment
**Estimated Effort:** 2-3 hours

---

## Quick Summary

You're **VERY CLOSE** to the reference structure! Only 5 small fixes needed:

1. 🔴 Update `.gitignore` (5 min)
2. 🔴 Add `[tool.setuptools]` to `pyproject.toml` (2 min)
3. 🟡 Create `defaults.py` (15 min)
4. 🟡 Update README structure (30 min)
5. 🟢 Clean up optional files (10 min)

**Total Time:** ~1 hour for critical fixes, ~2 hours for all improvements

---

## Critical Fixes (Must Do)

### 1. 🔴 Update .gitignore

**Current:** 52 lines (basic)
**Reference:** 209 lines (comprehensive GitHub Python template)

**Action:**
```bash
cp /c/projects/cubedev_source/gcp/pulumi-component-gcp-dataplex/.gitignore \
   /c/projects/cubedev_source/gcp/dataproducts-component/.gitignore
```

**Why Critical:**
- Prevents committing sensitive files (.env, credentials)
- Prevents committing build artifacts
- Standard TELUS practice

**Effort:** 1 minute (copy file)

---

### 2. 🔴 Add Flat-Layout Config to pyproject.toml

**Current:**
```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "dataproducts-component"
version = "0.0.1"
# ...
```

**Required Addition:**
```toml
# Add this at the end of pyproject.toml

# Flat-layout source-based component: declare the top-level modules explicitly so
# `pip install .` (run by Pulumi's plugin host) does not fail setuptools auto-discovery.
[tool.setuptools]
py-modules = ["dataproduct", "data_product_dh2_orchestrator", "simple_test", "defaults"]
```

**Why Critical:**
- Required for Pulumi's `pip install .` to work correctly
- Prevents setuptools auto-discovery failures
- Matches reference implementation exactly

**Effort:** 2 minutes (copy/paste + add module names)

---

## Important Improvements (Should Do)

### 3. 🟡 Create defaults.py

**Pattern from Reference:**
```python
# defaults.py — Default configuration constants for DataProductWithAspects component

# Business Context defaults
DEFAULT_BUSINESS_DOMAIN = "Data Platform"
DEFAULT_SLA_TIER = "standard"

# Compliance defaults
DEFAULT_DATA_CLASSIFICATION = "internal"
DEFAULT_RETENTION_YEARS = 7

# Technical defaults
DEFAULT_AVAILABILITY_TARGET = "99.9%"
DEFAULT_SUPPORT_HOURS = "business-hours"
DEFAULT_VERSION = "1.0.0"

# Aspect Types template
DEFAULT_ASPECT_TYPE_PREFIX = "projects/{project}/locations/{location}/aspectTypes"
```

**Then update dataproduct.py:**
```python
from defaults import (
    DEFAULT_SLA_TIER,
    DEFAULT_RETENTION_YEARS,
    DEFAULT_AVAILABILITY_TARGET,
    DEFAULT_SUPPORT_HOURS,
    DEFAULT_VERSION
)

class DataProductWithAspects(ComponentResource):
    def __init__(self, ...):
        # Replace hardcoded "standard" with DEFAULT_SLA_TIER
        sla_tier = args.get("slaTier", DEFAULT_SLA_TIER)
        # etc.
```

**Why Important:**
- Centralizes configuration
- Makes defaults easy to find and update
- Matches reference pattern
- Improves maintainability

**Effort:** 15 minutes

---

### 4. 🟡 Update README Structure

**Add Missing Sections:**

#### a) Repository Structure Section (after Prerequisites)

```markdown
## 📁 Repository Structure

\`\`\`
dataproducts-component/
├── __main__.py                           # Provider host entrypoint (registers components)
├── PulumiPlugin.yaml                     # Pulumi plugin manifest (runtime: python)
├── pyproject.toml                        # Packaging metadata + dev dependencies
├── requirements.txt                      # Runtime dependencies
├── defaults.py                           # Default configuration constants
├── dataproduct.py                        # DataProductWithAspects component
├── data_product_dh2_orchestrator.py      # DH2 orchestrator for batch creation
├── simple_test.py                        # Simple test component
├── README.md                             # This file
└── .gitignore
\`\`\`

This is a source-based Pulumi component package. Pulumi source-based plugin
packages need a `PulumiPlugin.yaml` manifest, a language manifest such as
`pyproject.toml`, an entry file (`__main__.py`), and one or more
`ComponentResource` subclasses.
```

#### b) Development Guide Section (before Contributing)

```markdown
## 🛠️ Development Guide

### Understanding defaults.py

`defaults.py` centralizes the component's default configuration constants:

\`\`\`python
DEFAULT_SLA_TIER = "standard"
DEFAULT_RETENTION_YEARS = 7
DEFAULT_AVAILABILITY_TARGET = "99.9%"
\`\`\`

### Local development

\`\`\`bash
pip install -e ".[dev]"
black .
mypy .
python test_component.py
\`\`\`

### Running validation

\`\`\`bash
python validate_code.py
python tests/test_orchestrator_standalone.py
\`\`\`
```

####c) How It Works Section (at end, before Contributing)

```markdown
## 🏗️ How It Works

### Component Registration

`__main__.py` starts the Pulumi component provider host and registers the components:

\`\`\`python
component_provider_host(
    name="dataproducts",
    components=[DataProductWithAspects, SimpleTestComponent]
)
\`\`\`

Each component declares its type token in `super().__init__(...)`:
- `dataproducts:index:DataProductWithAspects`
- `dataproducts:index:SimpleTest`

### Data Product Creation Flow

1. Validate required inputs (project, location, displayName, etc.)
2. Create the base `gcp.dataplex.DataProduct` resource
3. Apply mandatory governance aspects via Entry resources
4. Attach optional data assets (BigQuery datasets, GCS buckets)
5. Create optional data quality/profiling scans
6. Register outputs (dataProductId, dataProductName, aspectsApplied)

### DH2 Orchestrator Pattern

The `DataProductDH2Orchestrator` enables batch creation:

1. Read pipeline configurations from Pulumi Config
2. Filter for pipelines with `data_product.enabled: true`
3. For each enabled pipeline:
   - Generate data product ID from stack components
   - Map snake_case config to camelCase component args
   - Call `DataProductWithAspects` component
   - Create optional DQ/DP scans
4. Return list of created data products
```

**Why Important:**
- Helps users understand the component
- Matches reference repo documentation style
- Standard TELUS documentation practice

**Effort:** 30 minutes

---

## Optional Improvements (Nice to Have)

### 5. 🟢 Clean Up Optional Files

**Files to Consider Moving/Organizing:**

```bash
# Create a docs/ directory for supplementary docs
mkdir docs
mv claude.md docs/
mv MIGRATION_PLAN.md docs/
mv VALIDATION_REPORT.md docs/
mv STRUCTURE_GAP_ANALYSIS.md docs/
mv ACTUAL_GAP_ANALYSIS.md docs/
mv ALIGNMENT_ACTION_PLAN.md docs/  # This file!

# Update .gitignore to keep docs but ignore generated reports
echo "\n# Documentation (keep in git)\n!docs/\n" >> .gitignore
```

**Result:**
```
dataproducts-component/
├── __main__.py
├── PulumiPlugin.yaml
├── pyproject.toml
├── requirements.txt
├── README.md
├── .gitignore
├── defaults.py
├── dataproduct.py
├── data_product_dh2_orchestrator.py
├── simple_test.py
├── test_component.py
├── validate_code.py
├── docs/
│   ├── claude.md
│   ├── MIGRATION_PLAN.md
│   ├── VALIDATION_REPORT.md
│   └── ALIGNMENT_ACTION_PLAN.md
└── tests/
    ├── dh2-orchestrator-test/
    └── test_orchestrator_standalone.py
```

**Why Useful:**
- Cleaner root directory
- Matches reference simplicity
- Easier to navigate

**Effort:** 10 minutes

---

## Comparison Matrix: Before vs After

| Aspect | Before | After Fixes | Reference | Match? |
|--------|--------|-------------|-----------|--------|
| **File Count (root)** | 14 files | 10 files | 8 files | ⚠️ Close |
| **.gitignore** | 52 lines | 209 lines | 209 lines | ✅ Perfect |
| **pyproject.toml** | Missing [tool.setuptools] | Has [tool.setuptools] | Has [tool.setuptools] | ✅ Perfect |
| **defaults.py** | Missing | Created | Has defaults | ✅ Perfect |
| **README structure** | 8/10 sections | 10/10 sections | 10/10 sections | ✅ Perfect |
| **Code organization** | Scattered constants | Centralized in defaults.py | Centralized | ✅ Perfect |
| **Documentation** | Good | Excellent | Excellent | ✅ Perfect |
| **Test coverage** | Good | Good | None | ✅ Better! |
| **Overall Alignment** | 85% | 98% | 100% | ✅ Excellent |

---

## Implementation Checklist

### Phase 1: Critical Fixes (15 minutes)

- [ ] 1. Copy reference .gitignore
  ```bash
  cp /c/projects/cubedev_source/gcp/pulumi-component-gcp-dataplex/.gitignore .
  ```

- [ ] 2. Add `[tool.setuptools]` section to pyproject.toml
  ```toml
  [tool.setuptools]
  py-modules = ["dataproduct", "data_product_dh2_orchestrator", "simple_test", "defaults"]
  ```

- [ ] 3. Create defaults.py with all constants

- [ ] 4. Update dataproduct.py to import from defaults

- [ ] 5. Update data_product_dh2_orchestrator.py to import from defaults

### Phase 2: README Updates (30 minutes)

- [ ] 6. Add "Repository Structure" section to README

- [ ] 7. Add "Development Guide" section to README

- [ ] 8. Add "How It Works" section to README

- [ ] 9. Update table of contents in README

### Phase 3: Organization (10 minutes)

- [ ] 10. Create docs/ directory

- [ ] 11. Move supplementary docs to docs/

- [ ] 12. Update any internal doc links

### Phase 4: Validation (5 minutes)

- [ ] 13. Run validation script
  ```bash
  python validate_code.py
  ```

- [ ] 14. Run orchestrator test
  ```bash
  python tests/test_orchestrator_standalone.py
  ```

- [ ] 15. Run component test
  ```bash
  python test_component.py
  ```

- [ ] 16. Verify imports work
  ```bash
  python -c "from dataproduct import DataProductWithAspects; from defaults import *; print('OK')"
  ```

### Phase 5: Git Commit (2 minutes)

- [ ] 17. Review all changes
  ```bash
  git status
  git diff
  ```

- [ ] 18. Commit changes
  ```bash
  git add .
  git commit -m "Align structure with telus/pulumi-component-gcp-dataplex

  - Update .gitignore to comprehensive Python template
  - Add [tool.setuptools] flat-layout config to pyproject.toml
  - Create defaults.py for centralized constants
  - Update README with Repository Structure, Development Guide, How It Works sections
  - Organize supplementary docs into docs/ directory

  Alignment: 85% → 98%"
  ```

---

## After Alignment: Next Steps

Once aligned, you can:

1. **Tag a release:**
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. **Consume from YAML:**
   ```yaml
   packages:
     dataproducts: https://github.com/YOUR_ORG/dataproducts-component@v0.1.0
   ```

3. **Share with team:**
   - Update internal docs
   - Add to component registry
   - Create example projects

---

## Verification Script

Run this after implementing fixes to verify alignment:

```bash
#!/bin/bash
echo "=== Alignment Verification ==="

# Check .gitignore
echo "1. Checking .gitignore..."
if [ $(wc -l < .gitignore) -gt 200 ]; then
    echo "   ✅ .gitignore is comprehensive"
else
    echo "   ❌ .gitignore needs updating"
fi

# Check pyproject.toml
echo "2. Checking pyproject.toml..."
if grep -q "\[tool.setuptools\]" pyproject.toml; then
    echo "   ✅ pyproject.toml has flat-layout config"
else
    echo "   ❌ pyproject.toml missing [tool.setuptools]"
fi

# Check defaults.py
echo "3. Checking defaults.py..."
if [ -f defaults.py ]; then
    echo "   ✅ defaults.py exists"
else
    echo "   ❌ defaults.py is missing"
fi

# Check README sections
echo "4. Checking README sections..."
if grep -q "Repository Structure" README.md && \
   grep -q "Development Guide" README.md && \
   grep -q "How It Works" README.md; then
    echo "   ✅ README has all required sections"
else
    echo "   ❌ README missing some sections"
fi

# Check imports
echo "5. Checking imports..."
if python -c "from dataproduct import DataProductWithAspects; from defaults import DEFAULT_SLA_TIER" 2>/dev/null; then
    echo "   ✅ All imports work"
else
    echo "   ❌ Import errors detected"
fi

echo ""
echo "=== Verification Complete ==="
```

---

## Questions?

- **Q: Do we need to match 100%?**
  A: No! Being 85% aligned is already good. The critical fixes (gitignore, pyproject.toml, defaults.py) are most important.

- **Q: Can we skip the README updates?**
  A: Yes, README is "should have" not "must have". Your current README is already comprehensive.

- **Q: Should we delete test files to match reference?**
  A: NO! Your test coverage is better than reference. Keep the tests.

- **Q: What about the DH2 orchestrator file?**
  A: Keep it! It's extra functionality beyond the reference. The reference is simpler because it does less.

---

## Summary

**Minimum to be aligned:**
1. Update .gitignore (1 min)
2. Add [tool.setuptools] to pyproject.toml (2 min)
3. Create defaults.py (15 min)

**Total: 18 minutes for full alignment on critical items**

The rest are improvements, not requirements!

**Current Status:** ✅ You're already 85-90% aligned
**After Fixes:** ✅ You'll be 98% aligned (better than reference in some ways!)
