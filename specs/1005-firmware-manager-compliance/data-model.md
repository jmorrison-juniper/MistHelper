# Data Model: FirmwareManagerConfig

**Feature**: `refactor/firmware-manager-compliance`
**Purpose**: Define the frozen `slots=True` dataclass that collapses the eight-parameter constructor into a single immutable value object.

---

## Overview

`FirmwareManagerConfig` is the single positional argument for the refactored `FirmwareManager.__init__`. It carries the two required identity fields (`apisession`, `org_id`) plus the six dependency-injection hooks that were previously keyword arguments. All hooks are `Optional[Callable]` — the class supplies fallbacks in `_bind_module_globals` for `None` values, exactly matching pre-refactor behavior (FR-017).

The dataclass is:

- **Frozen** — prevents mutation of injected callables after construction (defense-in-depth against test-fixture aliasing bugs).
- **`slots=True`** — eliminates per-instance `__dict__` overhead (marginal but conventional for value-object dataclasses).
- **Kw_only** — every field is keyword-only at the dataclass level, but the class receives the whole config as a single positional param, so callers use `FirmwareManagerConfig(apisession=..., org_id=..., ...)` and pass the resulting object as one positional argument to the class.

---

## Field Definition

```python
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, Optional

# Type aliases match the pre-refactor names in firmware_manager.py
SafeInputFn = Callable[..., str]
SelectSiteFn = Callable[..., Optional[str]]
CheckCacheFn = Callable[..., Any]
GetCsvPathFn = Callable[..., str]
GeneratorFn = Callable[..., Iterable[Any]]


@dataclass(frozen=True, slots=True, kw_only=True)
class FirmwareManagerConfig:
    """Immutable configuration object for FirmwareManager.

    Collapses the pre-refactor 8-parameter __init__ into a single positional
    argument, satisfying STRUCT-PARAMS (threshold 5) and enabling downstream
    simplifications throughout the class.

    All six *_fn hooks are Optional; the class binds sensible defaults via
    _bind_module_globals when None is provided, matching pre-refactor
    behavior exactly (FR-017).
    """

    # Required identity fields
    apisession: Any                                    # WHY: Mist API session for all HTTP calls
    org_id: str                                        # WHY: organization scope for every operation

    # Dependency-injection hooks (all optional; class supplies defaults)
    safe_input_fn: Optional[SafeInputFn] = None        # WHY: prompt helper with context-tag audit trail
    select_site_fn: Optional[SelectSiteFn] = None      # WHY: site-picker used by menu 196 sub-flows
    check_cache_fn: Optional[CheckCacheFn] = None      # WHY: CSV cache warm-up / regenerate logic
    get_csv_path_fn: Optional[GetCsvPathFn] = None     # WHY: resolves per-org CSV output path
    gateway_templates_fn: Optional[GeneratorFn] = None # WHY: gateway template streamer for SSR flow
    sites_fn: Optional[GeneratorFn] = None             # WHY: site streamer for cross-org iteration
```

---

## Field Mapping from Pre-Refactor `__init__`

| Pre-refactor param (line 61-70 of current file) | FirmwareManagerConfig field | Notes |
|-------------------------------------------------|-----------------------------|-------|
| `apisession: Any` (required positional) | `apisession: Any` | Identity — never `None`. |
| `org_id: str` (required positional) | `org_id: str` | Identity — never `None`. |
| `safe_input_fn: SafeInputFn \| None = None` | `safe_input_fn: Optional[SafeInputFn] = None` | Same semantics; `None` -> `InputUtils.safe_input` default in `_bind_module_globals`. |
| `select_site_fn: SelectSiteFn \| None = None` | `select_site_fn: Optional[SelectSiteFn] = None` | `None` -> `PromptUtils.select_site` default. |
| `check_cache_fn: CheckCacheFn \| None = None` | `check_cache_fn: Optional[CheckCacheFn] = None` | `None` -> `CacheUtils.check_and_generate_csv` default. |
| `get_csv_path_fn: GetCsvPathFn \| None = None` | `get_csv_path_fn: Optional[GetCsvPathFn] = None` | `None` -> `FilePathUtils.get_csv_path` default. |
| `gateway_templates_fn: GeneratorFn \| None = None` | `gateway_templates_fn: Optional[GeneratorFn] = None` | `None` -> `GatewayExportUtils.templates` default. |
| `sites_fn: GeneratorFn \| None = None` | `sites_fn: Optional[GeneratorFn] = None` | `None` -> `OrgSiteExporter.sites` default. |

**Total field count**: 8 (matches the 8 pre-refactor params exactly — no fields added, none dropped).

---

## Validation Rules

The dataclass performs the following validations in `__post_init__`:

| Field | Rule | Behavior on Violation |
|-------|------|------------------------|
| `apisession` | Must not be `None` | Raise `ValueError("apisession is required")` |
| `org_id` | Must be a non-empty string | Raise `ValueError("org_id must be a non-empty string")` |
| Each `*_fn` | Must be `None` or a callable | Raise `TypeError(f"{field_name} must be callable or None")` |

```python
def __post_init__(self) -> None:
    # WHY: fail-fast validation ensures downstream helpers never see invalid state
    if self.apisession is None:                                          # WHY: guard identity field
        raise ValueError("apisession is required")                        # WHY: no silent None-passing
    if not isinstance(self.org_id, str) or not self.org_id:              # WHY: guard org scope
        raise ValueError("org_id must be a non-empty string")             # WHY: prevents empty-scope leakage
    for name in (                                                        # WHY: iterate optional hooks
        "safe_input_fn",
        "select_site_fn",
        "check_cache_fn",
        "get_csv_path_fn",
        "gateway_templates_fn",
        "sites_fn",
    ):
        value = getattr(self, name)                                      # WHY: field access via slot name
        if value is not None and not callable(value):                    # WHY: allow None or callable only
            raise TypeError(f"{name} must be callable or None")           # WHY: clear diagnostic
```

---

## State Transitions

The config object is **immutable** — no state transitions apply after construction.

| Lifecycle Event | Config Behavior |
|-----------------|-----------------|
| Constructed via `FirmwareManagerConfig(...)` | Fields set once; frozen from that moment. |
| Attempted mutation (`config.dry_run = False`) | Raises `dataclasses.FrozenInstanceError`. |
| Attempted new attribute (`config.new_field = 1`) | Raises `AttributeError` (from `slots=True`). |
| Referenced across `FirmwareManager` helpers | Read-only; no helper mutates the config. |

Verified in `quickstart.md` Step 6 (REPL smoke).

---

## Usage — Consumer Side (Class)

The refactored `FirmwareManager` accepts the config as its single positional argument and reads it via `self._config`:

```python
class FirmwareManager:
    """Firmware upgrade orchestrator for AP/SSR/MSP flows."""

    def __init__(self, config: FirmwareManagerConfig) -> None:
        # WHY: PCPP orchestrator — attribute-bind then re-hydrate module globals
        logging.info("Initializing FirmwareManager for org %s", config.org_id)
        self._config: FirmwareManagerConfig = config                     # WHY: single source of truth for all deps
        _bind_module_globals(config)                                     # WHY: preserve pre-refactor module surface
        logging.debug("FirmwareManager init complete for org %s", config.org_id)

    @property
    def org_id(self) -> str:
        # WHY: back-compat surface for helpers that read self.org_id directly
        return self._config.org_id

    @property
    def apisession(self) -> Any:
        # WHY: back-compat surface for helpers that read self.apisession directly
        return self._config.apisession
```

Every downstream helper accesses hooks via `self._config.safe_input_fn` (or falls back to the module-global default that `_bind_module_globals` installed).

---

## Usage — Producer Side (MistHelper.py Factory)

The permitted diff at MistHelper.py lines 18791-18807 is the sole callsite that constructs `FirmwareManagerConfig`:

```python
# Before (current, 18791-18807):
class FirmwareManager:
    """Factory for the extracted firmware manager (src.firmware.firmware_manager)."""

    @staticmethod
    def create(apisession: Any, org_id: str) -> Any:
        from src.firmware.firmware_manager import FirmwareManager as _Impl  # noqa: PLC0415
        logging.debug("Building firmware manager impl for org %s", org_id)
        return _Impl(
            apisession=apisession,
            org_id=org_id,
            safe_input_fn=InputUtils.safe_input,
            select_site_fn=PromptUtils.select_site,
            check_cache_fn=CacheUtils.check_and_generate_csv,
            get_csv_path_fn=FilePathUtils.get_csv_path,
            gateway_templates_fn=GatewayExportUtils.templates,
            sites_fn=OrgSiteExporter.sites,
        )

# After (post-refactor, same lines):
class FirmwareManager:
    """Factory for the extracted firmware manager (src.firmware.firmware_manager)."""

    @staticmethod
    def create(apisession: Any, org_id: str) -> Any:
        from src.firmware.firmware_manager import (                         # noqa: PLC0415
            FirmwareManager as _Impl,
            FirmwareManagerConfig,
        )
        logging.debug("Building firmware manager impl for org %s", org_id)
        config = FirmwareManagerConfig(
            apisession=apisession,
            org_id=org_id,
            safe_input_fn=InputUtils.safe_input,
            select_site_fn=PromptUtils.select_site,
            check_cache_fn=CacheUtils.check_and_generate_csv,
            get_csv_path_fn=FilePathUtils.get_csv_path,
            gateway_templates_fn=GatewayExportUtils.templates,
            sites_fn=OrgSiteExporter.sites,
        )
        return _Impl(config)
```

**Diff scope**: 17 lines changed (the factory body). No other MistHelper.py changes required (five downstream call-sites still invoke `FirmwareManager.create(apisession, org_id)` unchanged).

---

## Relationship to Prior Art

`FirmwareManagerConfig` mirrors `BulkAPUpgraderConfig` from `src/firmware/bulk_ap_upgrader.py` (the 1004 refactor):

| Trait | BulkAPUpgraderConfig (1004) | FirmwareManagerConfig (1005) |
|-------|------------------------------|-------------------------------|
| Frozen | Yes | Yes |
| `slots=True` | Yes | Yes |
| `kw_only=True` | Yes | Yes |
| Field count | 10 | 8 |
| Required identity fields | 2 (org_id, apisession) | 2 (apisession, org_id) |
| Optional DI hooks | 8 | 6 |
| `__post_init__` validation | Yes (types + non-empty org_id) | Yes (identity fields + callable-or-None hooks) |
| MistHelper.py factory diff | Single-block (bulk_ap_upgrader factory) | Single-block (18791-18807) |

Reviewers familiar with the 1004 template will recognize the exact structural pattern.

---

## Summary

- One frozen `slots=True` dataclass, 8 fields, matches pre-refactor params 1:1.
- Immutable — no state transitions after construction.
- Validated in `__post_init__` with clear diagnostics.
- Consumed by `FirmwareManager.__init__` and produced by exactly one MistHelper.py callsite (the permitted 18791-18807 diff).
- Structurally identical to the 1004 prior-art `BulkAPUpgraderConfig`.
