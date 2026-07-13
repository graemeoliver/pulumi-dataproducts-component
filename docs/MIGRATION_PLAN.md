# Migration Plan: From Multi-Language Component to Python Orchestrator

## Executive Summary

We need to **fundamentally restructure** the current implementation. What we've built is a **multi-language Pulumi component** (consumable from YAML via `component_provider_host`). What's needed is a **Python-only orchestrator class** that runs during regular `pulumi up` operations.

---

## Current State vs. Target State

### What We Built (Current)

**Architecture**: Multi-language Pulumi Component
- TypedDict-based `DataProductArgs` for schema auto-generation
- `component_provider_host` for cross-language support
- Consumable from YAML via `packages:` reference
- Standalone component with its own inputs/outputs
- Published to GitHub for reuse
- Creates Dataplex Data Products with 8 mandatory governance aspects

**Structure**:
```
dataproducts-component/
├── __main__.py              # component_provider_host entry point
├── dataproduct.py           # DataProductWithAspects ComponentResource
├── simple_test.py           # Test component
├── PulumiPlugin.yaml        # Plugin metadata
├── pyproject.toml           # Package definition
└── requirements.txt
```

**Usage** (from YAML):
```yaml
packages:
  dataproducts: https://github.com/graemeoliver/pulumi-dataproducts-component@v0.0.2

resources:
  myProduct:
    type: dataproducts:index:DataProductWithAspects
    properties:
      dataProductId: my-product
      project: my-project
      # ... 20+ properties
```

---

### What's Needed (Target)

**Architecture**: Python Orchestrator Pattern
- Regular Python class (NOT a ComponentResource)
- No multi-language support (Python-only)
- Reads config from `Pulumi.Config("pipeline")`
- Runs during existing `pulumi up` workflow
- Imported directly in Python program
- Creates Dataplex Data Products + optional Data Quality/Profiling scans

**Structure**:
```
dataplex-data-product-test/
├── Pulumi.yaml                          # Stack definition
├── Pulumi.dev-ne1-01-una-group1.yaml   # Config file
├── pyproject.toml                       # Dependencies
├── __main__.py                          # Test harness
└── data_product.py                      # DataProductOrchestrator class
```

**Usage** (from Python):
```python
orchestrator = DataProductOrchestrator(
    stack_prefix=stack_prefix,
    consumer=consumer_name,
    group=group_name,
    lake_project_id=lake_project_id,
    location=location,
    pipelines=pipelines,  # Dict from config
)
orchestrator.run()  # Iterates and creates resources
```

---

## Key Architectural Differences

| Aspect | Current (Component) | Target (Orchestrator) |
|--------|---------------------|----------------------|
| **Pattern** | Pulumi ComponentResource | Regular Python class |
| **Language Support** | Multi-language (YAML, TS, Python) | Python-only |
| **Distribution** | GitHub package reference | Direct file import |
| **Configuration** | TypedDict properties | Dict from Pulumi Config |
| **Invocation** | Via Pulumi YAML `resources:` | Direct Python class instantiation |
| **Resources Created** | 1 Data Product + 8 Aspects | 1 Data Product + optional DQ/DP scans |
| **Iteration** | Single resource per invocation | Iterates over multiple pipelines |
| **Entry Point** | `component_provider_host()` | `orchestrator.run()` |
| **Integration** | Standalone package | Part of main program |

---

## What Needs to Change

### 1. **Completely New Project Structure**

#### DELETE (not needed):
- ❌ `__main__.py` with `component_provider_host`
- ❌ `PulumiPlugin.yaml`
- ❌ `simple_test.py`
- ❌ TypedDict-based `DataProductArgs`
- ❌ `ComponentResource` inheritance
- ❌ All multi-language support code

#### CREATE (new files):
- ✅ `dataplex-data-product-test/` directory
- ✅ New `__main__.py` (test harness, NOT component host)
- ✅ New `data_product.py` (orchestrator class)
- ✅ `Pulumi.dev-ne1-01-una-group1.yaml` (config file)
- ✅ Updated `pyproject.toml` (exact Pulumi versions)

### 2. **Config Loading Strategy**

#### Current Approach:
```python
# Component receives TypedDict props from YAML
class DataProductWithAspects(ComponentResource):
    def __init__(self, name: str, args: DataProductArgs, ...):
        # args["dataProductId"], args["project"], etc.
```

#### Target Approach:
```python
# Orchestrator reads from Pulumi Config
config = pulumi.Config("pipeline")
pipelines = config.get_object("pipelines") or {}

# Iterates over pipelines dict
for pipeline_name, pipeline_cfg in pipelines.items():
    dp_cfg = pipeline_cfg.get("data_product", {})
    if dp_cfg.get("enabled"):
        self._create_data_product(pipeline_name, dp_cfg)
```

### 3. **Resource Creation Pattern**

#### Current (Component):
```python
class DataProductWithAspects(ComponentResource):
    def __init__(self, ...):
        super().__init__('dataproducts:index:DataProductWithAspects', name, {}, opts)

        # Creates 1 product + 8 aspects
        self.data_product = gcp.dataplex.DataProduct(...)
        self.aspects = self._apply_mandatory_aspects(...)

        self.register_outputs({...})
```

#### Target (Orchestrator):
```python
class DataProductOrchestrator:
    def run(self) -> list[gcp.dataplex.DataProduct]:
        created = []

        # Iterates over all pipelines
        for pipeline_name, pipeline_cfg in self.pipelines.items():
            if pipeline_cfg.get("data_product", {}).get("enabled"):
                product = self._create_data_product(...)
                created.append(product)

                # Optional scans
                if data_quality enabled:
                    self._create_dq_scan(...)
                if data_profiling enabled:
                    self._create_dp_scan(...)

        return created
```

### 4. **Naming Conventions**

#### Current:
- Properties use camelCase (`dataProductId`, `displayName`)
- Aspect-focused naming
- Component-centric IDs

#### Target:
- Config uses snake_case (`data_product_id`, `display_name`)
- Pipeline-focused naming
- Follows strict naming formula:
  ```python
  data_product_id = f"{stack_prefix}_{consumer}_{group}_{pipeline}"
  # e.g., "dev_ne1_01_una_group_01_customer_sync"
  ```

### 5. **Mandatory vs. Optional Features**

#### Current (Aspects-focused):
- 8 **mandatory** governance aspects
- Optional data assets (BQ datasets, GCS buckets)
- Optional data quality scans
- Optional monitoring

#### Target (Scans-focused):
- 1 **mandatory** Data Product (when enabled)
- **Optional** Data Quality scan (when `data_quality.enabled`)
- **Optional** Data Profiling scan (when `data_profiling.enabled`)
- **No Aspects** (reuses existing from common-governance)
- **No IAM** (managed via Dataplex UI)

### 6. **Data Quality Rules**

#### Current:
- Generic quality scan configuration
- No specific rule schema defined

#### Target:
- **9 specific rule types** with exact schemas:
  1. `non_null_expectation`
  2. `uniqueness_expectation`
  3. `set_expectation`
  4. `range_expectation`
  5. `regex_expectation`
  6. `row_condition_expectation`
  7. `table_condition_expectation`
  8. `sql_assertion`
  9. `statistic_range_expectation`
- `_build_dq_rule()` method maps YAML to Pulumi args
- Matches existing `dataplex_dq.yaml` schema

---

## Migration Steps

### Phase 1: Create New Isolated Project ✅ **DO THIS FIRST**

1. Create new directory: `dataplex-data-product-test/`
2. Create 5 files from claude.md specifications:
   - `Pulumi.yaml`
   - `Pulumi.dev-ne1-01-una-group1.yaml`
   - `pyproject.toml`
   - `__main__.py`
   - `data_product.py`
3. Set up venv and install dependencies
4. Initialize Pulumi stack: `dev-ne1-01-una-group1`
5. Test with `pulumi preview`
6. Validate all resources created correctly
7. **DO NOT touch existing `dataproducts-component/` directory**

### Phase 2: Validate Against Requirements

Verify the new implementation:
- [ ] Creates 1 DataProduct for `customer-sync` pipeline
- [ ] Creates 1 DQ DataScan with 3 rules
- [ ] Creates 1 DP DataScan with 10% sampling
- [ ] Skips `another-pipeline` (no `data_product` block)
- [ ] Naming follows: `dev_ne1_01_una_group_01_customer_sync`
- [ ] Labels include: `managed-by: datahub2`, `consumer: una`
- [ ] `pulumi up` succeeds
- [ ] GCP Console shows resources
- [ ] `pulumi destroy` cleans up

### Phase 3: Integration (Future)

Once validated:
1. Copy `data_product.py` to real `consumer-data-pipeline/` program
2. Add orchestrator instantiation to `__main__.py`
3. Test on dev stack
4. Verify coexistence with Analytics Hub (bqsharing)

---

## What to Preserve

From the current work, these concepts are still valuable:

- ✅ **Understanding of Dataplex Data Products** - core GCP resource knowledge
- ✅ **TypedDict patterns** - useful for other multi-language components
- ✅ **Naming conventions** - slugification, ID construction patterns
- ✅ **Git/GitHub workflow** - version control, tagging, publishing
- ✅ **Pulumi best practices** - resource options, outputs, logging

But the **implementation pattern** must change completely.

---

## Summary

This is **NOT a refactoring** - it's a **complete rewrite** with a different architectural pattern:

- **Old**: Standalone multi-language component consumable from YAML
- **New**: Python orchestrator class that integrates into existing programs

The **business logic** (creating Dataplex resources) is similar, but the **integration mechanism** is fundamentally different.

**Recommendation**:
1. Keep existing `dataproducts-component/` as a learning artifact
2. Create NEW `dataplex-data-product-test/` directory following claude.md
3. Start fresh with the orchestrator pattern
4. Once validated, deprecate the component approach
