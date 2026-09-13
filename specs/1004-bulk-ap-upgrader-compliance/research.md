# Phase 0 Research: Bulk AP Upgrader Compliance Refactor

**Feature**: `refactor/bulk-ap-upgrader-compliance`
**Date**: 2026-07-01
**Purpose**: Resolve every design NEEDS-CLARIFICATION before Phase 1 artifact generation.

---

## R-1: Backward-Compat Approach for the 10-Parameter Constructor

### Context

The current constructor signature at `src/firmware/bulk_ap_upgrader.py:43`:

```python
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
) -> None:
```

Two positional params (`org_id`, `apisession`), eight keyword-only params (everything after `*,`). Total: 10 params against the 5-param ceiling (Constitution I, FR-004).

### Known Callers (grep confirms exactly two direct constructor call sites)

| # | Call Site | Signature Used | Notes |
|---|-----------|----------------|-------|
| 1 | `MistHelper.py:19796` — production menu 195 (inside the thin wrapper class `BulkAPFirmwareUpgrader.execute`) | `_Impl(org_id=..., apisession=..., sites_override=..., dry_run=..., safe_input_fn=..., check_stop_fn=..., fetch_sites_fn=..., get_csv_path_fn=..., check_firmware_status_fn=..., get_org_id_fn=...)` | All 10 args passed as kwargs. |
| 2 | `tests/unit/test_bulk_ap_upgrader.py:83` — `_make_upgrader` factory | `BulkAPFirmwareUpgrader(**defaults)` where `defaults` is a dict of 9 kwargs (all except `apisession` which is present). | All args passed via `**kwargs`. |

Note on `src/firmware/firmware_manager.py:1463`: this line reads `BulkAPFirmwareUpgrader(self.org_id, sites_to_upgrade_override, dry_run=dry_run)` — but the class name bound at line 1460 is the **thin wrapper in `MistHelper.py:19783`**, not the implementation class. The wrapper's signature is `(org_id, sites_override=None, dry_run=False)`. This call site therefore does NOT hit the implementation constructor directly; it is insulated by the wrapper.

### Options Considered

**Option A**: Preserve positional/keyword signature; internally construct a config dataclass from the kwargs.
- Pros: Zero caller changes.
- Cons: Constructor still lists 10 parameters in its signature, so compliance analyzer still flags PARAM-COUNT even though internally the state uses a dataclass. Does NOT satisfy FR-004.

**Option B**: Replace constructor signature with `__init__(self, org_id, apisession, config: BulkAPUpgraderConfig)`. Update both direct callers to build the config object.
- Pros: 3 params total (well within 5). Satisfies FR-004. Both callers are in-repo and controllable in the same commit.
- Cons: Requires atomic multi-file commit.

**Option C**: Fold `org_id` and `apisession` into `BulkAPUpgraderConfig` too, so `__init__(self, config: BulkAPUpgraderConfig)`. Update both callers.
- Pros: 1 param total. Cleanest possible signature. All construction inputs travel through a single validated dataclass.
- Cons: Same atomic-commit requirement as Option B. Slightly more disruptive to the two call sites (they must add two more fields to their config-construction call).

### Recommendation

**Option C**. Rationale:

1. Both direct callers already live in this repository and both already pass every argument as a keyword — the migration cost is small and mechanical.
2. Option C leaves ZERO ambiguity for future readers about whether a param is "part of the config" or "special enough to be positional." Everything is in the config.
3. The compliance analyzer's PARAM-COUNT rule counts declared parameters, not dataclass field count. A 1-param `__init__` passes cleanly.
4. The `apisession` and `org_id` values are naturally part of "how this upgrader is configured for this run"; separating them was an accident of history, not a design choice.
5. If a future contributor adds an 11th parameter, they add a field to the dataclass instead of touching the constructor signature — the dataclass becomes the single point of extension.

**Rejected**: Option A (does not satisfy FR-004). Option B (acceptable fallback if a reviewer objects to folding `apisession` into the config on cognitive-load grounds; documented here so the fallback is pre-approved).

### Impact on Callers

- **`MistHelper.py:19796-19809`**: Replace the flat kwargs call with `config = BulkAPUpgraderConfig(org_id=..., apisession=apisession, sites_override=..., dry_run=..., safe_input_fn=..., ...)` then `_Impl(config).execute()`.
- **`tests/unit/test_bulk_ap_upgrader.py:69-83`**: Rewrite `_make_upgrader` to build a `BulkAPUpgraderConfig` from `defaults` and pass it. Kwargs passed to `_make_upgrader` still work via `defaults.update(kwargs)` — only the final construction line changes.

### Edge Case Coverage (from spec)

- **Legacy 10-positional call** (spec Edge Case 1): The new signature rejects positional args beyond `config`. Python itself raises `TypeError: __init__() takes 2 positional arguments but 11 were given` — this is the "fail fast with a clear TypeError" that the spec requires.
- **Keyword-only legacy callers** (spec Edge Case 2): Option (b) in the spec text — all in-repo callers updated in the same commit. This is the path chosen.

---

## R-2: `__init__` Helper Decomposition

### Context

Current `__init__` body: 62 lines (source lines 71-104 including blank lines and comments; ~30 executable lines). Violates the 25-line ceiling (FR-005).

### Design

Three private helpers, each with a clear scope, each ~8-12 executable lines, each with a distinct set of attributes to initialize:

1. **`_init_session_ctx(self, config: BulkAPUpgraderConfig) -> None`**
   Sets: `self.org_id`, `self.apisession`, `self.dry_run`, `self._input_fn` (with `or input` fallback), and the six injected callables (`_check_stop_fn`, `_fetch_sites_fn`, `_get_csv_path_fn`, `_check_firmware_status_fn`, `_get_org_id_fn`, `self.sites_override`).
   ~10 executable lines. One assignment per line, each with a `# WHY` inline comment.

2. **`_init_ap_and_site_state(self) -> None`**
   Sets: `self.sites_to_upgrade`, `self.all_sites_aps`, `self.all_aps`, `self.aps_by_model`, `self.ap_versions` (5 lines).
   Rationale: These are the "discovered inputs to the plan" — one conceptual bucket.

3. **`_init_plan_and_results_state(self) -> None`**
   Sets: `self.available_versions`, `self.model_version_ranges`, `self.upgrade_plan`, `self.skipped_already_at_target`, `self.upgrade_config`, `self.upgrade_ids`, `self.results`, `self.successful_upgrades`, `self.failed_upgrades` (9 lines).
   Rationale: These are the "plan and results" fields — one conceptual bucket. 9 lines is within the ceiling.

### Resulting `__init__` body

```python
def __init__(self, config: BulkAPUpgraderConfig) -> None:
    logging.info("Initializing BulkAPFirmwareUpgrader from config")
    self._init_session_ctx(config)              # Extract session + injected callables
    self._init_ap_and_site_state()              # Reset discovered-input state
    self._init_plan_and_results_state()         # Reset plan + results state
    logging.debug("BulkAPFirmwareUpgrader init complete; dry_run=%s", self.dry_run)
```

5 executable lines. Well within the ceiling. Each helper is <=25 lines and does real work (attribute assignment with inline commentary) — not a wrapper (FR-011).

### Why not "one big init helper"?

A single `_initialize_state` helper would still be a 30-line function that just moved the violation. Three helpers by conceptual grouping (session / discovered inputs / plan+results) each do real bounded work, and the grouping matches how the fields are used throughout the rest of the class.

---

## R-3: `execute` Decomposition

### Context

Current `execute()` method: source lines 106-137, contains 9 sequential `if not self._stepN_...(): return` branches plus a try/except. Violates the 5-logical-block ceiling (FR-012).

### Design

Group the 11 steps into 3 phases by responsibility, keeping the individual `_stepN_*` method names and ordering untouched (FR-015):

1. **`_run_discovery_phase(self) -> bool`** — steps 1-4 (`_step1_determine_sites`, `_step2_discover_aps`, `_step3_fetch_firmware_stats`, `_step4_fetch_available_firmware`). Returns `False` on early-exit; `True` on success.

2. **`_run_planning_phase(self) -> bool`** — steps 5-7 (`_step5_select_firmware_versions`, `_step6_configure_upgrade`, `_step7_confirm_upgrade`). Returns `False` on early-exit; `True` on success.

3. **`_run_execution_phase(self) -> None`** — steps 8-11 (`_step8_execute_upgrades`, `_step9_configure_auto_upgrade`, `_step10_offer_status_check`, `_step11_write_results`). No early-exit — these are terminal steps.

Additionally, extract the try/except header into:

4. **`_announce_start(self) -> None`** — the two logging.info lines plus the dry-run banner (lines 108-114).

### Resulting `execute` body

```python
def execute(self) -> None:
    """Execute the bulk AP firmware upgrade workflow."""
    self._announce_start()                              # Log start + dry-run banner
    try:
        if not self._run_discovery_phase():             # Steps 1-4 (site + AP + firmware discovery)
            return                                      # Early exit on any discovery failure
        if not self._run_planning_phase():              # Steps 5-7 (version + strategy + confirm)
            return                                      # Early exit on any planning failure
        self._run_execution_phase()                     # Steps 8-11 (execute + finalize; no early exit)
    except KeyboardInterrupt:
        print("\n Operation cancelled by user.")       # Preserve exact pre-refactor message text
        logging.info("Bulk AP firmware upgrade cancelled by user interrupt")
```

10 executable lines, 3 logical blocks (try + two early-return ifs). Passes the ceilings.

### Preserving observable behavior (FR-017)

- Every `_stepN_*` method is invoked in the same order.
- The dry-run banner is emitted at the same point in time (via `_announce_start`).
- The `KeyboardInterrupt` message text is byte-for-byte identical.
- The logging emissions from the phase helpers each get their own `logging.info` "phase start" and `logging.debug` "phase end" wrapper — this is NEW telemetry, and it is additive; it does not remove or change any existing log line.

---

## R-4: Shared Decomposition Pattern for the Remaining MEDIUM Offenders

### Context

FR-012 enumerates 10 offenders. Three (`execute`, `__init__`, and one covered by dedicated pattern) are addressed in R-2 and R-3. The remaining seven, plus `execute` itself, share a common shape: a large method that does (a) preparation / lookup, (b) core computation or iteration, (c) formatting / user output, (d) state mutation, (e) an early-return short-circuit.

Rather than design each independently, `tasks.md` should reference this shared pattern:

### The "Prepare / Compute / Present / Persist" (PCPP) pattern

For every offender in FR-012, split into up to four helpers:

- **`_prepare_<verb>_inputs`**: gather args, look up config, resolve names to IDs. Returns a small tuple/dict of inputs.
- **`_compute_<noun>`**: perform the actual work (filter, sort, group, API call). Returns a result.
- **`_present_<noun>`**: emit user-visible text (`print(...)`) and structured logs. Void return.
- **`_persist_<noun>` (optional)**: mutate `self.*` state or write files. Void return.

The public method then reads as a 4-6 line orchestrator: `inputs = self._prepare_x(); result = self._compute_x(inputs); self._present_x(result); self._persist_x(result); return result`.

### Application to each offender

| Method (pre-refactor line) | PCPP Slice |
|---------------------------|------------|
| `_select_strategy` (724, 43 lines) | prepare: read `_current_config`, model_ranges. compute: rank strategies by AP count. present: print strategy table + prompt. persist: store choice in `self.upgrade_config`. |
| `_estimate_api_calls` (850, 43 lines) | prepare: read plan. compute: multiply counts per strategy. present: print estimation table. persist: none (pure). |
| `_offer_additional_model_versions` (1297, 46 lines / 8 blocks) | prepare: enumerate models needing more versions. compute: filter available versions per model. present: prompt user per model. persist: extend `self.model_version_ranges`. |
| `_fetch_ap_model_families` (1231, 42 lines / 7 blocks) | prepare: build model list. compute: mistapi call. present: emit progress. persist: cache result on `self`. |
| `_configure_auto_upgrade_schedule` (1463, 38 lines) | prepare: read schedule input. compute: normalize to API shape. present: echo back to user. persist: store on `self.upgrade_config`. |
| `_step11_write_results` (1624, 50 lines) | prepare: build filename + header row. compute: build data rows. present: print summary. persist: write CSV. |
| `_apply_version_selection` (651, 34 lines) | prepare: read user choice. compute: match to available versions. present: echo selection. persist: update `self.upgrade_plan`. |
| `_upgrade_version_group` (1121, 34 lines) | prepare: build request body per model. compute: fire mistapi call (respect dry-run). present: log per-model status. persist: append to `self.upgrade_ids`. |
| `_log_upgrade_results` (1184, 34 lines) | prepare: collate success/fail counts. compute: format summary lines. present: print summary. persist: update `self.results`. |

Not every offender needs all four slices — some are pure computation, some are pure presentation. Any slice that would produce a <=3-line helper is inlined instead, to avoid the wrapper/delegator ban in FR-011.

### Ceiling per helper

Each PCPP slice is expected to be 8-15 executable lines. Any slice measured above 25 lines during implementation is re-split before the task is marked complete. The compliance analyzer is the arbiter.

---

## R-5: Inline-Comment Coverage Strategy

### Coverage math

- File is 1,673 lines pre-refactor. Approx 1,100 are executable (excluding docstrings, blank lines, comments-only lines, and closing punctuation).
- Current inline-comment coverage: 0.2% (roughly 2 executable lines carry `# ...` comments).
- Target: 80% (approximately 880 executable lines must carry a `# ...` comment).

### Approach

The refactor will touch approximately 60-70% of executable lines during decomposition — every constructor line, every touched offender method, every extracted helper, and every new phase-orchestration line. Applying `# WHY` inline comments to every touched line yields approximately 700-780 commented lines from touched code alone.

The remaining shortfall (~100-180 lines) is closed by:

1. Every executable line inside every new extracted helper (helpers are 100% inline-commented by construction because they are new code and Constitution VI applies).
2. Executable lines inside the 11 `_stepN_*` methods that already have step-level docstrings but no inline comments — these are on the boundary of "touched code" because the phase helpers in R-3 call them. Per Constitution VI's clause "When existing code is found lacking inline comments during any edit, comments MUST be added to the entire function or block being touched," the `_stepN_*` bodies must also receive inline comments. This yields the remaining coverage.

### Anti-scope-creep rule

Lines the refactor does NOT touch (e.g., utility methods far from the ten offenders, imports at the top of the file, module-level constants) are left uncommented. This is deliberate:

- FR-006 measures coverage across the file, not "every line."
- Empirically, the touched-line count above (~880) already meets the 80% floor without a sweeping file-wide comment pass.
- A file-wide comment pass would inflate the PR diff by roughly 3x with no corresponding compliance gain and would violate the spec's Edge Case that discourages scope-inflating changes.

### Estimated final coverage

Approximately 82-85%, comfortably clearing the 80% floor with a small margin against future ruff/analyzer rule tightening.

---

## R-6: Testing Strategy

### Correction to spec's stated assumption

The user's plan instructions said "no dedicated test file today (verify with `ls tests/*bulk*`)." Verification result:

```
$ ls tests/*bulk*        # returns nothing — tests/bulk_*.py does not exist
$ find tests -name '*bulk*'
tests/unit/test_bulk_ap_upgrader.py     # DOES exist, 644 lines, 88.2 KB
```

The test file exists at `tests/unit/test_bulk_ap_upgrader.py`. It is substantial (644 lines, 88 KB) and includes at least a `_make_upgrader` factory (line 69) and a `TestInit` class (line 91). It uses `**defaults` kwargs construction so the migration to `BulkAPUpgraderConfig` is confined to the factory function.

### Approach

1. **No new test file created.** The existing suite is the regression harness.
2. **Update `_make_upgrader` factory only.** It becomes: build a `BulkAPUpgraderConfig` from `defaults`, then call `BulkAPFirmwareUpgrader(config)`. Every `TestInit.*` test then exercises the new config-based init automatically.
3. **Acceptance gate is the four commands from FR-001, FR-002, FR-003, plus pytest:**
   - `python -m tools.compliance_analyzer src/firmware/bulk_ap_upgrader.py` — score >=80, grade >=B.
   - `python -m ruff check src/firmware/bulk_ap_upgrader.py` — zero errors, zero warnings.
   - `python -m py_compile src/firmware/bulk_ap_upgrader.py` — exit 0.
   - `python -m pytest tests/unit/test_bulk_ap_upgrader.py -v` — all existing tests pass without test-code modification beyond the `_make_upgrader` factory update.

Adding new tests is a follow-on feature (per spec Assumptions section).

### Risk

If `_make_upgrader` is the only test-code line that must change, but pytest still fails, the most likely cause is that a test constructs `BulkAPFirmwareUpgrader` directly (not through the factory). Task planning must include a `grep -n "BulkAPFirmwareUpgrader(" tests/` sweep before the refactor is declared complete, to catch any direct construction that bypasses the factory.

---

## Consolidated Decisions

| ID | Decision | Rationale | Alternatives Rejected |
|----|----------|-----------|----------------------|
| R-1 | Adopt Option C: single-param `__init__(self, config)` folding `org_id` and `apisession` into `BulkAPUpgraderConfig`. Update both callers in the same commit. | Cleanest 1-param signature; both callers are in-repo; leaves no ambiguity about which fields are config. | Option A (still 10 params in signature — fails FR-004). Option B (acceptable fallback if a reviewer objects to folding session args). |
| R-2 | 3-helper `__init__` decomposition: `_init_session_ctx`, `_init_ap_and_site_state`, `_init_plan_and_results_state`. | Each helper has a distinct conceptual bucket and 5-12 executable lines. No wrapper. | Single `_initialize` helper (just moves the violation). Two helpers (buckets end up unbalanced at 15 and 20 lines). |
| R-3 | 3-phase `execute` decomposition: `_run_discovery_phase` (steps 1-4), `_run_planning_phase` (steps 5-7), `_run_execution_phase` (steps 8-11), plus `_announce_start` for banner/logging. | Preserves 11-step order (FR-015). Reduces orchestrator to 10 lines, 3 blocks. | Splitting per step (4 helpers of 1 line each — that IS a wrapper). Splitting at try/except boundary only (still 8 blocks inside try). |
| R-4 | PCPP (Prepare / Compute / Present / Persist) pattern applied to the remaining 8 offenders. | One reusable mental model; tasks.md can reference the pattern rather than describe each split independently. | Bespoke design per method (verbose; harder to review consistency). |
| R-5 | Comment only touched lines. Estimated final coverage 82-85%. | Meets FR-006 floor with margin; avoids scope inflation. | File-wide comment pass (3x larger diff for no compliance gain). |
| R-6 | Existing `tests/unit/test_bulk_ap_upgrader.py` is the regression gate. Only `_make_upgrader` factory changes. | Test file exists and is substantial; kwargs construction confines the change. | Writing new tests (out of scope per spec Assumptions). |

All NEEDS-CLARIFICATION items in the plan template's Technical Context section are now resolved.
