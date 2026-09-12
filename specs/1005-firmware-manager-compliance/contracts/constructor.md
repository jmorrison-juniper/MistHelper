# Constructor Contract: FirmwareManager.__init__

**Feature**: `refactor/firmware-manager-compliance`
**Purpose**: Nail down the exact pre-/post-refactor signature contract for `FirmwareManager` construction and enumerate the invariants that must hold before merge.

---

## Pre-Refactor Signature (current)

```python
# src/firmware/firmware_manager.py (line 61-70)
class FirmwareManager:
    def __init__(
        self,
        apisession: Any,
        org_id: str,
        safe_input_fn: SafeInputFn | None = None,
        select_site_fn: SelectSiteFn | None = None,
        check_cache_fn: CheckCacheFn | None = None,
        get_csv_path_fn: GetCsvPathFn | None = None,
        gateway_templates_fn: GeneratorFn | None = None,
        sites_fn: GeneratorFn | None = None,
    ) -> None:
        ...
```

**Parameter count**: 8 (2 required positional + 6 keyword-optional). **STRUCT-PARAMS violation** (threshold 5).

**Callable via**:
- `FirmwareManager(apisession, org_id)` — bare identity.
- `FirmwareManager(apisession, org_id, safe_input_fn=..., ...)` — full DI form used by the MistHelper.py factory at line 18797.
- Positional-arg construction beyond the first two (e.g., `FirmwareManager(a, o, some_fn)`) — technically legal but not exercised anywhere in the codebase.

---

## Post-Refactor Signature (target)

```python
# src/firmware/firmware_manager.py (new)
@dataclass(frozen=True, slots=True, kw_only=True)
class FirmwareManagerConfig:
    apisession: Any
    org_id: str
    safe_input_fn: Optional[SafeInputFn] = None
    select_site_fn: Optional[SelectSiteFn] = None
    check_cache_fn: Optional[CheckCacheFn] = None
    get_csv_path_fn: Optional[GetCsvPathFn] = None
    gateway_templates_fn: Optional[GeneratorFn] = None
    sites_fn: Optional[GeneratorFn] = None


class FirmwareManager:
    def __init__(self, config: FirmwareManagerConfig) -> None:
        ...
```

**Parameter count**: 1 (well under STRUCT-PARAMS threshold 5).

**Callable via**:
- `FirmwareManager(config)` — the sole supported form.
- **All legacy multi-positional / multi-kwarg calls MUST raise `TypeError`.** (This is enforced by Python's arity check on `__init__`.)

---

## Contract Invariants

| # | Invariant | Enforcement | Verification |
|---|-----------|-------------|--------------|
| C-1 | `FirmwareManager(config)` succeeds when `config` is a valid `FirmwareManagerConfig`. | Class `__init__` accepts exactly one positional argument. | Quickstart Step 6 REPL positive-case block. |
| C-2 | `FirmwareManager("org", apisession, ...)` (legacy positional) raises `TypeError`. | Python arity check — new `__init__` takes 2 positional args (`self`, `config`); passing 3+ triggers `TypeError: __init__() takes 2 positional arguments but N were given`. | Quickstart Step 6 REPL negative-case block. |
| C-3 | `FirmwareManager(apisession=..., org_id=..., ...)` (legacy kwargs) raises `TypeError`. | Python unexpected-keyword check — `__init__` has no `apisession`/`org_id`/`*_fn` keywords, so any keyword raises `TypeError: __init__() got an unexpected keyword argument '<name>'`. | Quickstart Step 6 REPL negative-case block. |
| C-4 | `FirmwareManagerConfig` instances are immutable. | `@dataclass(frozen=True)` — attribute assignment raises `FrozenInstanceError`. | Quickstart Step 6 REPL immutability block. |
| C-5 | `FirmwareManagerConfig` rejects invalid identity fields at construction time. | `__post_init__` validates `apisession is not None` and `isinstance(org_id, str) and org_id`. | Quickstart Step 6 REPL validation block (optional extension). |
| C-6 | Observable behavior at all six MistHelper.py callsites is identical to pre-refactor. | Only the factory body at MistHelper.py lines 18791-18807 changes; the five downstream callsites (19809/22097/22154/22237/22246) are byte-identical. | `grep -n "FirmwareManager.create" MistHelper.py` returns exactly 5 non-definition matches, all `FirmwareManager.create(apisession, org_id)`. |

---

## Caller-Site Contract Changes

### Site 1: MistHelper.py lines 18791-18807 (the ONLY permitted diff)

**Before** (17 lines including class def):

```python
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
```

**After** (~20 lines):

```python
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

**Diff scope**: import statement expanded to two-name form, and the `_Impl(...)` call replaced with `FirmwareManagerConfig(...)` construction + single-positional `_Impl(config)`.

**Contract**: the static-method signature `FirmwareManager.create(apisession: Any, org_id: str) -> Any` **does not change**. Callers see identical behavior.

### Sites 2-6: MistHelper.py lines 19809, 22097, 22154, 22237, 22246

**All five sites**:

```python
firmware_manager = FirmwareManager.create(apisession, org_id)
```

**Change**: **NONE**. These lines are byte-identical before and after.

Verified via:

```bash
grep -n "FirmwareManager\.create" MistHelper.py
```

Expected pre- and post-refactor output (identical):

```
18797:    def create(apisession: Any, org_id: str) -> Any:
19809:        firmware_manager = FirmwareManager.create(apisession, org_id)
22097:    firmware_manager = FirmwareManager.create(apisession, org_id)
22154:    firmware_manager = FirmwareManager.create(apisession, org_id)
22237:    firmware_manager = FirmwareManager.create(apisession, org_id)
22246:    firmware_manager = FirmwareManager.create(apisession, org_id)
```

### Sites outside MistHelper.py

**None**. Grep for cross-repo consumers:

```bash
grep -rn "from src.firmware.firmware_manager import" --include="*.py" .
```

Expected: exactly one match — `MistHelper.py` line 18795 (inside the factory body, the sole import). No other Python file in the repo imports this module.

---

## Import Contract

**Pre-refactor** — the module exposes:

```python
# Public class (used via MistHelper.py factory)
FirmwareManager

# Type aliases (used only internally)
SafeInputFn, SelectSiteFn, CheckCacheFn, GetCsvPathFn, GeneratorFn
```

**Post-refactor** — the module exposes:

```python
# Public class + config dataclass (both used via MistHelper.py factory)
FirmwareManager, FirmwareManagerConfig

# Type aliases (used by FirmwareManagerConfig field annotations + internal helpers)
SafeInputFn, SelectSiteFn, CheckCacheFn, GetCsvPathFn, GeneratorFn
```

**Addition**: `FirmwareManagerConfig` becomes importable. No name is removed. Legacy import `from src.firmware.firmware_manager import FirmwareManager` continues to work.

---

## Backward Compatibility Verdict

**Not backward-compatible at the class-constructor level.**

The refactor intentionally breaks the pre-refactor 8-parameter constructor to force a compile-time fail-fast for any hypothetical direct-instantiation site. Given the six-callsite factory-wrapper insulation (R-9 in `research.md`), only the wrapper body needs updating and no in-repo caller is affected.

**Backward-compatible at the factory-static-method level.**

`FirmwareManager.create(apisession, org_id)` returns the same object shape (`FirmwareManager` instance with same public attribute surface — `self.org_id`, `self.apisession`, and all pre-existing method names). The five downstream MistHelper.py callsites, all their menu flows, and all their log lines remain identical (FR-017).

---

## Failure-Mode Diagnostics

If a future caller reintroduces a legacy call form, Python produces one of these clear errors:

| Legacy Call | Error |
|-------------|-------|
| `FirmwareManager("org", session, dry_run=True)` | `TypeError: __init__() takes 2 positional arguments but 3 were given` |
| `FirmwareManager(apisession=s, org_id="o")` | `TypeError: __init__() got an unexpected keyword argument 'apisession'` |
| `FirmwareManager(config, extra)` | `TypeError: __init__() takes 2 positional arguments but 3 were given` |
| `config.apisession = MagicMock()` | `dataclasses.FrozenInstanceError: cannot assign to field 'apisession'` |
| `config.new_attr = 1` | `AttributeError: 'FirmwareManagerConfig' object has no attribute 'new_attr'` (from `slots=True`) |

All five failure modes are auditable via the Quickstart Step 6 REPL smoke.

---

## Summary

- One new type in the module (`FirmwareManagerConfig`) and one changed constructor signature.
- Six invariants (C-1 through C-6) enumerate the observable contract.
- Only the MistHelper.py factory body at 18791-18807 changes; all five downstream callsites are byte-identical.
- Failure-mode diagnostics are clear and grep-friendly.
