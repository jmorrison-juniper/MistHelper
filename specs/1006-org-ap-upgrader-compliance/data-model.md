# Data Model: OrgAPUpgraderConfig

**Feature**: `refactor/org-ap-upgrader-compliance`
**Purpose**: Define the frozen `slots=True` `kw_only=True` dataclass that collapses the eleven-parameter constructor into a single immutable value object, satisfying STRUCT-PARAMS (threshold 5) while preserving byte-identical MistHelper.py callsite semantics at lines 20247/20269/20289/20305.

---

## Overview

`OrgAPUpgraderConfig` is the single internal value object that carries all eleven pre-refactor constructor parameters. It is constructed inside `OrgLevelAPFirmwareUpgrader.__init__(**cfg)` from the kwargs the four MistHelper.py callsites already pass — no callsite edits required (FR-018).

The dataclass is:

- **Frozen** — freezes the field *binding* (prevents `config.apisession = new_session`). Referenced objects (`mistapi` session, injected callables, `msp_privileges` list) retain their own mutation contracts. This mirrors the 1005 precedent.
- **`slots=True`** — eliminates per-instance `__dict__` overhead. Also enforces "no accidental new attributes."
- **`kw_only=True`** — every field is keyword-only, so the kwargs-passthrough constructor `OrgLevelAPFirmwareUpgrader(**cfg)` maps 1:1 to `OrgAPUpgraderConfig(**cfg)` without positional-order fragility.

The MistHelper.py callsites already use kwargs form (`_Impl(org_id=..., apisession=..., ...)`), so the shape aligns exactly (R-1, R-9).

---

## Field Definition

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True, slots=True, kw_only=True)
class OrgAPUpgraderConfig:
    """Immutable configuration object for OrgLevelAPFirmwareUpgrader.

    Collapses the pre-refactor 11-parameter __init__ into a single internal
    value object built from the kwargs the four MistHelper.py callsites
    already pass. Satisfies STRUCT-PARAMS (threshold 5) with a formal count
    of 1 (the __init__ signature becomes ``def __init__(self, **cfg)``).

    All six *_fn hooks are Optional; the class supplies sensible defaults
    (matching pre-refactor `_default_*` staticmethods) when None is provided.
    ``msp_privileges`` and ``selected_msp`` accept None for the org-mode
    entry points (callsites at lines 20247/20269) and are set to real
    values for the MSP-mode paths (callsites at lines 20289/20305).
    """

    # Identity fields (present at every callsite, may be empty string for MSP-selection paths)
    org_id: str                                             # WHY: organization scope (empty at MSP-select callsites)
    apisession: Any                                         # WHY: Mist API session used for every HTTP call

    # Mode toggle
    dry_run: bool = False                                   # WHY: preview-only mode; no upgrades committed

    # Dependency-injection hooks (all optional; class supplies pre-refactor defaults)
    safe_input_fn: Optional[Any] = None                     # WHY: safe_input(context=...) prompt helper
    check_stop_fn: Optional[Any] = None                     # WHY: cooperative-cancel probe between phases
    get_org_id_fn: Optional[Any] = None                     # WHY: resolves org id from user prompt / cache
    fetch_sites_fn: Optional[Any] = None                    # WHY: site streamer used by site-scope selection
    write_results_fn: Optional[Any] = None                  # WHY: CSV persister for per-phase results
    is_debug_fn: Optional[Any] = None                       # WHY: verbose-logging predicate

    # MSP context (populated only on the MSP-mode paths)
    msp_privileges: Optional[list[Any]] = None              # WHY: list of MSP orgs available to caller
    selected_msp: Optional[dict[str, Any]] = None           # WHY: pre-selected MSP payload (name + id)
```

---

## Field Mapping from Pre-Refactor `__init__`

The current signature at `src/firmware/org_ap_upgrader.py:41` is:

```python
def __init__(  # pylint: disable=too-many-arguments
    self,
    org_id: str,
    apisession: Any,
    *,
    dry_run: bool = False,
    safe_input_fn: Any = None,
    check_stop_fn: Any = None,
    get_org_id_fn: Any = None,
    fetch_sites_fn: Any = None,
    write_results_fn: Any = None,
    is_debug_fn: Any = None,
    msp_privileges: list[Any] | None = None,
    selected_msp: dict[str, Any] | None = None,
) -> None:
```

Every parameter maps 1:1 to a config field:

| Pre-refactor param | OrgAPUpgraderConfig field | Notes |
|--------------------|---------------------------|-------|
| `org_id: str` | `org_id: str` | May be `""` at MSP-selection callsites (20289, 20305). |
| `apisession: Any` | `apisession: Any` | Never `None`; runtime handle preserved by reference. |
| `dry_run: bool = False` | `dry_run: bool = False` | Preview-only toggle. |
| `safe_input_fn: Any = None` | `safe_input_fn: Optional[Any] = None` | `None` -> `_default_safe_input` (InputUtils). |
| `check_stop_fn: Any = None` | `check_stop_fn: Optional[Any] = None` | `None` -> no-op predicate. |
| `get_org_id_fn: Any = None` | `get_org_id_fn: Optional[Any] = None` | `None` -> `_default_get_org_id`. |
| `fetch_sites_fn: Any = None` | `fetch_sites_fn: Optional[Any] = None` | `None` -> `_default_fetch_sites`. |
| `write_results_fn: Any = None` | `write_results_fn: Optional[Any] = None` | `None` -> `_default_write_results`. |
| `is_debug_fn: Any = None` | `is_debug_fn: Optional[Any] = None` | `None` -> `_default_is_debug`. |
| `msp_privileges: list \| None = None` | `msp_privileges: Optional[list[Any]] = None` | Normalized to `[]` in `__post_init__`. |
| `selected_msp: dict \| None = None` | `selected_msp: Optional[dict[str, Any]] = None` | Kept as `None` when absent. |

**Total field count**: 11 (matches the 11 pre-refactor params exactly — no fields added, none dropped).

---

## Validation Rules

The dataclass performs the following validations in `__post_init__`. Because the object is frozen, normalization uses `object.__setattr__` (the sanctioned frozen-mutation pattern).

| Field | Rule | Behavior on Violation |
|-------|------|------------------------|
| `org_id` | Must be `str` (empty allowed for MSP-selection callsites) | `TypeError("org_id must be a string")` |
| `apisession` | Must not be `None` | `ValueError("apisession is required")` |
| `dry_run` | Coerced to `bool` via `bool(value)` | Never raises (permissive coercion, matches pre-refactor) |
| Each `*_fn` | Must be `None` or callable | `TypeError(f"{name} must be callable or None")` |
| `msp_privileges` | If not `None`, must be a `list`; `None` normalized to `[]` | `TypeError("msp_privileges must be a list or None")` |
| `selected_msp` | If not `None`, must be a `dict` | `TypeError("selected_msp must be a dict or None")` |

```python
def __post_init__(self) -> None:
    # WHY: fail-fast validation ensures downstream helpers never see invalid state
    if not isinstance(self.org_id, str):                                  # WHY: guard identity type (empty string OK)
        raise TypeError("org_id must be a string")                        # WHY: allow "" for MSP-select callsites
    if self.apisession is None:                                           # WHY: guard runtime handle
        raise ValueError("apisession is required")                        # WHY: no silent None-passing to mistapi
    object.__setattr__(self, "dry_run", bool(self.dry_run))               # WHY: permissive bool coercion (frozen ok)
    for name in (                                                         # WHY: iterate optional hook fields
        "safe_input_fn",
        "check_stop_fn",
        "get_org_id_fn",
        "fetch_sites_fn",
        "write_results_fn",
        "is_debug_fn",
    ):
        value = getattr(self, name)                                       # WHY: field access via slot name
        if value is not None and not callable(value):                     # WHY: allow None or callable only
            raise TypeError(f"{name} must be callable or None")           # WHY: clear diagnostic
    if self.msp_privileges is None:                                       # WHY: normalize absent MSP list
        object.__setattr__(self, "msp_privileges", [])                    # WHY: downstream helpers expect list, not None
    elif not isinstance(self.msp_privileges, list):                       # WHY: strict type check for MSP list
        raise TypeError("msp_privileges must be a list or None")          # WHY: no dict-vs-list confusion
    if self.selected_msp is not None and not isinstance(                  # WHY: guard MSP payload shape
        self.selected_msp, dict
    ):
        raise TypeError("selected_msp must be a dict or None")            # WHY: MSP payload is always a dict
```

---

## State Transitions

The config object is **immutable** — no state transitions apply after construction.

| Lifecycle Event | Config Behavior |
|-----------------|-----------------|
| Constructed via `OrgAPUpgraderConfig(**cfg)` inside `__init__` | Fields set once; frozen from that moment. `msp_privileges=None` normalized to `[]`. |
| Attempted rebinding (`config.dry_run = True`) | Raises `dataclasses.FrozenInstanceError`. |
| Attempted new attribute (`config.new_field = 1`) | Raises `AttributeError` (from `slots=True`). |
| Referenced object mutation (`config.msp_privileges.append(...)`) | **Allowed** — frozen freezes the field binding, not the referenced list's contents. Matches pre-refactor behavior where the same list reference was mutated in place. |
| Referenced across `OrgLevelAPFirmwareUpgrader` helpers | Read-only; no helper mutates `self._config` itself. |

---

## Immutability Contract — Value Object over References

The `frozen=True` guarantee is a **reference-binding** guarantee, not a deep-immutability guarantee:

- `config.apisession` cannot be reassigned to a different session object.
- The underlying `mistapi.APISession` instance retains its own state (cookie jar, retry counter, etc.) and mutates during API calls — this is pre-refactor behavior and must be preserved (FR-003, no observable behavior change).
- `config.msp_privileges` cannot be reassigned to a different list.
- The underlying list may be mutated by downstream helpers (e.g., `_select_orgs_from_msp` appends discovered orgs) — this preserves the current cross-helper communication channel.

This distinction is intentional and matches the 1005 precedent (`FirmwareManagerConfig` also freezes reference bindings while allowing the underlying `apisession` and callable hooks to retain their own contracts).

---

## Usage — Consumer Side (Class)

The refactored `OrgLevelAPFirmwareUpgrader` accepts `**cfg` (kwargs-passthrough), builds the config internally, and reads it via `self._config`:

```python
class OrgLevelAPFirmwareUpgrader:
    """Org-wide AP firmware upgrader (menu 196 org-mode path)."""

    def __init__(self, **cfg: Any) -> None:
        # WHY: kwargs-passthrough preserves the 4 MistHelper.py callsites byte-identically
        logging.info("Initializing OrgLevelAPFirmwareUpgrader (dry_run=%s)", cfg.get("dry_run", False))
        self._config: OrgAPUpgraderConfig = OrgAPUpgraderConfig(**cfg)   # WHY: single source of truth for all params
        self._init_selection_state()                                     # WHY: existing helper, unchanged
        self._init_device_state()                                        # WHY: existing helper, unchanged
        self._init_results_state()                                       # WHY: existing helper, unchanged
        logging.debug("OrgLevelAPFirmwareUpgrader init complete for org %s", self._config.org_id)

    @property
    def org_id(self) -> str:
        # WHY: back-compat surface for helpers that read self.org_id directly
        return self._config.org_id

    @property
    def apisession(self) -> Any:
        # WHY: back-compat surface for helpers that read self.apisession directly
        return self._config.apisession

    @property
    def dry_run(self) -> bool:
        # WHY: back-compat surface for helpers that read self.dry_run directly
        return self._config.dry_run
```

Every downstream helper accesses hooks via `self._config.safe_input_fn` (with a resolver that falls back to `_default_safe_input` when `None`).

---

## Usage — Producer Side (MistHelper.py Callsites — UNCHANGED)

The four MistHelper.py callsites at lines 20247, 20269, 20289, 20305 remain **byte-identical**. Because the class now accepts `**cfg`, the same kwargs flow through unchanged into the config constructor.

### Callsite 1 — Line 20247 (org-mode, full 11 kwargs)

```python
# UNCHANGED — no diff at this line range
_Impl = _resolve_impl()
upgrader = _Impl(
    org_id=org_id,
    apisession=apisession,
    dry_run=dry_run,
    safe_input_fn=safe_input_fn,
    check_stop_fn=check_stop_fn,
    get_org_id_fn=get_org_id_fn,
    fetch_sites_fn=fetch_sites_fn,
    write_results_fn=write_results_fn,
    is_debug_fn=is_debug_fn,
    msp_privileges=msp_privileges,
    selected_msp=selected_msp,
)
```

### Callsite 2 — Line 20269 (execute, 9 kwargs, no MSP context)

```python
# UNCHANGED — msp_privileges and selected_msp default to None
upgrader = _Impl(
    org_id=org_id,
    apisession=apisession,
    dry_run=dry_run,
    safe_input_fn=safe_input_fn,
    check_stop_fn=check_stop_fn,
    get_org_id_fn=get_org_id_fn,
    fetch_sites_fn=fetch_sites_fn,
    write_results_fn=write_results_fn,
    is_debug_fn=is_debug_fn,
)
```

### Callsite 3 — Line 20289 (MSP-select, 5 kwargs, org_id="")

```python
# UNCHANGED — org_id="" is the empty-scope sentinel for MSP selection
upgrader = _Impl(
    org_id="",
    apisession=apisession,
    safe_input_fn=safe_input_fn,
    check_stop_fn=check_stop_fn,
    msp_privileges=msp_privileges,
)
```

### Callsite 4 — Line 20305 (MSP-org-select, 3 kwargs, org_id="")

```python
# UNCHANGED — the thinnest construction path; only session + one hook
upgrader = _Impl(
    org_id="",
    apisession=apisession,
    safe_input_fn=safe_input_fn,
)
```

**Diff scope outside `src/firmware/org_ap_upgrader.py`**: **zero lines**. All four callsites remain byte-identical (FR-018, SC-007).

---

## Relationship to Prior Art

`OrgAPUpgraderConfig` mirrors `FirmwareManagerConfig` (1005) and `BulkAPUpgraderConfig` (1004) with adjustments for the 1006 constraints:

| Trait | BulkAPUpgraderConfig (1004) | FirmwareManagerConfig (1005) | OrgAPUpgraderConfig (1006) |
|-------|------------------------------|-------------------------------|------------------------------|
| Frozen | Yes | Yes | Yes |
| `slots=True` | Yes | Yes | Yes |
| `kw_only=True` | Yes | Yes | Yes |
| Field count | 10 | 8 | 11 |
| Required identity fields | 2 (org_id, apisession) | 2 (apisession, org_id) | 2 (org_id, apisession) |
| Identity permits `""` | No | No | **Yes** (org_id="" at MSP-select callsites) |
| Optional DI hooks | 8 | 6 | 6 |
| Runtime-context fields | 0 | 0 | 2 (msp_privileges, selected_msp) |
| `__post_init__` validation | Yes | Yes | Yes (+ list/dict shape + None normalization) |
| MistHelper.py factory diff | Single-block factory body | Single-block factory body (18791-18807) | **Zero-line diff** (kwargs-passthrough) |
| Constructor formal param count post-refactor | 1 (config positional) | 1 (config positional) | 1 (`**cfg`) |

The 1006 refactor is **strictly more constrained** than 1004 / 1005: no MistHelper.py diff is permitted at all, driving the kwargs-passthrough design (R-1, R-9).

---

## Failure-Mode Diagnostics

| Bad Call | Expected Exception | Diagnostic |
|----------|--------------------|------------|
| `OrgAPUpgraderConfig(org_id=None, apisession=s)` | `TypeError` | `org_id must be a string` |
| `OrgAPUpgraderConfig(org_id="o", apisession=None)` | `ValueError` | `apisession is required` |
| `OrgAPUpgraderConfig(org_id="o", apisession=s, safe_input_fn=42)` | `TypeError` | `safe_input_fn must be callable or None` |
| `OrgAPUpgraderConfig(org_id="o", apisession=s, msp_privileges={"x": 1})` | `TypeError` | `msp_privileges must be a list or None` |
| `OrgAPUpgraderConfig(org_id="o", apisession=s, selected_msp=["a"])` | `TypeError` | `selected_msp must be a dict or None` |
| `config.dry_run = True` (post-construction) | `FrozenInstanceError` | Dataclass frozen contract |
| `config.brand_new_field = 1` | `AttributeError` | Slots contract |

Every diagnostic message is ASCII-only, matches Constitution VII, and appears in `logging.error(...)` at the callsite where the exception is caught (if any).

---

## Summary

- One frozen `slots=True` `kw_only=True` dataclass, 11 fields, matches pre-refactor params 1:1.
- Immutable at the field-binding level; referenced objects retain their own contracts.
- Validated in `__post_init__` with clear ASCII diagnostics and `msp_privileges=None -> []` normalization via `object.__setattr__`.
- Consumed by `OrgLevelAPFirmwareUpgrader.__init__(**cfg)` — the sole producer is the class itself, so no MistHelper.py diff is required (contrast with 1004 / 1005 which had a single-block factory diff).
- Structurally the strict superset of the 1004 / 1005 precedents, adapted for the zero-callsite-diff constraint via kwargs-passthrough.
