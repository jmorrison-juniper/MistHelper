# Contract: `BulkAPFirmwareUpgrader` Constructor

**Feature**: `refactor/bulk-ap-upgrader-compliance`
**Contract Type**: Python class constructor signature
**Scope**: Two direct in-repo callers (production wrapper + test factory)

---

## Pre-Refactor Signature (current, `src/firmware/bulk_ap_upgrader.py:43`)

```python
class BulkAPFirmwareUpgrader:
    def __init__(
        self,
        org_id: str,
        apisession: Any,
        *,
        sites_override: list[dict[str, Any]] | None = None,
        dry_run: bool = False,
        safe_input_fn: Any = None,
        check_stop_fn: Any = None,
        fetch_sites_fn: Any = None,
        get_csv_path_fn: Any = None,
        check_firmware_status_fn: Any = None,
        get_org_id_fn: Any = None,
    ) -> None: ...
```

**Parameter count**: 10 (excluding `self`). **Violation**: Constitution I / FR-004 ceiling is 5.

---

## Post-Refactor Signature (target)

```python
@dataclass(frozen=True, slots=True)
class BulkAPUpgraderConfig:
    org_id: str
    apisession: Any
    sites_override: Optional[list[dict[str, Any]]] = None
    dry_run: bool = False
    safe_input_fn: Optional[Callable[..., str]] = None
    check_stop_fn: Optional[Callable[[], bool]] = None
    fetch_sites_fn: Optional[Callable[[str], list]] = None
    get_csv_path_fn: Optional[Callable[[str], str]] = None
    check_firmware_status_fn: Optional[Callable[[], None]] = None
    get_org_id_fn: Optional[Callable[[], str]] = None


class BulkAPFirmwareUpgrader:
    def __init__(self, config: BulkAPUpgraderConfig) -> None: ...
```

**Parameter count**: 1 (excluding `self`). **Passes**: FR-004.

---

## Contract Invariants

The following properties MUST hold across the refactor:

| # | Invariant | Verified By |
|---|-----------|-------------|
| C-1 | The class name `BulkAPFirmwareUpgrader` is unchanged. | `grep -n "^class BulkAPFirmwareUpgrader" src/firmware/bulk_ap_upgrader.py` returns exactly one line. |
| C-2 | The `.execute()` method signature is unchanged (`self` only, no new params). | `grep -n "def execute" src/firmware/bulk_ap_upgrader.py` shows `def execute(self) -> None:`. |
| C-3 | The 11-step workflow order (`_step1_*` through `_step11_*`) is preserved. | Read `_run_discovery_phase` -> `_run_planning_phase` -> `_run_execution_phase` bodies; assert steps 1-11 appear in ascending order. |
| C-4 | Every legacy `__init__` parameter maps to exactly one `BulkAPUpgraderConfig` field with the same name, type, and default. | See `data-model.md` mapping table. |
| C-5 | Constructor rejects positional arguments beyond `config` with a plain `TypeError`. | `BulkAPFirmwareUpgrader("org1", session, dry_run=True)` raises `TypeError: __init__() takes 2 positional arguments but 3 were given`. |
| C-6 | Every existing test in `tests/unit/test_bulk_ap_upgrader.py` passes with only the `_make_upgrader` factory function updated (no test-body changes). | `pytest tests/unit/test_bulk_ap_upgrader.py -v` — all green. |

---

## Caller-Site Contract Changes

### Caller 1: `MistHelper.py:19783-19810` (production menu 195 thin wrapper)

**Before**:

```python
class BulkAPFirmwareUpgrader:
    """Thin wrapper that delegates to src.firmware.bulk_ap_upgrader."""
    def __init__(self, org_id, sites_override=None, dry_run=False):
        self.org_id = org_id
        self.sites_override = sites_override
        self.dry_run = dry_run

    def execute(self):
        from src.firmware.bulk_ap_upgrader import BulkAPFirmwareUpgrader as _Impl
        upgrader = _Impl(
            org_id=self.org_id,
            apisession=apisession,
            sites_override=self.sites_override,
            dry_run=self.dry_run,
            safe_input_fn=InputUtils.safe_input,
            check_stop_fn=ConfigUtils.check_stop_signal,
            fetch_sites_fn=APICoreFetchUtils.all_sites_with_limit,
            get_csv_path_fn=FilePathUtils.get_csv_path,
            check_firmware_status_fn=lambda: FirmwareManager.create(
                apisession, ConfigUtils.get_cached_or_prompted_org_id()
            ).check_firmware_upgrade_status(),
            get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
        )
        upgrader.execute()
```

**After**:

```python
class BulkAPFirmwareUpgrader:
    """Thin wrapper that delegates to src.firmware.bulk_ap_upgrader."""
    def __init__(self, org_id, sites_override=None, dry_run=False):
        # Wrapper's external contract is unchanged — menu 195 still passes 3 args
        self.org_id = org_id
        self.sites_override = sites_override
        self.dry_run = dry_run

    def execute(self):
        from src.firmware.bulk_ap_upgrader import (
            BulkAPFirmwareUpgrader as _Impl,
            BulkAPUpgraderConfig,
        )
        config = BulkAPUpgraderConfig(               # Build config once from wrapper state + globals
            org_id=self.org_id,
            apisession=apisession,
            sites_override=self.sites_override,
            dry_run=self.dry_run,
            safe_input_fn=InputUtils.safe_input,
            check_stop_fn=ConfigUtils.check_stop_signal,
            fetch_sites_fn=APICoreFetchUtils.all_sites_with_limit,
            get_csv_path_fn=FilePathUtils.get_csv_path,
            check_firmware_status_fn=lambda: FirmwareManager.create(
                apisession, ConfigUtils.get_cached_or_prompted_org_id()
            ).check_firmware_upgrade_status(),
            get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,
        )
        _Impl(config).execute()                       # Single-arg constructor call
```

The wrapper's own signature is unchanged — `firmware_manager.py:1463` continues to work without modification (it targets the wrapper, not the impl).

### Caller 2: `tests/unit/test_bulk_ap_upgrader.py:69-83` (`_make_upgrader` factory)

**Before**:

```python
def _make_upgrader(**kwargs):
    defaults = {
        "org_id": "org-123",
        "apisession": MagicMock(),
        "dry_run": True,
        "safe_input_fn": MagicMock(return_value=""),
        "check_stop_fn": MagicMock(return_value=False),
        "fetch_sites_fn": MagicMock(return_value=[SAMPLE_SITE]),
        "get_csv_path_fn": MagicMock(return_value=None),
        "check_firmware_status_fn": MagicMock(),
        "get_org_id_fn": MagicMock(return_value="org-123"),
    }
    defaults.update(kwargs)
    return BulkAPFirmwareUpgrader(**defaults)
```

**After**:

```python
def _make_upgrader(**kwargs):
    defaults = {
        "org_id": "org-123",
        "apisession": MagicMock(),
        "dry_run": True,
        "safe_input_fn": MagicMock(return_value=""),
        "check_stop_fn": MagicMock(return_value=False),
        "fetch_sites_fn": MagicMock(return_value=[SAMPLE_SITE]),
        "get_csv_path_fn": MagicMock(return_value=None),
        "check_firmware_status_fn": MagicMock(),
        "get_org_id_fn": MagicMock(return_value="org-123"),
    }
    defaults.update(kwargs)                                  # Preserve per-test override semantics
    config = BulkAPUpgraderConfig(**defaults)                # Build immutable config from merged dict
    return BulkAPFirmwareUpgrader(config)                    # Single-arg construction
```

Test bodies (`TestInit.*`, `TestExecute.*`, etc.) require no changes — they call `_make_upgrader(...)` and get an instance back, exactly as before.

---

## Contract Violation Signals

If any of the following are observed after the refactor, the contract is broken and the refactor MUST be reverted or fixed:

- `menu 195` in production launches menu but raises `TypeError` at bulk-AP-upgrader construction.
- `pytest tests/unit/test_bulk_ap_upgrader.py` returns non-zero.
- `python -m py_compile src/firmware/bulk_ap_upgrader.py` returns non-zero.
- `python -m ruff check src/firmware/bulk_ap_upgrader.py` reports any error or warning.
- A reviewer greps for `_step1_` through `_step11_` and finds any step is not called, called out of order, or called more than once per `execute()`.

---

## Non-Contract (explicitly out of scope)

- Internal helper method names (`_init_session_ctx`, `_run_discovery_phase`, etc.) are NOT part of any contract. They may be renamed in future refactors without notice.
- The exact string content of INFO/DEBUG log messages is NOT a contract, provided the messages remain ASCII (FR-008) and the info-before / debug-after pattern is preserved (FR-007).
- The dataclass field order within `BulkAPUpgraderConfig` MAY be reordered for readability, but existing callers using keyword arguments are unaffected.
