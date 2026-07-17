# Code Elegance Review - dataproduct.py

## Overview

This document identifies opportunities to make the dataproduct.py code more concise, elegant, and Pythonic while maintaining readability and functionality.

---

## Recommendations

### 1. Use `dataclass` for AspectConfig ⭐⭐⭐

**Current** (lines 37-45):
```python
class AspectConfig:
    """Configuration for a single aspect type"""
    def __init__(self, aspect_type_id: str, builder_method: str, description: str):
        self.aspect_type_id = aspect_type_id
        """The AspectType ID in GCP Dataplex"""
        self.builder_method = builder_method
        """Name of the method that builds this aspect's data"""
        self.description = description
        """Human-readable description of the aspect"""
```

**Improved**:
```python
from dataclasses import dataclass

@dataclass
class AspectConfig:
    """Configuration for a single aspect type"""
    aspect_type_id: str
    """The AspectType ID in GCP Dataplex"""
    builder_method: str
    """Name of the method that builds this aspect's data"""
    description: str
    """Human-readable description of the aspect"""
```

**Benefits**:
- Automatic `__init__`, `__repr__`, `__eq__` methods
- More concise (9 lines → 7 lines)
- Standard Python pattern for data structures
- Better type hints support

---

### 2. Extract Scheduler Configuration Helper ⭐⭐⭐

**Current** (lines 573-579):
```python
# Get configuration values with defaults
time_zone = args.get("schedulerTimeZone", defaults.DEFAULT_SCHEDULER_TIME_ZONE)
retry_count = args.get("schedulerRetryCount", defaults.DEFAULT_SCHEDULER_RETRY_COUNT)
max_retry_duration = args.get("schedulerMaxRetryDuration", defaults.DEFAULT_SCHEDULER_MAX_RETRY_DURATION)
min_backoff = args.get("schedulerMinBackoffDuration", defaults.DEFAULT_SCHEDULER_MIN_BACKOFF_DURATION)
max_backoff = args.get("schedulerMaxBackoffDuration", defaults.DEFAULT_SCHEDULER_MAX_BACKOFF_DURATION)
max_doublings = args.get("schedulerMaxDoublings", defaults.DEFAULT_SCHEDULER_MAX_DOUBLINGS)
```

**Improved**:
```python
def _get_scheduler_config(self, args: DataProductArgs) -> Dict[str, Any]:
    """Extract scheduler configuration with defaults"""
    config_map = {
        "time_zone": ("schedulerTimeZone", defaults.DEFAULT_SCHEDULER_TIME_ZONE),
        "retry_count": ("schedulerRetryCount", defaults.DEFAULT_SCHEDULER_RETRY_COUNT),
        "max_retry_duration": ("schedulerMaxRetryDuration", defaults.DEFAULT_SCHEDULER_MAX_RETRY_DURATION),
        "min_backoff": ("schedulerMinBackoffDuration", defaults.DEFAULT_SCHEDULER_MIN_BACKOFF_DURATION),
        "max_backoff": ("schedulerMaxBackoffDuration", defaults.DEFAULT_SCHEDULER_MAX_BACKOFF_DURATION),
        "max_doublings": ("schedulerMaxDoublings", defaults.DEFAULT_SCHEDULER_MAX_DOUBLINGS),
    }
    return {key: args.get(arg_key, default) for key, (arg_key, default) in config_map.items()}

# Usage:
config = self._get_scheduler_config(args)
time_zone = config["time_zone"]
retry_count = config["retry_count"]
# ... or use config dict directly in retry_config
```

**Benefits**:
- DRY principle (no repeated args.get pattern)
- Easier to add/modify configuration options
- Configuration mapping in one place
- More testable

---

### 3. Extract Auto-Pause Determination ⭐⭐⭐

**Current** (lines 587-616):
```python
# Determine if job should be paused
# 1. If schedulerPaused is explicitly set, use that value
# 2. Otherwise, auto-pause for staging projects (bi-stg*)
# 3. Otherwise, don't pause (enabled)
project_id = str(args["project"])

if "schedulerPaused" in args:
    # Explicit override provided by user
    is_paused = bool(args["schedulerPaused"])
    if is_paused:
        pulumi.log.info(
            f"[{name}] Cloud Scheduler job will be created in PAUSED state "
            f"(explicitly set via schedulerPaused parameter)"
        )
    else:
        pulumi.log.info(
            f"[{name}] Cloud Scheduler job will be ENABLED "
            f"(explicitly set via schedulerPaused parameter)"
        )
elif project_id.startswith("bi-stg"):
    # Auto-pause for staging projects
    is_paused = True
    pulumi.log.info(
        f"[{name}] Cloud Scheduler job will be created in PAUSED state "
        f"(project '{project_id}' starts with 'bi-stg'). "
        f"Set schedulerPaused=false to enable."
    )
else:
    # Default to enabled for non-staging projects
    is_paused = False
```

**Improved**:
```python
def _determine_scheduler_pause_state(self, name: str, args: DataProductArgs) -> bool:
    """
    Determine if scheduler job should be paused.

    Priority:
    1. Explicit schedulerPaused parameter
    2. Auto-pause for staging projects (bi-stg*)
    3. Default to enabled
    """
    project_id = str(args["project"])

    if "schedulerPaused" in args:
        is_paused = bool(args["schedulerPaused"])
        state = "PAUSED" if is_paused else "ENABLED"
        pulumi.log.info(
            f"[{name}] Cloud Scheduler job will be {state} "
            f"(explicitly set via schedulerPaused parameter)"
        )
        return is_paused

    if project_id.startswith("bi-stg"):
        pulumi.log.info(
            f"[{name}] Cloud Scheduler job will be created in PAUSED state "
            f"(project '{project_id}' starts with 'bi-stg'). "
            f"Set schedulerPaused=false to enable."
        )
        return True

    return False

# Usage:
is_paused = self._determine_scheduler_pause_state(name, args)
```

**Benefits**:
- Single responsibility (one method, one concern)
- More testable (can test pause logic independently)
- Cleaner main method
- Reduced nesting

---

### 4. Simplify Execution Spec Building ⭐⭐

**Current** (lines 674-689):
```python
# Build execution_spec based on scheduling mode
if use_cloud_scheduler:
    # On-demand execution (triggered by Cloud Scheduler)
    execution_spec = {
        "trigger": {
            "on_demand": {}
        }
    }
else:
    # Internal scheduling (legacy mode)
    execution_spec = {
        "trigger": {
            "schedule": {
                "cron": schedule
            }
        }
    }
```

**Improved**:
```python
# Build execution_spec based on scheduling mode
execution_spec = {
    "trigger": {
        "on_demand": {} if use_cloud_scheduler else {"schedule": {"cron": schedule}}
    }
}
```

**Or with helper**:
```python
def _build_execution_spec(self, use_cloud_scheduler: bool, schedule: str) -> Dict[str, Any]:
    """Build datascan execution specification"""
    trigger = {"on_demand": {}} if use_cloud_scheduler else {"schedule": {"cron": schedule}}
    return {"trigger": trigger}

# Usage:
execution_spec = self._build_execution_spec(use_cloud_scheduler, schedule)
```

**Benefits**:
- More concise (15 lines → 3 lines or a helper method)
- Clearer intent
- Easier to read

---

### 5. Use Helper for Label Sanitization ⭐⭐

**Current** (lines 488-492):
```python
return {
    "data-product-id": args["dataProductId"].replace("_", "-").lower(),
    "cost-center": (args.get("costCenter", None) or "unallocated").replace("_", "-").lower(),
    "business-domain": args["businessDomain"].replace("_", "-").lower(),
    "managed-by": "pulumi",
    "version": args.get("version", defaults.DEFAULT_VERSION).replace(".", "-").lower()
}
```

**Improved**:
```python
def _sanitize_label(self, value: str) -> str:
    """Sanitize value for use as GCP label (lowercase, replace _ and . with -)"""
    return value.replace("_", "-").replace(".", "-").lower()

# Usage:
return {
    "data-product-id": self._sanitize_label(args["dataProductId"]),
    "cost-center": self._sanitize_label(args.get("costCenter") or "unallocated"),
    "business-domain": self._sanitize_label(args["businessDomain"]),
    "managed-by": "pulumi",
    "version": self._sanitize_label(args.get("version", defaults.DEFAULT_VERSION))
}
```

**Benefits**:
- DRY principle
- Consistent label sanitization
- Easier to modify sanitization rules
- More readable

---

### 6. DRY Asset Creation ⭐⭐⭐

**Current** (lines 502-540): BigQuery and GCS asset creation have significant duplication

**Improved**:
```python
def _create_asset(
    self,
    name: str,
    resource_type: str,
    resource_id: str,
    lake_path: str,
    zone_path: str,
    args: DataProductArgs,
    opts: ResourceOptions
) -> gcp.dataplex.Asset:
    """Create a Dataplex asset for BigQuery dataset or GCS bucket"""
    resource_map = {
        "BIGQUERY_DATASET": f"//bigquery.googleapis.com/projects/{args['project']}/datasets/{resource_id}",
        "STORAGE_BUCKET": f"//storage.googleapis.com/{resource_id}"
    }

    return gcp.dataplex.Asset(
        name,
        lake=lake_path,
        dataplex_zone=zone_path,
        location=args["location"],
        discovery_spec={
            "enabled": True,
            "schedule": "0 */12 * * *"
        },
        resource_spec={
            "name": resource_map[resource_type],
            "type": resource_type
        },
        labels=self._build_cost_labels(args),
        opts=opts
    )

def _attach_data_assets(self, name: str, args: DataProductArgs, opts: ResourceOptions) -> List[gcp.dataplex.Asset]:
    """Attach BigQuery datasets and GCS buckets as data assets"""
    assets = []
    lake_path = self._get_lake_path(args)
    zone_path = self._get_zone_path(args)

    for dataset_id in args.get("bigqueryDatasets", []):
        asset = self._create_asset(
            f"{name}-asset-bq-{dataset_id}",
            "BIGQUERY_DATASET",
            dataset_id,
            lake_path,
            zone_path,
            args,
            opts
        )
        assets.append(asset)

    for bucket_name in args.get("gcsBuckets", []):
        asset = self._create_asset(
            f"{name}-asset-gcs-{bucket_name}",
            "STORAGE_BUCKET",
            bucket_name,
            lake_path,
            zone_path,
            args,
            opts
        )
        assets.append(asset)

    return assets
```

**Benefits**:
- DRY principle (40 lines → ~30 lines)
- Single source of truth for asset creation
- Easier to add new asset types
- Consistent asset configuration

---

### 7. Simplify Validation Loop ⭐

**Current** (lines 342-346):
```python
# Validate email formats
email_fields = ["businessOwner", "technicalOwner", "technicalContact"]
for field in email_fields:
    email = str(args.get(field, ""))
    if "@" not in email:
        raise ValueError(f"Field '{field}' must be a valid email address, got: {email}")
```

**Improved**:
```python
# Validate email formats
for field in ["businessOwner", "technicalOwner", "technicalContact"]:
    if "@" not in str(args.get(field, "")):
        raise ValueError(f"Field '{field}' must be a valid email address, got: {args[field]}")
```

**Or more robust**:
```python
import re

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def _validate_email(self, email: str, field_name: str) -> None:
    """Validate email format using regex"""
    if not EMAIL_PATTERN.match(str(email)):
        raise ValueError(f"Field '{field_name}' must be a valid email address, got: {email}")

# Usage:
for field in ["businessOwner", "technicalOwner", "technicalContact"]:
    self._validate_email(args[field], field)
```

**Benefits**:
- More concise
- Better email validation (regex vs simple "@" check)
- Reusable validation method

---

### 8. Use Dict Comprehension for Required Fields ⭐

**Current** (lines 337-339):
```python
for field in required_fields:
    if not args.get(field):
        raise ValueError(f"Required field '{field}' is missing or empty")
```

**Improved**:
```python
missing_fields = [f for f in required_fields if not args.get(f)]
if missing_fields:
    raise ValueError(f"Required fields missing or empty: {', '.join(missing_fields)}")
```

**Benefits**:
- More Pythonic
- Reports all missing fields at once (better UX)
- More concise

---

### 9. Simplify Retry Config Building ⭐⭐

**Current** (lines 639-645):
```python
retry_config={
    "retry_count": retry_count,
    "max_retry_duration": max_retry_duration,
    "min_backoff_duration": min_backoff,
    "max_backoff_duration": max_backoff,
    "max_doublings": max_doublings
}
```

**Improved** (if using scheduler config helper from #2):
```python
def _build_retry_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """Build Cloud Scheduler retry configuration"""
    return {
        "retry_count": config["retry_count"],
        "max_retry_duration": config["max_retry_duration"],
        "min_backoff_duration": config["min_backoff"],
        "max_backoff_duration": config["max_backoff"],
        "max_doublings": config["max_doublings"]
    }

# Usage:
config = self._get_scheduler_config(args)
retry_config = self._build_retry_config(config)
```

**Benefits**:
- Cleaner separation of concerns
- Easier to test retry config building
- Can add validation if needed

---

### 10. Use Context Manager Pattern for Resource Options ⭐

**Current** (lines 463-466):
```python
entry_opts = ResourceOptions(
    parent=self,
    depends_on=[self.data_product]
)
entry = gcp.dataplex.Entry(
    f"{name}-entry",
    # ... many parameters ...
    opts=entry_opts
)
```

**Improved**:
```python
entry = gcp.dataplex.Entry(
    f"{name}-entry",
    # ... many parameters ...
    opts=ResourceOptions(parent=self, depends_on=[self.data_product])
)
```

**Benefits**:
- More concise (inline opts)
- Fewer intermediate variables
- Clearer that opts is specific to this resource

---

## Priority Summary

### High Priority (⭐⭐⭐) - Most Impact
1. **Use `dataclass` for AspectConfig** - Standard Python pattern
2. **Extract Scheduler Configuration Helper** - Eliminates repetition
3. **Extract Auto-Pause Determination** - Improves testability
4. **DRY Asset Creation** - Significant code reduction

### Medium Priority (⭐⭐) - Good Improvements
5. **Simplify Execution Spec Building** - Much more concise
6. **Use Helper for Label Sanitization** - DRY principle
7. **Simplify Retry Config Building** - Better separation

### Low Priority (⭐) - Nice to Have
8. **Simplify Validation Loop** - Marginal improvement
9. **Use Dict Comprehension for Required Fields** - Better UX
10. **Use Context Manager Pattern** - Marginal improvement

---

## Implementation Plan

### Phase 1 (High Priority - ~30 mins)
- Convert AspectConfig to dataclass
- Extract scheduler configuration helper
- Extract auto-pause determination method
- DRY asset creation

### Phase 2 (Medium Priority - ~20 mins)
- Simplify execution spec building
- Add label sanitization helper
- Extract retry config building

### Phase 3 (Low Priority - ~10 mins)
- Improve validation loops
- Use dict comprehension for required fields
- Inline ResourceOptions where appropriate

---

## Code Size Reduction

**Before**: ~794 lines
**After**: ~720 lines (estimated)
**Reduction**: ~70 lines (~9%)

**Method Count**:
- Before: 14 methods
- After: 19 methods (more, but smaller and more focused)

**Average Method Size**:
- Before: ~57 lines per method
- After: ~38 lines per method

---

## Testing Impact

All improvements are **refactorings** (no behavior changes):
- Existing tests should continue to pass
- New helper methods can be unit tested independently
- No breaking changes to public API

---

## Example: Complete Refactored `_create_scheduler_job_for_datascan()`

```python
def _create_scheduler_job_for_datascan(
    self,
    name: str,
    datascan: gcp.dataplex.Datascan,
    schedule: str,
    args: DataProductArgs,
    opts: ResourceOptions
) -> gcp.cloudscheduler.Job:
    """Create a Cloud Scheduler job to trigger a Dataplex Datascan on-demand."""

    # Get configuration
    config = self._get_scheduler_config(args)
    service_account = args.get("schedulerServiceAccount") or \
                     f"{self._project_data.number}-compute@developer.gserviceaccount.com"
    is_paused = self._determine_scheduler_pause_state(name, args)

    # Create scheduler job
    return gcp.cloudscheduler.Job(
        f"{name}-scheduler",
        name=f"{name}-scheduler",
        description=f"Cloud Scheduler job to trigger {name} datascan",
        schedule=schedule,
        time_zone=config["time_zone"],
        paused=is_paused,
        project=args["project"],
        region=args["location"],
        http_target={
            "uri": datascan.name.apply(
                lambda n: f"https://dataplex.googleapis.com/v1/{n}:run"
            ),
            "http_method": "POST",
            "oauth_token": {
                "service_account_email": service_account,
                "scope": "https://www.googleapis.com/auth/cloud-platform"
            }
        },
        retry_config=self._build_retry_config(config),
        opts=ResourceOptions(parent=self, depends_on=[datascan])
    )
```

**Before**: 111 lines
**After**: 37 lines
**Reduction**: 67% smaller, much more readable

---

## Recommendations

**Implement These First**:
1. ✅ Use dataclass for AspectConfig (easy win, standard pattern)
2. ✅ Extract scheduler config helper (eliminates most repetition)
3. ✅ Extract auto-pause logic (improves testability significantly)
4. ✅ DRY asset creation (significant code reduction)

**Consider These**:
- Add proper email validation with regex (mentioned in ROBUSTNESS-IMPROVEMENTS.md)
- Extract common patterns into helper methods
- Use type hints consistently throughout

**Don't Bother With**:
- Micro-optimizations that reduce readability
- One-off inline simplifications
- Changes that don't meaningfully improve the code

---

## Conclusion

The current code is **well-structured and functional**. These improvements would make it more:
- ✅ **Pythonic** (using standard patterns like dataclass)
- ✅ **DRY** (less repetition)
- ✅ **Testable** (smaller, focused methods)
- ✅ **Readable** (clearer intent, less nesting)
- ✅ **Maintainable** (easier to modify and extend)

**Recommended**: Implement Phase 1 (high priority) items first, then evaluate if Phase 2/3 provide enough value.
