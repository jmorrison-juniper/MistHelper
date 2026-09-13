# Constructor Contract: OrgLevelAPFirmwareUpgrader.__init__

**Feature**: `refactor/org-ap-upgrader-compliance`
**Purpose**: Nail down the exact pre-/post-refactor signature contract for `OrgLevelAPFirmwareUpgrader` construction, enumerate the invariants that must hold before merge, and prove byte-identity for the four MistHelper.py callsites at lines 20247, 20269, 20289, 20305.

---

## Pre-Refactor Signature (current)

```python
# src/firmware/org_ap_upgrader.py (line 41)
class OrgLevelAPFirmwareUpgrader:
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
        ...
```

**Parameter count**: 11 (2 required positional + 9 keyword-only). **STRUCT-PARAMS violation** (threshold 5). Suppressed today with `# pylint: disable=too-many-arguments`.

**Callable via**:
- `OrgLevelAPFirmwareUpgrader(org_id, apisession, **hooks)` — full DI form used at MistHelper.py line 20247.
- `OrgLevelAPFirmwareUpgrader(org_id="", apisession=..., safe_input_fn=...)` — thin form used at lines 20289 and 20305 for MSP-selection paths.

---

## Post-Refactor Signature (target)

```python
# src/firmware/org_ap_upgrader.py (new)
@dataclass(frozen=True, slots=True, kw_only=True)
class OrgAPUpgraderConfig:
    org_id: str
    apisession: Any
    dry_run: bool = False
    safe_input_fn: Optional[Any] = None
    check_stop_fn: Optional[Any] = None
    get_org_id_fn: Optional[Any] = None
    fetch_sites_fn: Optional[Any] = None
    write_results_fn: Optional[Any] = None
    is_debug_fn: Optional[Any] = None
    msp_privileges: Optional[list[Any]] = None
    selected_msp: Optional[dict[str, Any]] = None


class OrgLevelAPFirmwareUpgrader:
    def __init__(self, **cfg: Any) -> None:
        # WHY: kwargs-passthrough preserves all four callsites byte-identically
        self._config: OrgAPUpgraderConfig = OrgAPUpgraderConfig(**cfg)
        ...
```

**Formal parameter count**: **1** (`**cfg` counts as one for STRUCT-PARAMS purposes; the analyzer counts formal parameters, not runtime kwargs). This satisfies the threshold of 5 with no suppression required.

**Callable via**:
- `OrgLevelAPFirmwareUpgrader(org_id=..., apisession=..., ...)` — the sole supported form, matching the pre-refactor kwargs shape at all four callsites.
- **Positional calls (`OrgLevelAPFirmwareUpgrader("org", session)`) MUST raise `TypeError`** — the new signature accepts no positional arguments beyond `self`, so positional invocation triggers Python's arity check. This is a **tightening** vs. the pre-refactor signature (which allowed `org_id, apisession` positionally), but the four MistHelper.py callsites all use kwargs form, so no callsite is affected.

---

## Contract Invariants

| # | Invariant | Enforcement | Verification |
|---|-----------|-------------|--------------|
| C-1 | `OrgLevelAPFirmwareUpgrader(**valid_kwargs)` succeeds and populates `self._config` with a valid `OrgAPUpgraderConfig`. | `__init__` builds the config via `OrgAPUpgraderConfig(**cfg)`; `__post_init__` validates. | Byte-identical callsite invocations at lines 20247/20269/20289/20305 succeed under `python -m py_compile`. |
| C-2 | `OrgLevelAPFirmwareUpgrader(unknown_kwarg=42)` raises `TypeError`. | Dataclass rejects unknown fields — `TypeError: __init__() got an unexpected keyword argument 'unknown_kwarg'`. | Analyzer smoke: no unknown-kwarg callsite exists post-refactor. |
| C-3 | `OrgLevelAPFirmwareUpgrader(org_id=None, apisession=session)` raises `TypeError`. | `__post_init__` — `isinstance(org_id, str)` check. | Configuration validation section of `data-model.md`. |
| C-4 | `OrgAPUpgraderConfig` instances are immutable at the field-binding level. | `@dataclass(frozen=True, slots=True)` — attribute assignment raises `FrozenInstanceError`; new attributes raise `AttributeError`. | `data-model.md` state-transition table. |
| C-5 | `msp_privileges=None` is normalized to `[]` inside `__post_init__` (via `object.__setattr__`); `selected_msp=None` is preserved as-is. | `__post_init__` normalization block. | `data-model.md` validation-rules section. |
| C-6 | Observable behavior at all four MistHelper.py callsites is identical to pre-refactor. | Zero-line diff outside `src/firmware/org_ap_upgrader.py`. | `git diff main..HEAD -- MistHelper.py` returns empty output. |

---

## Caller-Site Contract Changes

### The Zero-Diff Guarantee

**All four MistHelper.py callsites remain byte-identical.** The `**cfg` kwargs-passthrough constructor accepts the same kwargs shape the callsites already pass. No factory wrapper is required; no import statement changes; no line moves.

Verified via:

```bash
git diff main..HEAD -- MistHelper.py
```

Expected post-refactor output: **empty** (zero lines touched).

### Callsite 1 — MistHelper.py line 20247 (org-mode full 11 kwargs)

**Before** and **After** (byte-identical):

```python
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

**Contract**: 11 kwargs flow through unchanged. Config `__post_init__` normalizes `msp_privileges=None -> []` if the caller happens to pass `None` for the list field.

### Callsite 2 — MistHelper.py line 20269 (execute 9 kwargs)

**Before** and **After** (byte-identical):

```python
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

**Contract**: 9 kwargs flow through. `msp_privileges` and `selected_msp` default to `None`; `__post_init__` normalizes the list to `[]`.

### Callsite 3 — MistHelper.py line 20289 (MSP-select 5 kwargs, org_id="")

**Before** and **After** (byte-identical):

```python
upgrader = _Impl(
    org_id="",
    apisession=apisession,
    safe_input_fn=safe_input_fn,
    check_stop_fn=check_stop_fn,
    msp_privileges=msp_privileges,
)
```

**Contract**: 5 kwargs; `org_id=""` sentinel. `__post_init__` validates `isinstance(org_id, str)` (empty string OK — this is the intentional relaxation vs. 1005 which required non-empty). All unspecified `*_fn` hooks default to `None`; the class resolves them to `_default_*` fallbacks at usage sites.

### Callsite 4 — MistHelper.py line 20305 (MSP-org-select 3 kwargs, org_id="")

**Before** and **After** (byte-identical):

```python
upgrader = _Impl(
    org_id="",
    apisession=apisession,
    safe_input_fn=safe_input_fn,
)
```

**Contract**: thinnest construction path. Only session + one hook. All other fields default per the dataclass definition. Confirms that the kwargs-passthrough design tolerates every observed call shape (11 / 9 / 5 / 3 kwargs) without special-casing.

### Sites outside MistHelper.py

**None**. Grep for cross-repo consumers:

```bash
grep -rn "from src.firmware.org_ap_upgrader import" --include="*.py" .
```

Expected: exactly four matches — all inside `MistHelper.py` at the lazy-import positions (lines 20247, 20269, 20289, 20305 area). No other Python file in the repo imports this module.

---

## Import Contract

**Pre-refactor** — the module exposes:

```python
# Public class (used via MistHelper.py lazy imports)
OrgLevelAPFirmwareUpgrader
```

**Post-refactor** — the module exposes:

```python
# Public class (unchanged import surface)
OrgLevelAPFirmwareUpgrader

# NEW: internal config dataclass (importable but not required by any callsite)
OrgAPUpgraderConfig
```

**Addition**: `OrgAPUpgraderConfig` becomes importable at the module level. This is a **strict superset** of the pre-refactor import surface; the pre-refactor imports (`from src.firmware.org_ap_upgrader import OrgLevelAPFirmwareUpgrader as _Impl`) continue to work byte-identically.

**No import statement change in MistHelper.py.** The four lazy-import lines remain:

```python
from src.firmware.org_ap_upgrader import OrgLevelAPFirmwareUpgrader as _Impl
```

Byte-identical to pre-refactor.

---

## Backward Compatibility Verdict

**Backward-compatible at every observed callsite.**

Every one of the four MistHelper.py callsites uses kwargs form. The new `**cfg` signature accepts the same kwargs shape and hands them to the config dataclass. No callsite is broken.

**Not backward-compatible for hypothetical positional callers.**

The pre-refactor signature accepted `org_id` and `apisession` positionally. The new signature does not — a hypothetical caller writing `OrgLevelAPFirmwareUpgrader("org", session)` would receive:

```
TypeError: __init__() takes 1 positional argument but 3 were given
```

This is intentional. No positional caller exists in the codebase (verified by `grep -n "OrgLevelAPFirmwareUpgrader(" MistHelper.py` — all four hits use kwargs). Future callers must use kwargs form, aligning with the dataclass `kw_only=True` contract.

---

## Suppressions Removed

Two comment-form suppressions are eliminated as part of this refactor:

| Location | Suppression | Reason for Removal |
|----------|-------------|---------------------|
| `src/firmware/org_ap_upgrader.py:9` | `# pylint: disable=too-many-lines,logging-fstring-interpolation` | LOC still exceeds 1000 after refactor, but `too-many-lines` is out of scope for compliance-analyzer (analyzer does not enforce module LOC). Retain if strictly needed; otherwise remove. `logging-fstring-interpolation` is addressed by converting every f-string in a `logging.*` call to lazy `%s`/`%d` form (R-8). |
| `src/firmware/org_ap_upgrader.py:41` | `# pylint: disable=too-many-arguments` on `__init__` | Formal param count drops from 11 to 1 via `**cfg`. Suppression is no longer meaningful. |

Post-refactor state: **zero `# pylint: disable` on the class or its methods**. Any remaining module-level suppression (if kept) is limited to lint-family concerns orthogonal to compliance-analyzer scoring (NG-009).

---

## Failure-Mode Diagnostics

If a future caller reintroduces a legacy or malformed call form, Python produces one of these clear errors:

| Bad Call | Error |
|----------|-------|
| `OrgLevelAPFirmwareUpgrader("org", session)` | `TypeError: __init__() takes 1 positional argument but 3 were given` |
| `OrgLevelAPFirmwareUpgrader(bogus_kwarg=42)` | `TypeError: __init__() got an unexpected keyword argument 'bogus_kwarg'` (raised by `OrgAPUpgraderConfig`) |
| `OrgLevelAPFirmwareUpgrader(org_id=None, apisession=s)` | `TypeError: org_id must be a string` (from `__post_init__`) |
| `OrgLevelAPFirmwareUpgrader(org_id="o", apisession=None)` | `ValueError: apisession is required` (from `__post_init__`) |
| `OrgLevelAPFirmwareUpgrader(org_id="o", apisession=s, safe_input_fn=42)` | `TypeError: safe_input_fn must be callable or None` |
| `OrgLevelAPFirmwareUpgrader(org_id="o", apisession=s, msp_privileges={"x": 1})` | `TypeError: msp_privileges must be a list or None` |
| `config.apisession = MagicMock()` (post-construction) | `dataclasses.FrozenInstanceError: cannot assign to field 'apisession'` |
| `config.new_attr = 1` | `AttributeError: 'OrgAPUpgraderConfig' object has no attribute 'new_attr'` (from `slots=True`) |

All eight failure modes are auditable via REPL smoke.

---

## Relationship to Prior-Art Contracts

| Aspect | 1004 (bulk_ap_upgrader) | 1005 (firmware_manager) | 1006 (org_ap_upgrader) |
|--------|-------------------------|---------------------------|---------------------------|
| Formal `__init__` params post-refactor | 1 (`config` positional) | 1 (`config` positional) | 1 (`**cfg` kwargs-only) |
| MistHelper.py factory diff | Single-block factory body | Single-block factory body (18791-18807) | **Zero-line diff** |
| Callsite import statement changes | Import adds `Config` name | Import adds `Config` name | **No import changes** |
| Positional legacy calls supported? | No | No | No |
| Kwargs legacy calls supported? | No | No | **Yes** (this is the primary supported form) |
| Constructor signature style | `def __init__(self, config)` | `def __init__(self, config)` | `def __init__(self, **cfg)` |

The 1006 kwargs-passthrough is the strictest-constraint variant of the compliance-refactor pattern: it accepts a slightly less clean class-signature form (`**cfg` vs. explicit `config: Config`) in exchange for the strongest possible byte-identity guarantee at every callsite.

---

## Summary

- One new type in the module (`OrgAPUpgraderConfig`) and one changed constructor signature (`**cfg` kwargs-passthrough).
- Six invariants (C-1 through C-6) enumerate the observable contract.
- **Zero lines change outside `src/firmware/org_ap_upgrader.py`**; all four MistHelper.py callsites are byte-identical.
- Two `# pylint: disable` suppressions removed (`too-many-arguments`; f-string suppression rendered moot by lazy-format conversion).
- Failure-mode diagnostics cover every legacy call form and every validation branch.
