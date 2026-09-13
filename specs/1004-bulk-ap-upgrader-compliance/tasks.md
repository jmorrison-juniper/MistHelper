---

description: "Task list for the Bulk AP Upgrader Compliance Refactor (specs/1004-bulk-ap-upgrader-compliance)"
---

# Tasks: Bulk AP Upgrader Compliance Refactor

**Input**: Design documents from `specs/1004-bulk-ap-upgrader-compliance/`
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/constructor.md`, `quickstart.md`

**Tests**: NOT added. The existing regression suite at `tests/unit/test_bulk_ap_upgrader.py` is the harness (per `research.md` R-6). Only the `_make_upgrader` factory in that file is edited.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently. Every task's verification gate is the four commands below unless noted otherwise.

## Standing Verification Gate (applies to every task in this file)

Every task in this file is not complete until ALL FOUR commands report clean:

```bash
python -m tools.compliance_analyzer src/firmware/bulk_ap_upgrader.py   # score should trend toward >=80
python -m ruff check src/firmware/bulk_ap_upgrader.py                  # zero errors, zero warnings
python -m py_compile src/firmware/bulk_ap_upgrader.py                  # exit 0
python -m pytest tests/unit/test_bulk_ap_upgrader.py -v                # all pass
```

Any task that regresses ruff / py_compile / pytest is reverted before moving on. Compliance score is expected to climb monotonically; a within-task dip is only acceptable if the very next task recovers it.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Task edits a file that no concurrent task is also editing. Because ~95% of this refactor lives in `src/firmware/bulk_ap_upgrader.py`, [P] appears sparingly.
- **[Story]**: Which user story from `spec.md` (US1..US5). Setup / Foundational / Polish tasks have no story label.
- Every task lists the exact file path being edited.

## Path Conventions

- Repository root is the current working directory.
- Primary edit target: `src/firmware/bulk_ap_upgrader.py` (single file, ~1,673 lines pre-refactor).
- Two caller-migration targets: `MistHelper.py` and `tests/unit/test_bulk_ap_upgrader.py`.
- Optional plan reference update: `.github/copilot-instructions.md`.

## AGENTS.md Non-Negotiables (apply inside every implementation task)

1. Every NEW or EDITED executable line must carry an inline `# WHY` comment explaining why the line exists (not what it does).
2. Every NEW operation (I/O, mutation, branch, API call, file op) must be bracketed by `logging.info(...)` BEFORE and `logging.debug(...)` AFTER with a result summary.
3. All log strings must be ASCII-only (FR-008).
4. All `input(...)` calls must be wrapped in `safe_input(..., context="...")` (FR-009).
5. All filesystem paths must use `os.path.join(...)` or `pathlib.Path(...)` (FR-010).
6. No wrapper / delegator / shim helpers (FR-011). Any extracted helper must do real work.

If a task's diff would introduce a violation of items 1-6, the task is not complete.

---

## Phase 1: Setup (Baseline Capture)

**Purpose**: Freeze the pre-refactor baseline so every subsequent task can be measured against a known starting point. No source code is changed in this phase.

- [X] T001 Capture baseline compliance analyzer output by running `python -m tools.compliance_analyzer src/firmware/bulk_ap_upgrader.py` and saving stdout+stderr to `specs/1004-bulk-ap-upgrader-compliance/artifacts/baseline_compliance.txt`. Confirm the recorded score is 50.0 and grade is F (matches spec claim).
- [X] T002 [P] Capture baseline test-suite output by running `python -m pytest tests/unit/test_bulk_ap_upgrader.py -v` and saving to `specs/1004-bulk-ap-upgrader-compliance/artifacts/baseline_pytest.txt`. Confirm all tests currently pass; if any fail on baseline, resolve before proceeding.
- [X] T003 [P] Capture baseline ruff + py_compile output by running both commands on `src/firmware/bulk_ap_upgrader.py` and saving to `specs/1004-bulk-ap-upgrader-compliance/artifacts/baseline_lint.txt`. Confirm both currently exit clean.
- [X] T004 Enumerate every direct constructor call site by running `grep -rn "BulkAPFirmwareUpgrader(" src/ MistHelper.py tests/` and saving to `specs/1004-bulk-ap-upgrader-compliance/artifacts/callsites.txt`. Confirm exactly two impl-class construction sites exist: `MistHelper.py` thin wrapper (~line 19796) and `tests/unit/test_bulk_ap_upgrader.py` `_make_upgrader` (~line 83). Any additional impl-class site discovered here is added as a follow-up task.

**Checkpoint**: Baselines locked. Every later task compares against these artifacts.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Introduce the `BulkAPUpgraderConfig` dataclass. This is `T-DATACLASS` (labeled per user request). It BLOCKS the `__init__` decomposition (Phase 3, US1) AND both caller-site updates (Phase 3, US2). Nothing else in the refactor can begin until this task lands cleanly.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 [T-DATACLASS] Add the `BulkAPUpgraderConfig` frozen dataclass to `src/firmware/bulk_ap_upgrader.py` per `data-model.md`. Place it below the module imports and above the `BulkAPFirmwareUpgrader` class. Requirements: `@dataclass(frozen=True, slots=True)`; 10 fields matching the current `__init__` parameters 1:1 (see `data-model.md` mapping table); import `dataclass`, `field`, `Callable`, `Optional`, `Any` if not already imported; every field declaration carries a `# WHY` inline comment (fields count as executable lines for compliance purposes); no `__post_init__` (deferred per `data-model.md`). Verification: `python -m py_compile src/firmware/bulk_ap_upgrader.py` exits 0; `python -m ruff check` clean; `python -c "from src.firmware.bulk_ap_upgrader import BulkAPUpgraderConfig; print(BulkAPUpgraderConfig.__dataclass_fields__.keys())"` prints all 10 field names; existing pytest suite still passes because the dataclass is not yet consumed by `__init__`.

**Checkpoint**: `BulkAPUpgraderConfig` exists and is importable. `__init__` still has its 10-parameter shape (unchanged). US1 constructor work AND US2 caller work can now proceed.

---

## Phase 3: User Story 1 - Restore Compliance Grade to Passing (Priority: P1) MVP

**Goal**: Bring `src/firmware/bulk_ap_upgrader.py` from grade F / 50.0 to grade B / >=80.0 by decomposing the two highest-severity structural offenders — `__init__` (10 params, 30+ lines) and `execute` (32 lines, 9 blocks) — into helpers that respect the Constitution I ceilings.

**Independent Test**: After Phase 3 completes, `python -m tools.compliance_analyzer src/firmware/bulk_ap_upgrader.py` should show `__init__` and `execute` no longer flagged for PARAM-COUNT or LOGICAL-BLOCKS. Score should climb from 50 to the mid-60s (further gains come from US3 and US4).

### Constructor Decomposition (depends on T005)

- [X] T006 [US1] Add private helper `_init_session_ctx(self, config: BulkAPUpgraderConfig) -> None` to `src/firmware/bulk_ap_upgrader.py` per `research.md` R-2. Body assigns `self.org_id`, `self.apisession`, `self.dry_run`, `self._input_fn` (with `or input` fallback wrapped in `safe_input(..., context="bulk_ap_upgrader.session")`), and the six injected callables from `config`. Every assignment on its own line with a `# WHY` inline comment. Bracket the helper with `logging.info("Initializing session context from config")` at entry and `logging.debug("Session context ready: org_id=%s dry_run=%s", ...)` at exit. Ceiling: <=25 lines, <=5 params, <=5 blocks, <=4 nesting.
- [X] T007 [US1] Add private helper `_init_ap_and_site_state(self) -> None` to `src/firmware/bulk_ap_upgrader.py` per `research.md` R-2. Body resets `self.sites_to_upgrade`, `self.all_sites_aps`, `self.all_aps`, `self.aps_by_model`, `self.ap_versions` to their empty defaults. Every assignment carries a `# WHY` inline comment. Bracket with `logging.info(...)` / `logging.debug(...)`. Ceiling: <=25 lines.
- [X] T008 [US1] Add private helper `_init_plan_and_results_state(self) -> None` to `src/firmware/bulk_ap_upgrader.py` per `research.md` R-2. Body resets `self.available_versions`, `self.model_version_ranges`, `self.upgrade_plan`, `self.skipped_already_at_target`, `self.upgrade_config`, `self.upgrade_ids`, `self.results`, `self.successful_upgrades`, `self.failed_upgrades`. Every assignment carries a `# WHY` inline comment. Bracket with `logging.info(...)` / `logging.debug(...)`. Ceiling: <=25 lines.
- [X] T009 [US1] Rewrite `BulkAPFirmwareUpgrader.__init__` in `src/firmware/bulk_ap_upgrader.py` to the shape shown in `research.md` R-2: signature is `def __init__(self, config: BulkAPUpgraderConfig) -> None`; body is exactly 5 executable lines — `logging.info(...)`, three helper calls (T006/T007/T008), one `logging.debug(...)`. Each of the 5 lines carries a `# WHY` inline comment. This task DEPENDS ON T005-T008. After this task lands, existing pytest suite will FAIL because callers still pass 10 kwargs — this is expected and cleared by Phase 3 US2 tasks T010/T011 which follow immediately.

### Execute Method Decomposition

- [X] T010 [US1] Add private helper `_announce_start(self) -> None` to `src/firmware/bulk_ap_upgrader.py` per `research.md` R-3. Body emits the two `logging.info` lines that today live at the top of `execute()` plus the dry-run banner `print(...)` if `self.dry_run`. Every line carries a `# WHY` inline comment. Log strings must be ASCII-only (FR-008). Bracket with `logging.info(...)` / `logging.debug(...)`. Ceiling: <=25 lines.
- [X] T011 [US1] Add private helper `_run_discovery_phase(self) -> bool` to `src/firmware/bulk_ap_upgrader.py` per `research.md` R-3. Body calls `_step1_determine_sites`, `_step2_discover_aps`, `_step3_fetch_firmware_stats`, `_step4_fetch_available_firmware` in order; returns `False` on the first step that returns falsy; returns `True` at the end. Every executable line has a `# WHY` inline comment. Bracket with `logging.info("Discovery phase starting")` / `logging.debug("Discovery phase result: %s", ok)`. Ceiling: <=25 lines, <=5 blocks.
- [X] T012 [US1] Add private helper `_run_planning_phase(self) -> bool` to `src/firmware/bulk_ap_upgrader.py` per `research.md` R-3. Body calls `_step5_select_firmware_versions`, `_step6_configure_upgrade`, `_step7_confirm_upgrade` in order; returns `False` on the first falsy return; returns `True` at the end. Every executable line has a `# WHY` inline comment. Bracket with `logging.info(...)` / `logging.debug(...)`. Ceiling: <=25 lines.
- [X] T013 [US1] Add private helper `_run_execution_phase(self) -> None` to `src/firmware/bulk_ap_upgrader.py` per `research.md` R-3. Body calls `_step8_execute_upgrades`, `_step9_configure_auto_upgrade`, `_step10_offer_status_check`, `_step11_write_results` in order. No early exit — these are terminal steps. Every executable line has a `# WHY` inline comment. Bracket with `logging.info(...)` / `logging.debug(...)`. Ceiling: <=25 lines.
- [X] T014 [US1] Rewrite `BulkAPFirmwareUpgrader.execute` in `src/firmware/bulk_ap_upgrader.py` to the exact shape shown in `research.md` R-3 (~10 executable lines, 3 logical blocks): `_announce_start()`; `try:` block calling `_run_discovery_phase()` -> early return, `_run_planning_phase()` -> early return, `_run_execution_phase()`; `except KeyboardInterrupt:` block preserving the pre-refactor `print` message text byte-for-byte (FR-017) plus a new `logging.info(...)` on cancel. Every line carries a `# WHY` inline comment. DEPENDS ON T010-T013.

**Checkpoint**: `__init__` is 5 lines, 1 param. `execute` is ~10 lines, 3 blocks. Compliance analyzer no longer flags either for PARAM-COUNT or LOGICAL-BLOCKS. Score has climbed materially. `pytest` may fail if US2 tasks T015/T016 have not run yet — that is expected and cleared next.

---

## Phase 3b: User Story 2 - Preserve Existing Caller Contracts (Priority: P1)

**Goal**: Update the two direct impl-class callers so `pytest` and menu 195 continue to work after the constructor shape changes. This story ships in the same commit as US1 per FR-014.

**Independent Test**: `pytest tests/unit/test_bulk_ap_upgrader.py -v` returns all-green. Manually running menu 195 in dry-run mode from a Python REPL reaches the "no upgrades executed" summary without `TypeError`.

- [X] T015 [US2] Update the `MistHelper.py` thin wrapper at approximately line 19796 to construct a `BulkAPUpgraderConfig` and pass it as the single positional argument to the impl class, per `contracts/constructor.md` "Caller 1" After block. Add `BulkAPUpgraderConfig` to the deferred import inside `execute()`. Every new/edited executable line in the wrapper carries a `# WHY` inline comment. Bracket the config construction with `logging.info("Building BulkAPUpgraderConfig for menu 195")` before and `logging.debug("Config built; delegating to impl")` after. Preserve the wrapper's own external signature (menu 195 still passes `org_id`, `sites_override`, `dry_run` — unchanged).
- [X] T016 [P] [US2] Update the `_make_upgrader` factory in `tests/unit/test_bulk_ap_upgrader.py` at approximately line 69 per `contracts/constructor.md` "Caller 2" After block. The `defaults` dict stays as is; only the two final lines change: build `config = BulkAPUpgraderConfig(**defaults)`, then return `BulkAPFirmwareUpgrader(config)`. Import `BulkAPUpgraderConfig` from `src.firmware.bulk_ap_upgrader` at the top of the test file. Every new/edited executable line carries a `# WHY` inline comment. NOTE: this file is a different file from `MistHelper.py`, so it can proceed in parallel with T015.
- [X] T017 [US2] Sweep `tests/` for any direct call to `BulkAPFirmwareUpgrader(` that bypasses the `_make_upgrader` factory. Run `grep -n "BulkAPFirmwareUpgrader(" tests/` and inspect every match. Any match that is not inside `_make_upgrader` or inside a docstring/comment must be either rewritten to use `_make_upgrader(...)` or updated to build a `BulkAPUpgraderConfig`. Every edited line carries a `# WHY` inline comment.
- [X] T018 [US2] Run the REPL constructor contract smoke from `quickstart.md` Step 6: verify positive construction via `BulkAPUpgraderConfig`, verify legacy positional call raises `TypeError`, verify frozen dataclass rejects mutation with `FrozenInstanceError`. All three cases must behave as shown in the quickstart. Save the REPL transcript to `specs/1004-bulk-ap-upgrader-compliance/artifacts/constructor_smoke.txt`.

**Checkpoint**: `pytest tests/unit/test_bulk_ap_upgrader.py -v` is all-green. Both direct impl-class callers construct via `BulkAPUpgraderConfig`. Menu 195 wrapper's external signature is unchanged.

---

## Phase 4: User Story 3 - Meet AGENTS.md Documentation and Logging Standards (Priority: P2)

**Goal**: Push inline-comment coverage from 0.2% to >=80% on the file, ensure every touched operation is bracketed by `logging.info` / `logging.debug`, and eliminate any non-ASCII in log strings, any raw `input(...)` calls, and any raw path concatenation in touched code.

**Independent Test**: `python -m tools.compliance_analyzer src/firmware/bulk_ap_upgrader.py` reports inline-comment coverage >=80%. `grep -n "logging.info\|logging.debug" src/firmware/bulk_ap_upgrader.py` shows the info-before / debug-after pattern at the 10 targeted refactor sites. The Python one-liner in `quickstart.md` Step 5 finds no non-ASCII log strings.

- [X] T019 [US3] Add `# WHY` inline comments to every executable line inside the four constructor-related helpers (`__init__`, `_init_session_ctx`, `_init_ap_and_site_state`, `_init_plan_and_results_state`) in `src/firmware/bulk_ap_upgrader.py`. Comments explain WHY the line exists, not WHAT it does (Constitution VI). No line is left uncommented if it was created or edited in T005-T009.
- [X] T020 [US3] Add `# WHY` inline comments to every executable line inside the five execute-related helpers (`execute`, `_announce_start`, `_run_discovery_phase`, `_run_planning_phase`, `_run_execution_phase`) in `src/firmware/bulk_ap_upgrader.py`. Same standard as T019.
- [X] T021 [US3] Add `# WHY` inline comments and info-before / debug-after brackets to every executable line inside every `_stepN_*` method body in `src/firmware/bulk_ap_upgrader.py` (11 methods total, `_step1_determine_sites` through `_step11_write_results`). Rationale: per Constitution VI, when existing code is found lacking inline comments during any edit, comments MUST be added to the entire function/block being touched, and these methods are now called from the new phase helpers (T011-T013). This task is the largest single-diff task in the plan and may be split into 2-3 sub-tasks (`_step1..4`, `_step5..7`, `_step8..11`) if the diff becomes unwieldy for review.
- [X] T022 [US3] Wrap every remaining `input(...)` call in `src/firmware/bulk_ap_upgrader.py` (across all touched methods) in `safe_input(..., context="bulk_ap_upgrader.<purpose>")` per FR-009. Grep-verify: `grep -n "^\\s*input(" src/firmware/bulk_ap_upgrader.py` returns nothing after this task. Every edited call carries a `# WHY` inline comment naming the prompt purpose.
- [X] T023 [US3] Audit every `logging.*(` and every `print(` call in `src/firmware/bulk_ap_upgrader.py` for non-ASCII characters per FR-008. Use the Python one-liner from `quickstart.md` Step 5 to find violations. Replace emoji with ASCII markers (e.g., `[OK]`, `[FAIL]`), replace curly quotes with straight, replace en-dash with `-`, replace check-mark with `[OK]`. Every edited string carries an updated `# WHY` inline comment.
- [X] T024 [US3] Replace any filesystem path construction that uses raw `/` or `\\` string concatenation with `os.path.join(...)` or `pathlib.Path(...)` in touched code paths of `src/firmware/bulk_ap_upgrader.py` (particularly around `_step11_write_results` CSV output). Add `import os` or `from pathlib import Path` if not already imported. Every edited line carries a `# WHY` inline comment.

**Checkpoint**: Inline-comment coverage on the file is >=80%. Info-before / debug-after pattern is uniform. No ASCII violations in log strings. No raw `input(...)`. No raw path concatenation in touched code.

---

## Phase 5: User Story 4 - Resolve Top MEDIUM-Severity Function Complexity (Priority: P2)

**Goal**: Decompose the nine remaining MEDIUM-severity offenders enumerated in FR-012 (excluding `execute` and `__init__`, which are covered by US1) using the PCPP (Prepare / Compute / Present / Persist) pattern from `research.md` R-4. Each offender's method body must end up <=25 executable lines, <=5 logical blocks, <=5 cyclomatic complexity, <=4 nesting levels.

**Independent Test**: `python -m tools.compliance_analyzer src/firmware/bulk_ap_upgrader.py` shows none of the nine methods listed below appearing in the flagged-offenders section. File grade is B (>=80) or better.

**Rule for every task in this phase**:

- Apply the PCPP pattern. Helpers named `_prepare_*`, `_compute_*`, `_present_*`, `_persist_*` as applicable.
- Any PCPP slice that would produce a helper of <=3 executable lines is inlined instead — no wrappers (FR-011).
- Every helper introduced carries a `# WHY` inline comment on every executable line, plus info-before / debug-after logging.
- Every helper is <=25 lines, <=5 params, <=5 blocks, <=5 complexity, <=4 nesting.
- The public method (or `_stepN_*` method) is rewritten as a 4-6 line orchestrator whose executable lines also carry `# WHY` comments.
- Any single-letter loop variable encountered inside the touched method is renamed as part of the same task (spec FR-013, covered by US5 but opportunistically fixed here).

Tasks (all edit `src/firmware/bulk_ap_upgrader.py` sequentially — no [P] because same file):

- [X] T025 [US4] Decompose `_select_strategy` (currently 43 lines, line ~724) per PCPP: `_prepare_strategy_inputs` (read `_current_config` + `model_ranges`), `_compute_strategy_ranking`, `_present_strategy_table`, `_persist_strategy_choice`. Rewrite `_select_strategy` as the 4-6 line orchestrator. Confirm the analyzer no longer flags this method.
- [X] T026 [US4] Decompose `_estimate_api_calls` (currently 43 lines, line ~850) per PCPP: `_prepare_estimate_inputs`, `_compute_estimate_counts`, `_present_estimate_table`. No persist slice (pure computation). Rewrite `_estimate_api_calls` as the orchestrator.
- [X] T027 [US4] Decompose `_offer_additional_model_versions` (currently 46 lines / 8 blocks, line ~1297) per PCPP: `_prepare_additional_version_candidates`, `_compute_available_extra_versions`, `_present_additional_version_prompt`, `_persist_additional_version_selection`. Rewrite the offender as the orchestrator.
- [X] T028 [US4] Decompose `_fetch_ap_model_families` (currently 42 lines / 7 blocks, line ~1231) per PCPP: `_prepare_model_family_request`, `_compute_model_family_response` (mistapi call), `_present_model_family_progress`, `_persist_model_family_cache`. Rewrite the offender as the orchestrator.
- [X] T029 [US4] Decompose `_configure_auto_upgrade_schedule` (currently 38 lines, line ~1463) per PCPP: `_prepare_schedule_input`, `_compute_schedule_api_shape`, `_present_schedule_echo`, `_persist_schedule_config`. Rewrite the offender as the orchestrator.
- [X] T030 [US4] Decompose `_step11_write_results` (currently 50 lines, line ~1624) per PCPP: `_prepare_results_filename` (uses `os.path.join`, see T024), `_compute_results_rows`, `_present_results_summary`, `_persist_results_csv`. Rewrite the offender as the orchestrator. This is the largest offender in the list — pay particular attention to the <=25-line ceiling on each helper.
- [X] T031 [US4] Decompose `_apply_version_selection` (currently 34 lines, line ~651) per PCPP: `_prepare_version_choice`, `_compute_matched_versions`, `_present_selection_echo`, `_persist_version_plan_update`. Rewrite the offender as the orchestrator.
- [X] T032 [US4] Decompose `_upgrade_version_group` (currently 34 lines, line ~1121) per PCPP: `_prepare_upgrade_request_body`, `_compute_upgrade_api_call` (respect dry-run), `_present_upgrade_status_per_model`, `_persist_upgrade_id`. Rewrite the offender as the orchestrator.
- [X] T033 [US4] Decompose `_log_upgrade_results` (currently 34 lines, line ~1184) per PCPP: `_prepare_result_counts`, `_compute_summary_lines`, `_present_summary_output`, `_persist_results_state`. Rewrite the offender as the orchestrator.

**Checkpoint**: All 9 MEDIUM offenders enumerated in FR-012 (plus `execute` and `__init__` from US1 = 11 total) are decomposed. Compliance-analyzer score is >=80. File grade is B or better.

---

## Phase 6: User Story 5 - Address LOW-Severity Findings Where Touched (Priority: P3)

**Goal**: Fix LOW-severity findings that overlap the touched code paths, particularly the single-letter loop variables at pre-refactor lines 587 and 595 inside `_get_versions_for_model` (FR-013). Do NOT expand scope beyond touched code.

**Independent Test**: `grep -n "for [a-z] in\| for [a-z] in" src/firmware/bulk_ap_upgrader.py` returns no results in code paths modified by this feature.

- [X] T034 [US5] Rename the single-letter loop variable at pre-refactor line 587 in `_get_versions_for_model` inside `src/firmware/bulk_ap_upgrader.py` to a descriptive identifier (e.g., `v` -> `version_entry`). Every touched line carries a `# WHY` inline comment. If the surrounding method is itself an offender, apply info-before / debug-after brackets at method entry/exit.
- [X] T035 [US5] Rename the single-letter loop variable at pre-refactor line 595 in `_get_versions_for_model` inside `src/firmware/bulk_ap_upgrader.py` to a descriptive identifier. Same standard as T034.
- [X] T036 [US5] Sweep every helper introduced in Phase 3-5 (all `_init_*`, `_run_*`, `_prepare_*`, `_compute_*`, `_present_*`, `_persist_*` methods) in `src/firmware/bulk_ap_upgrader.py` for single-letter loop / comprehension variables introduced during decomposition. Rename any found. Every edited line carries a `# WHY` inline comment.

**Checkpoint**: No single-letter loop/comprehension variable remains in any code path touched by this feature.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, artifact capture, and reviewer-friendly documentation updates.

- [X] T037 Run the final compliance analyzer gate: `python -m tools.compliance_analyzer src/firmware/bulk_ap_upgrader.py`. Save output to `specs/1004-bulk-ap-upgrader-compliance/artifacts/final_compliance.txt`. Confirm score >=80.0, grade B or better, zero HIGH-severity findings, at most 2 MEDIUM-severity findings, and none of the ten enumerated FR-012 offenders remain flagged (SC-001 through SC-004).
- [X] T038 [P] Run the final ruff gate: `python -m ruff check src/firmware/bulk_ap_upgrader.py`. Save output to `specs/1004-bulk-ap-upgrader-compliance/artifacts/final_ruff.txt`. Confirm zero errors, zero warnings (FR-002, SC-006).
- [X] T039 [P] Run the final py_compile gate: `python -m py_compile src/firmware/bulk_ap_upgrader.py`. Confirm exit 0 (FR-003, SC-007). Save exit code + any stderr to `specs/1004-bulk-ap-upgrader-compliance/artifacts/final_pycompile.txt`.
- [X] T040 [P] Run the final pytest gate: `python -m pytest tests/unit/test_bulk_ap_upgrader.py -v`. Save output to `specs/1004-bulk-ap-upgrader-compliance/artifacts/final_pytest.txt`. Confirm all tests pass without any test-body modification beyond `_make_upgrader` (SC-008).
- [X] T041 Perform the inline-comment coverage spot check from `quickstart.md` Step 4: sample 25 executable lines from `src/firmware/bulk_ap_upgrader.py` at random offsets and confirm at least 20 carry an inline `# WHY` comment (SC-009). Save the sampled line ranges + comment counts to `specs/1004-bulk-ap-upgrader-compliance/artifacts/comment_sample.txt`.
- [X] T042 Perform the logging pattern spot check from `quickstart.md` Step 5: grep for the info-before / debug-after pattern at the ten targeted refactor sites (SC-010). Run the ASCII-only log string one-liner from the same quickstart step. Expected: empty output. Save both to `specs/1004-bulk-ap-upgrader-compliance/artifacts/logging_audit.txt`.
- [X] T043 Optional: perform the menu 195 manual smoke from `quickstart.md` Step 7 against a dry-run session (FR-017). Save observed prompt sequence to `specs/1004-bulk-ap-upgrader-compliance/artifacts/menu_195_smoke.txt`. Only required if a reviewer has doubts after T037-T042 all pass.
- [X] T044 Update `.github/copilot-instructions.md` between the `<!-- SPECKIT START -->` and `<!-- SPECKIT END -->` markers to reference `specs/1004-bulk-ap-upgrader-compliance/plan.md` as the active plan (per `plan.md` Phase 1 Deliverables). Every edited line carries a `# WHY` inline comment where the target file's convention allows.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies. Can start immediately.
- **Phase 2 (Foundational — T-DATACLASS)**: Depends on Phase 1 complete. **BLOCKS ALL USER STORIES.**
- **Phase 3 (US1 constructor + execute)**: Depends on T005 (T-DATACLASS) complete.
- **Phase 3b (US2 caller migration)**: Depends on T005 (T-DATACLASS) complete AND T009 (new `__init__` signature) complete. Menu 195 wrapper (T015) is in a different file from the test factory (T016), so those two tasks can proceed in parallel.
- **Phase 4 (US3 docs & logging)**: Depends on Phase 3 + 3b complete — comments and logging brackets are added to the code that Phase 3 restructured.
- **Phase 5 (US4 MEDIUM offender decomp)**: Depends on Phase 3 + 3b + 4 complete. All nine offender tasks (T025-T033) edit the same file and must run sequentially.
- **Phase 6 (US5 LOW-severity)**: Depends on Phase 5 complete (single-letter loops may have been renamed opportunistically inside Phase 5 tasks; Phase 6 sweeps any that remain).
- **Phase 7 (Polish)**: Depends on all Phases 1-6 complete. T038/T039/T040 can run in parallel because they read the same file and do not mutate it.

### T-DATACLASS Blocking Diagram

```text
                       T005 (T-DATACLASS)
                        /       |       \
                       /        |        \
                  T006-T009   T015     T016
                  (US1 init)  (US2     (US2 test
                              caller)   factory)
                       \        |        /
                        \       |       /
                         T014 (US1 execute rewrite)
                                |
                                v
                         Phase 4 (US3 docs & logging)
                                |
                                v
                         Phase 5 (US4 MEDIUM offenders)
                                |
                                v
                         Phase 6 (US5 LOW-severity)
                                |
                                v
                         Phase 7 (Polish)
```

### Within Each User Story

- No formal test-first requirement (existing test file is the harness).
- Helpers before orchestrator rewrite (e.g., T006-T008 before T009; T010-T013 before T014).
- After each task the four-command gate (see top of file) must pass.

### Parallel Opportunities

- T002 and T003 (baseline capture) can run in parallel.
- T015 (edit `MistHelper.py`) and T016 (edit `tests/unit/test_bulk_ap_upgrader.py`) can run in parallel — different files.
- T038, T039, T040 (final ruff / py_compile / pytest) can run in parallel — read-only against the file.
- Everything else touches `src/firmware/bulk_ap_upgrader.py` and must serialize.

---

## Parallel Example: Phase 3b (US2 Caller Migration)

```bash
# After T005 (T-DATACLASS) and T009 (new __init__ signature) both land:

# Terminal 1 (edits MistHelper.py):
Task: T015 Update MistHelper.py thin wrapper at line ~19796 to build BulkAPUpgraderConfig

# Terminal 2 (edits tests/unit/test_bulk_ap_upgrader.py):
Task: T016 Update _make_upgrader factory to build BulkAPUpgraderConfig
```

Both terminals converge to a passing `pytest tests/unit/test_bulk_ap_upgrader.py -v` when done.

---

## Implementation Strategy

### MVP First (Phase 1 + 2 + US1 + US2 only)

1. Complete Phase 1: Setup (T001-T004) — baseline captured.
2. Complete Phase 2: T-DATACLASS (T005) — dataclass exists but unused.
3. Complete Phase 3: US1 constructor + execute decomposition (T006-T014).
4. Complete Phase 3b: US2 caller migration (T015-T018).
5. **STOP and VALIDATE**: run all four gates. Compliance score should be in the mid-60s (still F/D, but constructor and execute violations gone). Pytest all-green. Menu 195 REPL smoke clean.
6. This is a mergeable increment if the reviewer accepts a non-B interim grade. Grade B requires Phase 4+.

### Incremental Delivery to Grade B

1. Setup + Foundational -> ready to refactor.
2. + US1 + US2 -> constructor and execute cleaned, callers migrated, tests passing. **Score ~65.**
3. + US3 -> inline-comment coverage and logging pattern satisfied. **Score ~75.**
4. + US4 -> nine MEDIUM offenders decomposed. **Score >=80, grade B.** Ship-able.
5. + US5 -> LOW-severity findings in touched code fixed. **Score ~82-85.**
6. + Polish -> artifacts captured, plan reference updated.

### Recommended Commit Boundaries

- One commit per phase: `refactor(bulk-ap-upgrader): phase 1 baseline`, `refactor(bulk-ap-upgrader): phase 2 T-DATACLASS`, etc. Six or seven total commits.
- OR: one commit per task if the reviewer prefers finer-grained review. Estimated 44 commits.
- Grade B is only reached at the end of Phase 5 (US4), so if committing per phase, the "grade B" milestone commit is `refactor(bulk-ap-upgrader): phase 5 MEDIUM offender decomposition`.

---

## Notes

- Every task edits `src/firmware/bulk_ap_upgrader.py` unless otherwise noted. Two exceptions: T015 edits `MistHelper.py`, T016 edits `tests/unit/test_bulk_ap_upgrader.py`, T044 edits `.github/copilot-instructions.md`.
- Every task's success is measured against the standing four-command gate at the top of this file.
- No wrapper / delegator / shim helpers may be introduced (FR-011). If a PCPP slice would be a 1-line forward, inline it.
- Every executable line new or edited must carry `# WHY` inline commentary (Constitution VI, AGENTS.md non-negotiable).
- Every new operation must be bracketed by `logging.info` before / `logging.debug` after (Constitution VII, AGENTS.md non-negotiable).
- All log strings must be ASCII-only (FR-008). All `input(...)` calls must use `safe_input(..., context=...)` (FR-009).
- The `BulkAPUpgraderConfig` dataclass lives in `src/firmware/bulk_ap_upgrader.py` (FR-018). No new module is created.
- Task IDs are gap-friendly. If a task needs to be split during implementation (e.g., T021), assign `T021a`, `T021b` rather than renumbering.
