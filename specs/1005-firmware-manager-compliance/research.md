# Phase 0 Research: Firmware Manager Compliance Refactor

**Feature**: `refactor/firmware-manager-compliance`
**Purpose**: Resolve all open questions before Phase 1 design. Every decision is traceable to a spec FR/SC/NG and to the compliance-analyzer rule it addresses.

---

## R-1: Backward-Compatibility Strategy for the 8-Parameter Constructor

### Context

The current signature is:

```python
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
```

Eight parameters trip STRUCT-PARAMS (threshold 5) and — because two of the eight are positional required (`apisession`, `org_id`) while six are keyword-optional dependency-injection hooks — the parameter list is also difficult to reason about.

Six MistHelper.py callsites all funnel through `FirmwareManager.create(apisession, org_id)` (the factory at lines 18785-18807), which constructs the class with the full 8-kwarg call. This is exactly the insulation pattern the 1004 prior-art work established.

### Options Considered

**Option A** — Keep the 8-kwarg signature, suppress STRUCT-PARAMS with a threshold-relaxation config knob.
- **Rejected**: violates NG-004 (no compliance-threshold relaxations) and NG-009 (no `# noqa` / suppressions). Would not reach A+/100.

**Option B** — Dual-mode: accept either 8 kwargs (deprecated) or a `FirmwareManagerConfig` (new).
- **Rejected**: doubles the constructor logic, adds a runtime branch, and leaves the STRUCT-PARAMS finding in place until the deprecation cutover completes. No downstream benefit vs. Option C given the six-callsite insulation.

**Option C** — Collapse to a single `FirmwareManagerConfig` positional parameter (frozen `slots=True` dataclass). Update the six-callsite factory wrapper.
- **Selected**. Reduces params from 8 to 1 (well under threshold 5). Matches 1004 precedent exactly. All six callsites already route through `FirmwareManager.create`, so only the factory body needs to change.

### Decision

Adopt **Option C**. Create `FirmwareManagerConfig` in the same module. Signature becomes `def __init__(self, config: FirmwareManagerConfig) -> None:`. The MistHelper.py factory at lines 18791-18807 constructs a `FirmwareManagerConfig(...)` and passes it to `FirmwareManager(config)`.

### Rationale

- Single positional param aligns with STRUCT-PARAMS threshold 5.
- Frozen + `slots=True` makes the config value-immutable — prevents accidental mutation of injected callables mid-flow.
- Matches the 1004 template so reviewers see one consistent pattern across the firmware campaign.
- Zero-cost migration: only the six-callsite factory wrapper body changes; the callsites themselves (`FirmwareManager.create(apisession, org_id)`) are untouched.

**Spec traceability**: FR-011 (only permitted MistHelper.py diff), FR-014 (frozen config-object contract).

---

## R-2: `__init__` Decomposition and Module-Global Preservation

### Context

The current `__init__` does more than parameter unpacking. It also mutates four module-level globals:

- `msp_privileges` — cached list used by `_select_msps_for_upgrade`.
- `apisession` — bound at module scope for cross-function reuse.
- `org_id` — same as above.
- `PROGRESS_EMITTER` — the module-level progress hook used by the `execute` entry point.

If we collapse to `def __init__(self, config): ...` and stop there, we break those four module-global consumers.

### Decision

Introduce a private module-level helper `_bind_module_globals(config: FirmwareManagerConfig) -> None` that performs the four bindings via `sys.modules[__name__]` attribute-setting. Call it once from `__init__`. Add `# WHY:` inline comments on every executable line.

Structure:

```python
def _bind_module_globals(config: FirmwareManagerConfig) -> None:
    # WHY: preserve the pre-refactor module-level surface consumed by helpers
    module = sys.modules[__name__]                      # WHY: get this module object for attribute binding
    module.apisession = config.apisession               # WHY: rebinds the module-scope api session
    module.org_id = config.org_id                       # WHY: rebinds the org id used by helpers
    module.PROGRESS_EMITTER = _make_progress_emitter()  # WHY: refresh emitter for this instance
    module.msp_privileges = []                          # WHY: reset cached msp list per instance
```

The `_bind_module_globals` call becomes the sole side-effecting statement in `__init__`; everything else is attribute assignment from the config.

### Rationale

- Isolates the side effects into one auditable helper (analyzable independently).
- Keeps `__init__` under 15 lines and CC `<=3` (well under STRUCT-COMPLEXITY threshold).
- Preserves exact pre-refactor behavior for all downstream module-global consumers (FR-017 no-behavior-change).

**Spec traceability**: FR-004 (constructor collapse), FR-005 (module-global preservation), FR-017 (no behavior change).

---

## R-3: `execute`-Style Entry Point Decomposition (HIGH-Severity STRUCT-LENGTH)

### Context

Four HIGH-severity STRUCT-LENGTH offenders each exceed 90 lines:

1. `check_firmware_upgrade_status` — ~110 lines, CC 9.
2. `_continuous_monitoring_mode` — ~95 lines.
3. `_upgrade_ap_firmware_by_gateway_template` — ~100 lines.
4. `_execute_msp_upgrade_plan` — ~95 lines, CC 10.

All four follow the same shape: prompt user -> fetch API data -> compute plan -> present preview -> execute (or dry-run) -> log/persist results.

### Decision

Apply the **PCPP pattern** (Prepare / Compute / Present / Persist) to each:

- `_prepare_<action>_context(...)` — collect inputs, resolve site/org/msp IDs, produce a dataclass or namedtuple.
- `_compute_<action>_plan(context)` — pure computation over the prepared context (no I/O), returns the plan.
- `_present_<action>_preview(plan)` — user-facing print + confirmation prompt (uses `safe_input(context=...)`).
- `_persist_<action>_results(plan, response)` — CSV / log / recap.

Each helper `<=25` lines and `<=5` blocks. The original method becomes a thin orchestrator that calls the four helpers in sequence.

### Example — `check_firmware_upgrade_status` -> orchestrator + 4 helpers:

```python
def check_firmware_upgrade_status(self) -> None:
    # WHY: PCPP orchestrator for status-check flow
    logging.info("Starting firmware upgrade status check for org %s", self._config.org_id)
    context = self._prepare_status_check_context()      # WHY: gather sites, filter for upgradable
    plan = self._compute_status_check_plan(context)     # WHY: pure derivation of per-site status
    self._present_status_check_preview(plan)            # WHY: user-visible summary
    self._persist_status_check_results(plan)            # WHY: CSV + logfile
    logging.debug("Status check completed for %d sites", len(plan.sites))
```

### Rationale

- Removes all four HIGH STRUCT-LENGTH findings in one pass.
- Introduces zero new behavior — the four helpers execute in the same order as the original method's four visible phases.
- Analyzable independently (each PCPP helper is a candidate for future extension without touching the orchestrator).

**Spec traceability**: FR-002 (STRUCT-LENGTH `<=25`), FR-003 (STRUCT-COMPLEXITY `<=5` blocks), FR-017 (no behavior change), SC-001 (HIGH count 0).

---

## R-4: MEDIUM-Severity STRUCT-LENGTH / STRUCT-COMPLEXITY (PCPP for the Long Tail)

### Context

The remaining 32 MEDIUM STRUCT-LENGTH offenders and 27 STRUCT-COMPLEXITY findings (CC 6-10 at 27 more sites) share the same PCPP shape but at smaller scale.

### Decision

Apply the PCPP pattern verbatim — same four helper suffixes (`_prepare_...`, `_compute_...`, `_present_...`, `_persist_...`). For methods where one phase is missing (e.g., pure `_compute_*` selectors with no user output), omit the missing phase.

For STRUCT-COMPLEXITY hotspots at CC 9-10:

- `_select_msps_for_upgrade` (CC 10) — split into `_prepare_msp_candidate_list` + `_compute_msp_selection_from_input` + `_present_msp_confirmation`.
- `_select_orgs_for_upgrade` (CC 10) — mirror decomposition.
- `_handle_ssr_upgrade_error_response` (CC 10) — split by HTTP status code family into `_handle_client_error`, `_handle_server_error`, `_handle_unexpected_error` helpers.

Each resulting helper `<=5` block-count and CC `<=5`.

### Rationale

- One pattern applied uniformly — reviewer builds mental model once.
- Preserves per-method call ordering (helpers invoked in original visible sequence).

**Spec traceability**: FR-002, FR-003, SC-002 (MEDIUM STRUCT-LENGTH count 0), SC-003 (STRUCT-COMPLEXITY count 0).

---

## R-5: Inline-Comment Strategy (`# WHY:` on Every Executable Line)

### Context

Current inline-comment coverage is **6.3%** (85 / 1348 executable lines). The Constitution VI + spec SC-009 target is **90%+**; the analyzer threshold for CONV-COMMENTS is 80%.

### Decision

For every executable line (including single-statement lines, list comprehensions, conditional branches, and `return`s), attach an inline comment in the form `# WHY: <intent>`. Comments explain **purpose**, not mechanics.

- **Bad**: `x = x + 1  # increment x`
- **Good**: `x = x + 1  # WHY: advance to next retry attempt in exponential backoff`

For multi-line statements (long function calls split across lines), attach the `# WHY:` to the trailing line only.

For pure structural lines (blank lines, dataclass field definitions inside an `@dataclass` block, `pass` in an except-suppress block), no comment is required — the analyzer excludes these from the executable-line count.

### Rationale

- Uniform `# WHY:` prefix is grep-friendly (`grep -c "# WHY:" src/firmware/firmware_manager.py` gives a fast coverage estimate).
- Constitution VI is explicit that comments explain *why*, not *what*.
- 90% target leaves a small buffer above the 80% analyzer threshold to absorb future line insertions during maintenance.

**Spec traceability**: FR-006 (inline coverage), SC-009 (90%+ coverage), Constitution VI.

---

## R-6: Testing Strategy (No New Test Files)

### Context

Spec NG-001 forbids new test files under `tests/unit/test_firmware_manager*.py`. No pre-existing unit tests target this module.

### Decision

The compliance analyzer + `ruff` + `py_compile` form the primary gates. Optional REPL constructor smoke (per `quickstart.md` Step 6) exercises the frozen-config contract manually.

- **Gate 1** — `python -m py_compile src/firmware/firmware_manager.py` must succeed.
- **Gate 2** — `python -m ruff check src/firmware/firmware_manager.py` must exit 0.
- **Gate 3** — `python -m tools.compliance_analyzer src/firmware/firmware_manager.py` must report `Score: 100.0`, `Grade: A+`, zero HIGH/MEDIUM/LOW findings.
- **Gate 4** — six-callsite grep smoke: `grep -n "FirmwareManager.create\|FirmwareManager(" MistHelper.py` returns exactly the pre-refactor set (one class-def at line 18789, one impl-import at 18795, one static-method def at 18791, plus five call-sites at 19809/22097/22154/22237/22246).
- **Gate 5** (optional) — REPL smoke: construct via `FirmwareManagerConfig`, verify frozen mutation raises `FrozenInstanceError`, verify legacy positional call raises `TypeError`.

### Rationale

- Analyzer at 100.0 is a stronger guarantee than any unit-test suite for the compliance dimension.
- Six-callsite grep smoke is the cheapest possible integration check.
- Skipping new test files honors NG-001 while keeping the review surface small.

**Spec traceability**: NG-001 (no new test files), SC-004 (analyzer 100.0/A+), FR-011 (only MistHelper.py 18791-18807 diff outside target file).

---

## R-7: STRUCT-NESTING Flattening (Early-Return Guards)

### Context

Two STRUCT-NESTING findings at:

- Line 750 — a triple-nested `if / for / if` inside `_upgrade_ap_firmware_by_gateway_template`.
- Line 1740 — a triple-nested `if / try / for` inside `_continuous_monitoring_mode`.

Both exceed the analyzer threshold of nesting depth 3.

### Decision

Replace the outer nesting layer with **early-return guards**:

- Line 750 pattern:
    - Before: `if <outer>: for <items>: if <inner>: ...`
    - After: `if not <outer>: return early_result` -> `for <items>:` -> `if not <inner>: continue` -> flat body.
- Line 1740 pattern:
    - Before: `if <ok>: try: ... except: ... for <sites>: if <due>: ...`
    - After: `if not <ok>: return` -> extract try/except into helper -> `for <sites>: if not <due>: continue` -> flat body.

### Rationale

- Standard Kernighan-style flattening — well-understood by reviewers.
- Adds two lines total (the early-return guards) but eliminates two nesting-depth violations.

**Spec traceability**: FR-002 (STRUCT-NESTING `<=3`), SC-011 (STRUCT-NESTING count 0).

---

## R-8: CONV-NAME Loop-Variable Renames

### Context

Three `for r in <collection>:` loops at lines 1364, 1373, 1381 (all inside `_split_results_by_status`) use the single-letter name `r`. CONV-NAME requires variable names >=2 chars unless conventional (like `i`/`j` in numeric loops).

### Decision

Rename per context:

- Line 1364 (`for r in results:` iterating upgrade-status API responses) -> `for result in results:`.
- Line 1373 (`for r in records:` iterating parsed CSV rows) -> `for record in records:`.
- Line 1381 (`for r in report_rows:` building the final output table) -> `for report_row in report_rows:`.

### Rationale

- Names now match the loop-body operations reader would expect.
- Zero behavior change; pure textual substitution.

**Spec traceability**: FR-009 (CONV-NAME `>=2` chars), SC-012 (CONV-NAME count 0).

---

## R-9: Six-Callsite Factory-Wrapper Insulation Verification

### Context

Spec FR-011 permits only `MistHelper.py` lines 18791-18807 (the `FirmwareManager.create` factory body) as an off-file diff. That is only viable if every downstream MistHelper.py callsite already routes through `FirmwareManager.create(apisession, org_id)`.

### Decision

Verified via `grep -n "FirmwareManager\." MistHelper.py`:

| Line | Site | Contract |
|------|------|----------|
| 18789 | `class FirmwareManager:` (factory-wrapper class definition) | Definition, no change. |
| 18791 | `@staticmethod` decorator on `create` | No change. |
| 18795 | `from src.firmware.firmware_manager import FirmwareManager as _Impl` inside `create` | No change (import line only). |
| 18797-18807 | Factory body (kwargs construction of `_Impl(...)`) | **THIS IS THE PERMITTED DIFF**. Replace kwargs with `FirmwareManagerConfig(...)` and single positional call. |
| 19809 | `FirmwareManager.create(apisession, org_id)` inside menu 196 handler | No change. |
| 22097 | `FirmwareManager.create(apisession, org_id)` inside SSR upgrade path | No change. |
| 22154 | `FirmwareManager.create(apisession, org_id)` inside AP fleet upgrade path | No change. |
| 22237 | `FirmwareManager.create(apisession, org_id)` inside MSP-org bulk path | No change. |
| 22246 | `FirmwareManager.create(apisession, org_id)` inside status-check menu | No change. |

All five call-sites (19809/22097/22154/22237/22246) use the identical `FirmwareManager.create(apisession, org_id)` shape. Insulation confirmed — no downstream MistHelper.py changes required.

### Rationale

- The 1004 prior-art work established this pattern; the identical structure applies here.
- No callsite-level ripple, no test-file update, no menu-flow change.

**Spec traceability**: FR-011 (only 18791-18807 diff), FR-017 (no observable behavior change at callsites).

---

## Consolidated Decisions

| # | Decision | Rationale | Spec Refs |
|---|----------|-----------|-----------|
| R-1 | Frozen `slots=True` `FirmwareManagerConfig` collapses 8 params -> 1 | Matches 1004 precedent; single-callsite factory-wrapper diff | FR-011, FR-014 |
| R-2 | `_bind_module_globals(config)` helper preserves module-global surface | Keeps `__init__` under STRUCT-LENGTH/COMPLEXITY thresholds; isolates side effects | FR-004, FR-005, FR-017 |
| R-3 | PCPP decomposition for 4 HIGH STRUCT-LENGTH offenders | One pattern across all four >90-line methods | FR-002, FR-003, SC-001 |
| R-4 | Same PCPP pattern for 32 MEDIUM STRUCT-LENGTH + 27 STRUCT-COMPLEXITY | Uniform reviewer mental model | FR-002, FR-003, SC-002, SC-003 |
| R-5 | `# WHY: <intent>` on every executable line, coverage >=90% | Constitution VI compliance; grep-friendly audit | FR-006, SC-009 |
| R-6 | Analyzer + ruff + py_compile as gates; no new test files | Honors NG-001; stronger than unit tests for compliance | NG-001, SC-004 |
| R-7 | Early-return guards at lines 750 and 1740 | Kernighan flattening; two-line change per site | FR-002, SC-011 |
| R-8 | Rename `r` -> `result`/`record`/`report_row` at 1364/1373/1381 | Names match loop-body intent | FR-009, SC-012 |
| R-9 | Six-callsite factory-wrapper insulation confirmed | Only 18791-18807 diff needed outside target file | FR-011, FR-017 |

**Every NEEDS CLARIFICATION resolved. Ready for Phase 1 design.**
