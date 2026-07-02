# Phase 1 Data Model: BulkAPUpgraderConfig

**Feature**: `refactor/bulk-ap-upgrader-compliance`
**Date**: 2026-07-01
**Location**: Same module as the target class — `src/firmware/bulk_ap_upgrader.py` (per FR-018)

---

## Entity: `BulkAPUpgraderConfig`

A frozen `@dataclass` that holds every input parameter required to construct a `BulkAPFirmwareUpgrader`. Replaces the 10-parameter constructor signature.

### Definition

```python
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass(frozen=True, slots=True)
class BulkAPUpgraderConfig:
    """Immutable configuration bundle for BulkAPFirmwareUpgrader.

    Groups every input required by the upgrader's constructor into a single
    dataclass, replacing the legacy 10-parameter __init__ signature. Frozen
    so that once a run starts, its configuration cannot be mutated mid-flight
    (defensive against the "same config, two upgraders, one modifies mid-run"
    class of bug).
    """

    # ------------------------------------------------------------------
    # Required session inputs
    # ------------------------------------------------------------------
    org_id: str                                     # Mist organization ID this run targets
    apisession: Any                                 # Authenticated mistapi session object

    # ------------------------------------------------------------------
    # Optional behavior flags
    # ------------------------------------------------------------------
    sites_override: Optional[list[dict[str, Any]]] = None   # Pre-selected sites (skips interactive)
    dry_run: bool = False                                    # Simulate upgrades without API calls

    # ------------------------------------------------------------------
    # Injected callables (dependency injection points)
    # ------------------------------------------------------------------
    safe_input_fn: Optional[Callable[..., str]] = None          # (prompt, context) -> str
    check_stop_fn: Optional[Callable[[], bool]] = None          # () -> bool for interrupt polling
    fetch_sites_fn: Optional[Callable[[str], list]] = None      # (org_id) -> list of sites
    get_csv_path_fn: Optional[Callable[[str], str]] = None      # (filename) -> resolved path
    check_firmware_status_fn: Optional[Callable[[], None]] = None  # () -> None; runs status check
    get_org_id_fn: Optional[Callable[[], str]] = None           # () -> str; prompts if unset
```

### Field-by-Field Mapping from Legacy `__init__`

| Legacy `__init__` Parameter | `BulkAPUpgraderConfig` Field | Default | Notes |
|-----------------------------|-------------------------------|---------|-------|
| `org_id: str` | `org_id: str` | required | Formerly 1st positional arg. |
| `apisession: Any` | `apisession: Any` | required | Formerly 2nd positional arg. Moved into config per R-1 recommendation (Option C). |
| `sites_override` | `sites_override` | `None` | Unchanged type. |
| `dry_run` | `dry_run` | `False` | Unchanged. |
| `safe_input_fn` | `safe_input_fn` | `None` | Unchanged. Fallback to builtin `input` still happens in `_init_session_ctx`. |
| `check_stop_fn` | `check_stop_fn` | `None` | Unchanged. |
| `fetch_sites_fn` | `fetch_sites_fn` | `None` | Unchanged. |
| `get_csv_path_fn` | `get_csv_path_fn` | `None` | Unchanged. |
| `check_firmware_status_fn` | `check_firmware_status_fn` | `None` | Unchanged. |
| `get_org_id_fn` | `get_org_id_fn` | `None` | Unchanged. |

Total: 10 legacy parameters -> 10 dataclass fields. One-to-one mapping. No renames, no type changes, no default changes — the mapping is purely structural, preserving observable behavior (FR-017).

---

## Validation Rules

The dataclass itself enforces:

1. **Frozen instances**: Fields cannot be reassigned after construction. Any attempt raises `dataclasses.FrozenInstanceError`. This is a defensive property, not a functional requirement.
2. **Slots**: `slots=True` prevents accidental attribute additions and reduces per-instance memory footprint.
3. **Required fields**: `org_id` and `apisession` have no default, so Python raises `TypeError` at construction if omitted — this satisfies the spec Edge Case ("fail fast with a clear `TypeError`" when required inputs are missing).

The dataclass does NOT enforce:

- Non-empty string checks on `org_id` (delegated to `mistapi` — an invalid ID surfaces as an API error, which is the pre-refactor behavior).
- Callable-signature checks on the six injected callables (Python's duck typing is preserved; the upgrader tolerates `None` for each and falls back to `input`/no-op as it does today).

Optional post-init hook (deferred; not part of this feature): a `__post_init__` that logs a debug line with the non-secret fields would be pleasant but is not required for grade B and is skipped to keep the diff small.

---

## State Transitions

`BulkAPUpgraderConfig` has none. It is immutable, constructed once, consumed once. There is no lifecycle — it is a data-only value object.

The `BulkAPFirmwareUpgrader` instance that receives it, however, transitions through:

```text
constructed -> _init_session_ctx -> _init_ap_and_site_state -> _init_plan_and_results_state
       -> execute() -> _announce_start
       -> _run_discovery_phase   (steps 1-4; may early-exit)
       -> _run_planning_phase    (steps 5-7; may early-exit)
       -> _run_execution_phase   (steps 8-11; terminal)
       -> [done]
```

This is unchanged from the pre-refactor lifecycle — only the phase groupings are new (see `research.md` R-3).

---

## Relationship to Other Entities

- **Consumed by**: `BulkAPFirmwareUpgrader.__init__(config: BulkAPUpgraderConfig)`. Single consumer.
- **Constructed by**:
  1. `MistHelper.py:19783` thin wrapper class (production menu 195 path).
  2. `tests/unit/test_bulk_ap_upgrader.py:69` `_make_upgrader` factory (test path).
- **Depends on**: Nothing beyond `dataclasses`, `typing.Any`, `typing.Callable`, `typing.Optional` — all standard library. No import from other project modules, so no circular-import risk (FR-018).

---

## Backward Compatibility Notes

- Callers that pass a bare `BulkAPFirmwareUpgrader(org_id, apisession, sites_override=..., ...)` will receive a `TypeError` at construction time because the new signature is `__init__(self, config)`. This is intentional and matches the spec Edge Case requirement.
- The two known in-repo callers are updated in the same commit as this dataclass introduction. No transition period is needed because both callers are under our control.
- The class name `BulkAPFirmwareUpgrader` is preserved (FR-014). Only its constructor signature changes.
- The `.execute()` method signature is unchanged (FR-014, FR-015).
