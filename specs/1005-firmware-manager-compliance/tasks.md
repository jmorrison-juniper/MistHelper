---

description: "Task list for the Firmware Manager Compliance Refactor (specs/1005-firmware-manager-compliance)"
---

# Tasks: Firmware Manager Compliance Refactor

**Input**: Design documents from `specs/1005-firmware-manager-compliance/`
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/constructor.md`, `quickstart.md`

**Tests**: NOT added. No pre-existing unit test file for `firmware_manager.py` exists and NG-001 forbids creating one. The compliance analyzer, `ruff`, `py_compile`, and the manual REPL/menu-196 smokes from `quickstart.md` are the sole gates.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently. Every task's verification gate is the three commands below unless noted otherwise.

## Standing Verification Gate (applies to every task in this file)

Every task in this file is not complete until ALL THREE commands report clean:

```bash
python -m tools.compliance_analyzer src/firmware/firmware_manager.py   # score trends toward 100.0 / A+
python -m ruff check src/firmware/firmware_manager.py                  # zero errors, zero warnings
python -m py_compile src/firmware/firmware_manager.py                  # exit 0
```

Any task that regresses ruff / py_compile is reverted before moving on. Compliance score is expected to climb monotonically; a within-task dip is only acceptable if the very next task recovers it. The final target is exactly 100.0 / A+ with zero HIGH / zero MEDIUM / zero LOW findings across all seven analyzer rules — no intermediate grade is a pass.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Task edits a file that no concurrent task is also editing. Because ~99% of this refactor lives in `src/firmware/firmware_manager.py`, [P] appears sparingly (only the MistHelper.py factory-body diff and the final read-only verification tasks).
- **[Story]**: Which user story from `spec.md` (US1..US6). Setup / Foundational / Polish tasks have no story label.
- Every task lists the exact file path being edited.
- Every task has a "Done when:" line stating the acceptance criterion for that task in isolation.

## Path Conventions

- Repository root is the current working directory.
- Primary edit target: `src/firmware/firmware_manager.py` (single file, 2450 lines pre-refactor, ~4000 lines post-refactor).
- Sole permitted off-file diff: `MistHelper.py` lines 18791-18807 (the `FirmwareManager.create` factory body).
- Optional plan reference update: `.github/copilot-instructions.md`.
- Artifact drop directory: `specs/1005-firmware-manager-compliance/artifacts/`.

## AGENTS.md Non-Negotiables (apply inside every implementation task)

1. Every NEW or EDITED executable line must carry an inline `# WHY: <intent>` comment explaining why the line exists (not what it does) — Constitution VI.
2. Every NEW operation (I/O, mutation, branch, API call, file op) must be bracketed by `logging.info(...)` BEFORE and `logging.debug(...)` AFTER with a result summary — Constitution VII, FR-019.
3. All log strings must be ASCII-only and use lazy `%s` / `%d` form — no f-strings inside `logging.*` calls (FR-020, spec Edge Case).
4. All `input(...)` calls must be wrapped in `safe_input(..., context="firmware-manager.<kebab-tag>")` (FR-021).
5. All filesystem paths must use `os.path.join(...)` or `pathlib.Path(...)` (FR-022).
6. No wrapper / delegator / shim helpers (FR-007). Any extracted helper must do real work.
7. No `# noqa`, `# type: ignore`, or `# pragma: no cover` markers as substitutes for real structural fixes (FR-006).

If a task's diff would introduce a violation of items 1-7, the task is not complete.

---

## Phase 1: Setup (Baseline Capture)

**Purpose**: Freeze the pre-refactor baseline so every subsequent task can be measured against a known starting point. No source code is changed in this phase.

- [X] T-001 Capture baseline compliance analyzer output by running `python -m tools.compliance_analyzer src/firmware/firmware_manager.py` and saving stdout+stderr to `specs/1005-firmware-manager-compliance/artifacts/baseline_compliance.txt`. Confirm the recorded score is 51.0 and grade is F (matches spec claim of 82 violations: 6 HIGH, 34 MEDIUM, 42 LOW).
  - **Done when:** file exists and its first line-block reports `Score: 51.0` and `Grade: F`, and the per-rule totals in the JSON block enumerate the exact 82 violations claimed by `spec.md`.
- [X] T-002 [P] Capture baseline ruff + py_compile output by running both commands on `src/firmware/firmware_manager.py` and saving to `specs/1005-firmware-manager-compliance/artifacts/baseline_lint.txt`. Confirm both currently exit clean.
  - **Done when:** file records exit code 0 for both commands and no ruff violations are present pre-refactor (only the analyzer is failing).
- [X] T-003 [P] Enumerate every callsite of `FirmwareManager.create(...)` and every direct impl-class import by running `grep -rn "FirmwareManager\.create\|from src\.firmware\.firmware_manager" MistHelper.py src/ tests/` and saving output to `specs/1005-firmware-manager-compliance/artifacts/callsites.txt`. Confirm exactly one impl-import (MistHelper.py line 18795 inside the factory body), one `def create` (line 18797), and five downstream `FirmwareManager.create(apisession, org_id)` calls (lines 19809, 22097, 22154, 22237, 22246). Any additional impl-class import discovered here is added as a follow-up task and blocks Phase 7.
  - **Done when:** callsites.txt matches the seven expected lines exactly. If anything else appears, halt and re-plan.
- [X] T-004 Verify the artifact directory `specs/1005-firmware-manager-compliance/artifacts/` exists (it already contains `baseline_compliance_report.md`). Confirm write access by creating an empty sentinel `specs/1005-firmware-manager-compliance/artifacts/.gitkeep` if not already present. This unblocks Phase 8 artifact drops.
  - **Done when:** `ls` on the artifacts directory succeeds and shows the pre-existing baseline report; no other change to that directory is made yet.

**Checkpoint**: Baselines locked. Every later task compares against these artifacts.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Introduce the `FirmwareManagerConfig` dataclass. This is `T-DATACLASS` (labeled per user request). It BLOCKS the `__init__` decomposition (Phase 3, US3) AND the MistHelper.py factory-body migration (Phase 7, US2). Nothing else in the refactor can begin until this task lands cleanly.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T-005 [T-DATACLASS] Add the `FirmwareManagerConfig` frozen dataclass to `src/firmware/firmware_manager.py` per `data-model.md`. Placement: below the module imports and above the `FirmwareManager` class. Requirements:
  - Decorator: `@dataclass(frozen=True, slots=True, kw_only=True)`.
  - Eight fields matching the pre-refactor 8-parameter `__init__` 1:1 (see `data-model.md` field mapping table): `apisession: Any`, `org_id: str`, `safe_input_fn: Optional[SafeInputFn] = None`, `select_site_fn: Optional[SelectSiteFn] = None`, `check_cache_fn: Optional[CheckCacheFn] = None`, `get_csv_path_fn: Optional[GetCsvPathFn] = None`, `gateway_templates_fn: Optional[GeneratorFn] = None`, `sites_fn: Optional[GeneratorFn] = None`.
  - Type aliases (`SafeInputFn`, `SelectSiteFn`, `CheckCacheFn`, `GetCsvPathFn`, `GeneratorFn`) already exist in the module; reuse them, do not redefine.
  - Add `__post_init__` with the validation rules from `data-model.md`: `apisession` must not be `None`; `org_id` must be a non-empty `str`; each `*_fn` must be `None` or callable. Diagnostics per the table in `data-model.md`.
  - Every field declaration and every executable line inside `__post_init__` carries a `# WHY: <intent>` inline comment (fields count as executable lines for the analyzer).
  - Imports: add `from dataclasses import dataclass` and `from typing import Optional` at the top of the file if not already present. `Any` and `Callable` / `Iterable` are already imported.
  - Verification: `python -m py_compile src/firmware/firmware_manager.py` exits 0; `python -m ruff check src/firmware/firmware_manager.py` clean; `python -c "from src.firmware.firmware_manager import FirmwareManagerConfig; print(list(FirmwareManagerConfig.__dataclass_fields__))"` prints all eight field names.
  - **Done when:** `FirmwareManagerConfig` is importable, `__post_init__` rejects the three invalid cases from `data-model.md` (verified interactively), and no analyzer regression is introduced by the addition (existing 8-parameter `__init__` is still present and still flagged — that is expected and cleared in Phase 3).

**Checkpoint**: `FirmwareManagerConfig` exists and is importable. `__init__` still has its pre-refactor 8-parameter shape (unchanged). US3 constructor work AND US2 MistHelper.py migration can now proceed independently.

---

## Phase 3: User Story 3 - Consolidate Constructor Into Config Dataclass (Priority: P2, but sequenced early)

**Goal**: Bring `FirmwareManager.__init__` from 8 parameters / 44 lines / STRUCT-PARAMS violation to 1 parameter (`config: FirmwareManagerConfig`) and <=15 lines / <=5 blocks / CC<=3. Preserve every module-global side effect via the `_bind_module_globals(config)` helper described in `research.md` R-2.

**Independent Test**: `python -m tools.compliance_analyzer src/firmware/firmware_manager.py` shows `__init__` no longer flagged for STRUCT-PARAMS or STRUCT-LENGTH. Direct instantiation with the pre-refactor 8-kwarg pattern raises `TypeError` (contract C-3). Instantiation via `FirmwareManagerConfig` succeeds (contract C-1).

### Constructor Decomposition (depends on T-005)

- [X] T-006 [US3] Add module-level private helper `_bind_module_globals(config: FirmwareManagerConfig) -> None` to `src/firmware/firmware_manager.py` per `research.md` R-2. Body (via `sys.modules[__name__]` attribute setting): rebinds `module.apisession`, `module.org_id`, `module.PROGRESS_EMITTER` (via `_make_progress_emitter()` if that helper exists, otherwise leave the existing initializer in place), and resets `module.msp_privileges = []`. Every executable line carries a `# WHY:` inline comment. Bracket the helper with `logging.info("Binding module globals for org %s", config.org_id)` at entry and `logging.debug("Module globals bound: apisession=%s org_id=%s", type(config.apisession).__name__, config.org_id)` at exit. Ceiling: <=25 lines, <=5 params, <=5 blocks, <=4 nesting, CC <=5.
  - **Done when:** helper exists, calling it from a REPL rebinds all four module-scope names, ruff+py_compile clean, no new analyzer violations introduced.
- [X] T-007 [US3] Rewrite `FirmwareManager.__init__` in `src/firmware/firmware_manager.py` to the shape shown in `data-model.md` "Usage — Consumer Side": signature is `def __init__(self, config: FirmwareManagerConfig) -> None`; body is exactly 4 executable lines — `logging.info(...)`, `self._config = config`, `_bind_module_globals(config)`, `logging.debug(...)`. Each line carries a `# WHY:` inline comment. Also add the two read-only properties `org_id` and `apisession` from `data-model.md` "Usage — Consumer Side" so downstream helpers that already read `self.org_id` / `self.apisession` continue to work byte-identically (FR-023). Every helper method in the file that reads `self.safe_input_fn` / `self.select_site_fn` / etc. via attribute access must be updated in the same task to read `self._config.safe_input_fn` (or equivalent). This task DEPENDS ON T-005 + T-006. After it lands, direct `FirmwareManager(...)` calls with the pre-refactor 8-kwarg pattern will raise `TypeError` — this is the intended fail-fast per contract C-2/C-3 and is cleared for production paths by the Phase 7 MistHelper.py migration.
  - **Done when:** `__init__` body is <=15 executable lines, analyzer no longer reports STRUCT-PARAMS or STRUCT-LENGTH on `__init__`, ruff clean, py_compile 0, all downstream `self.<callable>_fn` references in the file resolve through `self._config`.

**Checkpoint**: `__init__` is 4 lines with 1 param. STRUCT-PARAMS clears. STRUCT-LENGTH clears on `__init__`. Score climbs materially. Downstream method bodies now read collaborators via `self._config.*_fn`. MistHelper.py factory is NOT yet updated, so any production menu invocation will fail at construction until Phase 7 T-033 lands. Serialize Phase 3 -> Phase 4 -> ... -> Phase 7 so the whole file is compliant before the callsite migration goes in the same commit.

---

## Phase 4: User Story 4 (HIGH) - Decompose the Four HIGH-Severity STRUCT-LENGTH Offenders

**Goal**: Bring each of the four HIGH-severity STRUCT-LENGTH offenders to <=25 lines and <=5 blocks / <=5 complexity / <=4 nesting by applying the PCPP pattern (Prepare / Compute / Present / Persist) from `research.md` R-3. Each orchestrator ends as a 4-8 line sequence of helper calls; each helper is <=25 lines with `# WHY:` comments on every executable line and info-before / debug-after brackets.

**Independent Test**: For each of the four HIGH offenders, `python -m tools.compliance_analyzer src/firmware/firmware_manager.py` shows the method removed from the flagged-offenders list at every severity. Menu 195 / menu 196 dry-run smokes reach identical prompt sequences vs. the pre-refactor branch (FR-023).

**Rule for every task in this phase**: apply PCPP; helpers named `_prepare_<action>_context`, `_compute_<action>_plan`, `_present_<action>_preview`, `_persist_<action>_results` (omit any slice that would be <=3 executable lines — inline it, per FR-007). Every helper carries `# WHY:` on every executable line + info-before / debug-after brackets. Every helper <=25 lines / <=5 blocks / CC<=5 / nesting<=4. The public method is rewritten as a thin orchestrator whose executable lines also carry `# WHY:` comments. Any single-letter loop variable encountered inside the method is renamed opportunistically (US6 task-list target).

Tasks (all edit `src/firmware/firmware_manager.py` sequentially — no [P] because same file):

- [X] T-008 [US4] Decompose `check_firmware_upgrade_status` (currently 61 executable lines at line 182, HIGH-severity STRUCT-LENGTH + CC 9) per PCPP: `_prepare_status_check_context`, `_compute_status_check_plan`, `_present_status_check_preview`, `_persist_status_check_results`. Rewrite `check_firmware_upgrade_status` as the 4-8 line orchestrator per the sample in `research.md` R-3. Preserve every existing prompt string, CSV output path, and API call byte-for-byte (FR-023, FR-025).
  - **Done when:** analyzer shows `check_firmware_upgrade_status` at <=25 lines with no flags; every helper is <=25 lines / <=5 blocks / CC<=5.
- [X] T-009 [US4] Decompose `_continuous_monitoring_mode` (currently 74 executable lines at line 244, HIGH-severity STRUCT-LENGTH) per PCPP: `_prepare_monitoring_context`, `_compute_monitoring_snapshot`, `_present_monitoring_row`, `_persist_monitoring_log`. Also flatten the STRUCT-NESTING offender at line 1740 which lives inside `_parse_ssr_site_selection` — that separate rename is covered in T-020; here focus is on this method's own nesting per R-7. Rewrite `_continuous_monitoring_mode` as the orchestrator.
  - **Done when:** analyzer shows `_continuous_monitoring_mode` at <=25 lines with no flags; nesting depth <=4 throughout the extracted helpers.
- [X] T-010 [US4] Decompose `_upgrade_ap_firmware_by_gateway_template` (currently 69 executable lines at line 522, HIGH-severity STRUCT-LENGTH; also owns the STRUCT-NESTING offender at line 750) per PCPP: `_prepare_ap_template_context`, `_compute_ap_template_upgrade_plan`, `_present_ap_template_preview`, `_persist_ap_template_execution`. Apply the R-7 early-return-guard flattening at the former line-750 nested `if/for/if` inside the appropriate helper. Rewrite the orchestrator.
  - **Done when:** analyzer shows `_upgrade_ap_firmware_by_gateway_template` at <=25 lines with no flags; the former line-750 nesting is now depth <=3 in every helper.
- [X] T-011 [US4] Decompose `_execute_msp_upgrade_plan` (currently 97 executable lines at line 1252, HIGH-severity STRUCT-LENGTH + CC 10 — the single largest offender in the file) per PCPP: `_prepare_msp_execution_context`, `_compute_msp_execution_batches`, `_present_msp_execution_preview`, `_persist_msp_execution_results`. Because CC is 10, expect to split the compute slice further into two helpers (e.g. `_compute_msp_org_partition` + `_compute_msp_upgrade_targets`) rather than pack it into one. Rewrite the orchestrator.
  - **Done when:** analyzer shows `_execute_msp_upgrade_plan` at <=25 lines with no flags; every extracted helper is <=25 lines / <=5 blocks / CC<=5.

**Checkpoint**: All four HIGH-severity STRUCT-LENGTH offenders removed. Score has climbed substantially (baseline 51.0 -> ~65-70 expected). HIGH-severity finding count is 0 for STRUCT-LENGTH. Remaining HIGH findings are the CONV-COMMENTS coverage failure (cleared in Phase 6) and the STRUCT-COMPLEXITY hotspots co-located with the HIGH STRUCT-LENGTH offenders (also cleared here as a side effect).

---

## Phase 5: User Story 4 (MEDIUM) + User Story 6 - Decompose the 32 MEDIUM STRUCT-LENGTH Offenders and Clear STRUCT-COMPLEXITY / STRUCT-BLOCKS / STRUCT-NESTING

**Goal**: Decompose the 32 MEDIUM-severity STRUCT-LENGTH offenders enumerated in FR-013 (`__init__` was already handled in Phase 3). Every method in the file must end at <=25 lines, <=5 blocks, CC <=5, nesting <=4. This phase also clears the remaining 28 STRUCT-COMPLEXITY, 11 STRUCT-BLOCKS, and 1 remaining STRUCT-NESTING findings — most overlap with the STRUCT-LENGTH decomposition and clear as a side effect.

**Independent Test**: `python -m tools.compliance_analyzer src/firmware/firmware_manager.py` shows zero STRUCT-LENGTH, zero STRUCT-COMPLEXITY, zero STRUCT-BLOCKS, and zero STRUCT-NESTING findings. Score >=95.

**Rule for every task in this phase**: same PCPP rule as Phase 4. Helpers <=25 lines / <=5 blocks / CC<=5 / nesting<=4. Every executable line in every touched helper (new or rewritten orchestrator) carries a `# WHY:` inline comment. Info-before / debug-after logging at every operation site. Any single-letter loop variable encountered is renamed opportunistically. Filesystem paths use `os.path.join(...)` or `pathlib.Path(...)`. `input(...)` calls route through `safe_input(..., context="firmware-manager.<kebab-tag>")`.

Tasks are batched by cohesive functional area so each task keeps a manageable diff size. All edit `src/firmware/firmware_manager.py` sequentially (no [P]):

### Batch A: Firmware Version + Template Selection (5 offenders)

- [X] T-012 [US4] Decompose `_is_firmware_downgrade` (36 lines) and `_show_org_level_upgrade_jobs` (49 lines) via PCPP. Note `_is_firmware_downgrade` is pure computation — omit the present/persist slices. `_show_org_level_upgrade_jobs` needs all four PCPP slices (compute is the API paginate loop; present is the tabular echo; persist is the CSV write, which MUST use `os.path.join`).
  - **Done when:** both methods <=25 lines; helpers <=25 lines each; analyzer no longer flags either.
- [X] T-013 [US4] Decompose `_load_template_sites_mapping` (30 lines), `_prompt_template_selection` (56 lines), and `_execute_template_based_upgrade` (30 lines) via PCPP. `_prompt_template_selection` includes the `input(...)` prompt — wrap in `safe_input(..., context="firmware-manager.template-select")` at the same time (FR-021 opportunistic fix).
  - **Done when:** all three methods <=25 lines; helpers <=25 lines each; every `input(` in these code paths is `safe_input(..., context=...)`.

### Batch B: Mode-Selection + STRUCT-NESTING Line 750 (2 offenders + 1 nesting)

- [X] T-014 [US4,US6] Decompose `execute_firmware_upgrade_with_mode_selection` (60 lines, currently owns the STRUCT-NESTING depth-5 offender at line 750 per FR-016) via PCPP: `_prepare_ap_mode_selection`, `_compute_ap_mode_target`, `_present_ap_mode_preview`, `_persist_ap_mode_launch`. Apply R-7 early-return-guard flattening to eliminate the depth-5 nest. Rewrite the orchestrator.
  - **Done when:** method <=25 lines; every helper <=25 lines / nesting depth <=3; analyzer STRUCT-NESTING finding for this line clears.

### Batch C: MSP Multi-Org + Site Selection (6 offenders)

- [X] T-015 [US4,US6] Decompose `_execute_msp_multi_org_upgrade` (45 lines), `_select_msps_for_upgrade` (55 lines, CC 10), `_select_orgs_for_upgrade` (59 lines, CC 10) via PCPP. Because both `_select_*` methods have CC 10, expect compute-slice sub-splits (e.g. `_compute_msp_selection_from_input`, `_present_msp_confirmation`) per R-4. Any `input(...)` in these code paths -> `safe_input(..., context="firmware-manager.<scope>-select")`.
  - **Done when:** all three methods <=25 lines / CC<=5; helpers <=25 lines / CC<=5.
- [X] T-016 [US4] Decompose `_run_site_selection_loop` (26 lines), `_select_sites_for_org_upgrade` (33 lines), `_parse_selection_input` (27 lines), `_display_upgrade_plan_summary` (33 lines) via PCPP. `_parse_selection_input` is pure computation — omit non-compute slices.
  - **Done when:** all four methods <=25 lines; analyzer no longer flags any.

### Batch D: AP Bulk + Switch Path (4 offenders)

- [X] T-017 [US4] Decompose `_bulk_upgrade_ap_firmware_by_site` (37 lines) via PCPP: `_prepare_bulk_ap_context`, `_compute_bulk_ap_plan`, `_present_bulk_ap_preview`, `_persist_bulk_ap_results`. Rewrite the orchestrator.
  - **Done when:** method <=25 lines; helpers <=25 lines each.
- [X] T-018 [US4] Decompose `execute_switch_firmware_upgrade_with_mode_selection` (48 lines), `_bulk_upgrade_switch_firmware_by_site` (29 lines), `_upgrade_switch_firmware_by_gateway_template` (53 lines) via PCPP. Any `input(...)` -> `safe_input(..., context="firmware-manager.switch-<scope>-select")`.
  - **Done when:** all three methods <=25 lines; helpers <=25 lines each.

### Batch E: SSR Mode + Parsing + STRUCT-NESTING Line 1740 (4 offenders + 1 nesting)

- [X] T-019 [US4] Decompose `execute_ssr_firmware_upgrade_with_mode_selection` (59 lines) via PCPP. Any `input(...)` -> `safe_input(..., context="firmware-manager.ssr-scope-select")`.
  - **Done when:** method <=25 lines; helpers <=25 lines each.
- [X] T-020 [US4,US6] Decompose `_parse_ssr_site_selection` (28 lines, currently owns the STRUCT-NESTING depth-5 offender at line 1740 per FR-016) via PCPP. Apply R-7 early-return-guard flattening to eliminate the depth-5 nest. Also decompose `_get_ssr_available_versions` (33 lines) and `_select_ssr_version_from_list` (27 lines) in the same task since they are called from `_parse_ssr_site_selection`. `_select_ssr_version_from_list` includes an `input(...)` — wrap in `safe_input(..., context="firmware-manager.ssr-version-select")`.
  - **Done when:** all three methods <=25 lines; nesting depth <=3 in every extracted helper; analyzer STRUCT-NESTING finding for line 1740 clears.

### Batch F: SSR Inventory + Discovery + Validation (3 offenders)

- [X] T-021 [US4] Decompose `_confirm_ssr_upgrade` (39 lines), `_load_org_ssr_inventory` (31 lines), `_discover_site_ssr_devices` (26 lines) via PCPP. `_confirm_ssr_upgrade` includes an `input(...)` — wrap in `safe_input(..., context="firmware-manager.ssr-confirm")`. `_load_org_ssr_inventory` may write a CSV — ensure the path uses `os.path.join` (FR-022 opportunistic fix).
  - **Done when:** all three methods <=25 lines; every `input(` in these code paths is `safe_input(..., context=...)`.
- [X] T-022 [US4] Decompose `_validate_ssr_devices_for_version` (35 lines) and `_handle_ssr_upgrade_error_response` (40 lines, CC 10 per R-4). Because `_handle_ssr_upgrade_error_response` has CC 10 driven by HTTP status-code branching, split by status-code family into `_handle_ssr_client_error` / `_handle_ssr_server_error` / `_handle_ssr_unexpected_error` per R-4 rather than a single PCPP compute slice.
  - **Done when:** both methods <=25 lines / CC<=5; helpers <=25 lines / CC<=5.

### Batch G: SSR API + Site Loop + Bulk Paths (5 offenders)

- [X] T-023 [US4] Decompose `_call_ssr_upgrade_api` (34 lines), `_process_ssr_site_upgrade` (50 lines), `_run_ssr_site_upgrades` (29 lines) via PCPP. `_call_ssr_upgrade_api` is the actual `mistapi.*` invocation — preserve exact HTTP verb / URL / payload byte-for-byte (FR-023).
  - **Done when:** all three methods <=25 lines; API-call semantics unchanged.
- [X] T-024 [US4] Decompose `_bulk_upgrade_ssr_firmware_by_site` (56 lines) and `_upgrade_ssr_firmware_by_gateway_template` (57 lines) via PCPP. Any CSV output paths -> `os.path.join`. Any `input(...)` -> `safe_input(..., context="firmware-manager.ssr-<scope>-confirm")`.
  - **Done when:** both methods <=25 lines; every helper <=25 lines / <=5 blocks / CC<=5.

**Checkpoint**: All 32 MEDIUM STRUCT-LENGTH offenders (plus `__init__` from Phase 3) are decomposed = 33 total. Every STRUCT-COMPLEXITY, STRUCT-BLOCKS, and STRUCT-NESTING finding is cleared as a side effect of the PCPP splits + the two R-7 early-return-guard flattenings (T-014, T-020). Analyzer buckets STRUCT-LENGTH / STRUCT-COMPLEXITY / STRUCT-BLOCKS / STRUCT-NESTING / STRUCT-PARAMS all report 0. Only two buckets remain non-zero: CONV-COMMENTS (cleared in Phase 6) and CONV-NAME (three `for r in` sites, cleared in Phase 6). Score is ~85-90 at this checkpoint.

---

## Phase 6: User Story 5 + User Story 6 - Comment Coverage, Loop-Variable Renames, Logging Pattern, ASCII Fixes, safe_input, Path Hygiene

**Goal**: Push inline-comment coverage from 6.3% to >=90% (spec target — analyzer threshold is 80%, we leave a buffer). Clear the three CONV-NAME violations. Guarantee every `logging.*` call is ASCII-only lazy-form. Guarantee every `input(...)` is `safe_input(..., context=...)`. Guarantee every filesystem path is `os.path.join` / `pathlib.Path`. This is the largest single-diff phase in the plan.

**Independent Test**: `python -m tools.compliance_analyzer src/firmware/firmware_manager.py` reports zero CONV-COMMENTS and zero CONV-NAME findings, and inline-comment coverage >=90%. The Python one-liner from `quickstart.md` Step 5 finds zero non-ASCII log strings and zero f-strings inside `logging.*` calls. `grep -n "^\\s*input(" src/firmware/firmware_manager.py` returns nothing. `grep -n "for r in " src/firmware/firmware_manager.py` returns nothing.

- [X] T-025 [US5] Sweep the constructor cohort in `src/firmware/firmware_manager.py` — `__init__`, `_bind_module_globals`, `FirmwareManagerConfig` (fields + `__post_init__`), and the `org_id` / `apisession` properties — and confirm every executable line carries a `# WHY: <intent>` inline comment. Add missing comments. Every comment explains WHY the line exists (Constitution VI), not WHAT it does. Since these were introduced fresh in Phase 2-3, coverage should already be at 100% here — this task is the audit.
  - **Done when:** grep of the constructor cohort shows every executable line ends in `# WHY:` (or a functionally equivalent trailing `# <intent>` for the rare case where `# WHY:` reads awkwardly).
- [X] T-026 [US5] Sweep every helper introduced in Phase 4 (the ~16-20 helpers from T-008..T-011) in `src/firmware/firmware_manager.py` and confirm every executable line carries a `# WHY:` inline comment. Add missing comments. Also confirm each helper has `logging.info(...)` on its first executable line and `logging.debug(...)` on its last executable line before return (FR-019).
  - **Done when:** grep on each Phase-4 helper's body shows every executable line ends in `# WHY:` and each helper is bracketed by info-before / debug-after logging.
- [X] T-027 [US5] Sweep every helper introduced in Phase 5 (the ~40+ helpers from T-012..T-024) in `src/firmware/firmware_manager.py` and confirm every executable line carries a `# WHY:` inline comment. Add missing comments. Also confirm each helper has `logging.info(...)` on its first executable line and `logging.debug(...)` on its last executable line before return. This is the largest sub-task in the phase and may be split into three review-friendly sub-tasks (T-027a / T-027b / T-027c) if the diff becomes unwieldy — sub-splits use `Ta` / `Tb` letter suffixes without renumbering.
  - **Done when:** analyzer's inline-comment coverage metric on the file is >=90%; grep confirms info-before / debug-after brackets at every helper.
- [X] T-028 [US5] Sweep every remaining executable line in `src/firmware/firmware_manager.py` that was NOT touched by Phases 3-5 (i.e. methods the analyzer never flagged, but which still need to reach the file-wide >=80% coverage threshold). Add `# WHY:` comments to those lines. The measurement is file-wide, so untouched code that was already commented stays; untouched code that had no comment picks one up now.
  - **Done when:** `python -m tools.compliance_analyzer src/firmware/firmware_manager.py` reports CONV-COMMENTS count 0 and inline-comment coverage >=90%.
- [X] T-029 [US6] Rename the three single-letter loop variables at pre-refactor lines 1364 / 1373 / 1381 inside `_split_results_by_status` (or its post-Phase-5 successor helpers) in `src/firmware/firmware_manager.py` per R-8: `for r in results:` -> `for result in results:`; `for r in records:` -> `for record in records:`; `for r in report_rows:` -> `for report_row in report_rows:`. Every renamed line + every line inside the renamed loop body that references the loop variable is updated together. Each edited line carries a `# WHY:` inline comment (or reuses the existing one).
  - **Done when:** `grep -n "for r in " src/firmware/firmware_manager.py` returns zero matches; analyzer CONV-NAME count is 0.
- [X] T-030 [US5,US6] Audit every `input(...)` call in `src/firmware/firmware_manager.py` per FR-021. Every remaining raw `input(...)` (Phases 4-5 wrapped the touched ones opportunistically; this sweeps the rest) is wrapped in `safe_input(..., context="firmware-manager.<kebab-tag>")`. Grep-verify: `grep -nE "^\\s*[^#]*[^_a-zA-Z]input\\(" src/firmware/firmware_manager.py` returns nothing (excluding `safe_input` matches). Every edited call carries a `# WHY:` inline comment naming the prompt purpose.
  - **Done when:** no raw `input(...)` remains in the file; every prompt is `safe_input(..., context=...)`.
- [X] T-031 [US5,US6] Audit every `logging.*(...)` and every `print(...)` call in `src/firmware/firmware_manager.py` for non-ASCII characters per FR-020 and for f-string usage per FR-019 / spec Edge Case. Run the two Python one-liners from `quickstart.md` Step 5 (ASCII scan + f-string scan). Replace emoji with ASCII markers (`[OK]`, `[FAIL]`, `[SKIP]`), replace curly quotes with straight, replace en/em-dash with `-`, replace non-ASCII arrows with `->`. Convert any `logging.info(f"... {x}")` to `logging.info("... %s", x)` (lazy form). Every edited string carries an updated `# WHY:` inline comment.
  - **Done when:** the two one-liners from Step 5 emit zero lines; grep confirms no f-strings inside `logging.*` calls.
- [X] T-032 [US5,US6] Audit every filesystem path construction in `src/firmware/firmware_manager.py` per FR-022. Replace any raw `/` or `\\` string concatenation with `os.path.join(...)` or `pathlib.Path(...)`. Particularly around CSV output paths in `_persist_*` helpers. Add `import os` if not already imported (it should be). Every edited line carries a `# WHY:` inline comment.
  - **Done when:** grep `grep -nE '"[^"]*/[^"]*"' src/firmware/firmware_manager.py` shows no user-facing filesystem path built by concatenation (URL patterns like `/api/v1/orgs/{org_id}` are unaffected — those are mistapi paths, not filesystem paths).

**Checkpoint**: Analyzer reports zero findings across all seven rule buckets. Inline-comment coverage >=90%. Every `input(...)` is `safe_input(..., context=...)`. Every log string is ASCII-only lazy-form. Every filesystem path is `os.path.join` / `pathlib.Path`. Compliance score is 100.0 / A+. **The refactor's compliance work is complete.** The next phase migrates the sole permitted off-file callsite.

---

## Phase 7: User Story 2 - Migrate MistHelper.py Factory Body (the ONLY Permitted Off-File Diff)

**Goal**: Update `MistHelper.py` lines 18791-18807 (the `FirmwareManager.create` staticmethod body) to construct a `FirmwareManagerConfig` and pass it to the refactored impl class as a single positional argument. No other MistHelper.py change is permitted (FR-011, NG-002).

**Independent Test**: `grep -n "FirmwareManager\.create\|from src\.firmware\.firmware_manager" MistHelper.py` returns exactly the seven lines expected by `quickstart.md` Step 3. `python -c "from MistHelper import FirmwareManager; from unittest.mock import MagicMock; print(type(FirmwareManager.create(MagicMock(), 'test-org')).__name__)"` prints `FirmwareManager`. Menu 196 dry-run reaches the "no upgrades executed" summary (optional per `quickstart.md` Step 8).

- [X] T-033 [P] [US2] Update the `MistHelper.py` factory body at lines 18791-18807 per `contracts/constructor.md` "Caller-Site Contract Changes" -> "Site 1: MistHelper.py lines 18791-18807 (the ONLY permitted diff)". The After block is:

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

    Every new/edited executable line carries a `# WHY:` inline comment. The static-method signature `FirmwareManager.create(apisession, org_id)` is preserved verbatim so the five downstream callsites (19809, 22097, 22154, 22237, 22246) are byte-identical (contract C-6). The single existing `# noqa: PLC0415` on the deferred import is preserved because it predates this refactor and is not an analyzer-quieting suppression added by this change (compliant with FR-006).
  - **Done when:** `grep -n "FirmwareManager\.create\|from src\.firmware\.firmware_manager" MistHelper.py` returns exactly the seven expected lines from `quickstart.md` Step 3; the five downstream callsites are byte-identical to pre-refactor via `git diff MistHelper.py` (only lines 18791-18807 changed); Python REPL smoke `FirmwareManager.create(MagicMock(), 'test-org')` returns an instance without raising.

**Checkpoint**: Factory migration complete. All six MistHelper.py callsites are functional. Only the 17-line factory body diff exists in MistHelper.py. All menus (195, 196, SSR, switch, MSP) reach construction cleanly.

---

## Phase 8: Verification Gates (Polish & Cross-Cutting Concerns)

**Purpose**: Final verification, artifact capture, and reviewer-friendly documentation updates. Executes the eight `quickstart.md` steps in order and drops all outputs to `specs/1005-firmware-manager-compliance/artifacts/`.

- [X] T-034 Run the final compliance analyzer gate: `python -m tools.compliance_analyzer src/firmware/firmware_manager.py`. Save output to `specs/1005-firmware-manager-compliance/artifacts/final_compliance.txt`. Confirm score is **exactly 100.0**, grade is **A+**, and every rule bucket (`CONV-COMMENTS`, `CONV-NAME`, `STRUCT-BLOCKS`, `STRUCT-COMPLEXITY`, `STRUCT-LENGTH`, `STRUCT-NESTING`, `STRUCT-PARAMS`) reports 0 findings (FR-001, FR-002, FR-003, SC-001, SC-002, SC-003). Any single LOW-severity finding is a failure — no partial credit per `quickstart.md` Step 2.
  - **Done when:** artifact file reports `Score: 100.0`, `Grade: A+`, and zero findings across all seven rule buckets.
- [X] T-035 [P] Run the final ruff gate: `python -m ruff check src/firmware/firmware_manager.py`. Save output to `specs/1005-firmware-manager-compliance/artifacts/final_ruff.txt`. Confirm zero errors, zero warnings (FR-005, SC-007).
  - **Done when:** artifact file records exit code 0 and empty output.
- [X] T-036 [P] Run the final py_compile gate: `python -m py_compile src/firmware/firmware_manager.py`. Save exit code + any stderr to `specs/1005-firmware-manager-compliance/artifacts/final_pycompile.txt`. Confirm exit 0 (FR-004, SC-006).
  - **Done when:** artifact file records exit code 0.
- [X] T-037 [P] Run the six-callsite factory-wrapper insulation smoke per `quickstart.md` Step 3. Execute `grep -n "FirmwareManager\.create\|from src\.firmware\.firmware_manager" MistHelper.py` and confirm the output matches the seven lines expected by Step 3 exactly. Then execute `grep -rn "from src\.firmware\.firmware_manager" --include="*.py" .` and confirm exactly one match (the MistHelper.py factory-body import). Save both outputs to `specs/1005-firmware-manager-compliance/artifacts/callsite_smoke.txt` (FR-011, FR-012, contract C-6, SC-008).
  - **Done when:** artifact file shows the seven expected MistHelper.py lines and the single repo-wide import match.
- [X] T-038 Perform the inline-comment coverage spot check from `quickstart.md` Step 4: run the embedded Python coverage one-liner and confirm output `coverage=90.0%` or higher. Then randomly sample 25 executable lines from three regions (~lines 80-110 for `__init__` / `_bind_module_globals`; ~lines 700-730 inside a Phase-4 helper region; ~lines 1360-1385 for the renamed loop region) and count `# WHY:` (or equivalent trailing `# ...`) comments. Confirm at least 20 of 25 carry an inline comment (SC-005, SC-009). Save the coverage percentage and the 25-line sample results to `specs/1005-firmware-manager-compliance/artifacts/comment_sample.txt`.
  - **Done when:** artifact file records coverage >=90% and >=20/25 sampled lines commented.
- [X] T-039 Perform the logging pattern spot check from `quickstart.md` Step 5: grep for the info-before / debug-after pattern at each of the four HIGH-severity refactor sites plus `__init__`. Run the two Python one-liners (non-ASCII scan + f-string-in-logging scan) and confirm both emit empty output (FR-019, FR-020, SC-013). Save all outputs to `specs/1005-firmware-manager-compliance/artifacts/logging_audit.txt`.
  - **Done when:** artifact file records: info-before / debug-after present at every named site; empty output from both one-liners.
- [X] T-040 Perform the constructor-contract REPL smoke from `quickstart.md` Step 6: exercise all five cases (C-1 positive construction via `FirmwareManagerConfig`; C-2 legacy positional call raises `TypeError`; C-3 legacy kwargs call raises `TypeError`; C-4 frozen dataclass rejects mutation with `FrozenInstanceError`; C-5 empty `org_id` raises `ValueError`). All five cases must behave exactly as the Step-6 sample shows (FR-008, FR-009, FR-010, contracts C-1..C-5). Save the REPL transcript to `specs/1005-firmware-manager-compliance/artifacts/constructor_smoke.txt`.
  - **Done when:** transcript shows all five cases with the exact expected outcome; each case verified visually.
- [X] T-041 [P] Perform the loop-variable rename spot check from `quickstart.md` Step 7: `grep -n "for r in " src/firmware/firmware_manager.py` must return empty; `grep -n "for result in \|for record in \|for report_row in " src/firmware/firmware_manager.py` must return the three expected matches inside the `_split_results_by_status` region (SC-011, FR-017). Save output to `specs/1005-firmware-manager-compliance/artifacts/rename_smoke.txt`.
  - **Done when:** first grep is empty; second grep shows the three intended matches.
- [X] T-042 Optional: perform the menu 196 production-path manual smoke from `quickstart.md` Step 8 against a dry-run session. Launch `python MistHelper.py --dry-run`, select menu 196, walk through each sub-menu (status check, AP upgrade, SSR upgrade, MSP bulk), cancel at each confirmation prompt, and confirm the prompt sequence + log lines + CSV output paths are byte-identical vs. the pre-refactor branch (FR-023, FR-025, SC-014). Save the observed prompt sequence to `specs/1005-firmware-manager-compliance/artifacts/menu_196_smoke.txt`. Only required if a reviewer has doubts after T-034 through T-041 all pass.
  - **Done when:** transcript shows identical prompts / log lines / CSV paths vs. the pre-refactor branch; any divergence is treated as an FR-023 violation and returned to Phase 5-6 for fix.
- [X] T-043 [P] Update `.github/copilot-instructions.md` between the `<!-- SPECKIT START -->` and `<!-- SPECKIT END -->` markers to reference `specs/1005-firmware-manager-compliance/plan.md` as the active plan (per plan.md Phase 1 Deliverables). Every edited line carries a `# WHY:` inline comment where the target file's convention allows.
  - **Done when:** file diff shows only lines between the SPECKIT markers changed; those lines reference the 1005 plan.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies. Can start immediately.
- **Phase 2 (Foundational — T-DATACLASS)**: Depends on Phase 1 complete. **BLOCKS ALL USER STORY WORK.**
- **Phase 3 (US3 constructor)**: Depends on T-005 (T-DATACLASS) complete.
- **Phase 4 (US4 HIGH offenders)**: Depends on Phase 3 complete. Every task in Phase 4 also reads collaborators via `self._config.*_fn`, so the constructor refactor must land first.
- **Phase 5 (US4 MEDIUM offenders + US6 STRUCT-*)**: Depends on Phase 4 complete. All 13 tasks (T-012..T-024) edit the same file and must run sequentially.
- **Phase 6 (US5 comments + US6 CONV-NAME + logging + safe_input + paths)**: Depends on Phase 5 complete — comment/logging sweeps land on the fully-decomposed code, not the pre-refactor shape (otherwise every comment is thrown away when a method is split).
- **Phase 7 (US2 MistHelper.py factory-body migration)**: Depends on Phase 6 complete — the whole target file must be compliant before the callsite migration goes in. Technically Phase 7 could ship the same commit as Phase 6, but the analyzer must report 100.0 / A+ before T-033 lands.
- **Phase 8 (Polish)**: Depends on all Phases 1-7 complete. T-035 / T-036 / T-037 / T-041 / T-043 can run in parallel because they are read-only against the file (or edit a different file).

### T-DATACLASS Blocking Diagram

```text
                           T-005 (T-DATACLASS)
                                  |
                                  v
                          T-006, T-007 (US3 init)
                                  |
                                  v
                    T-008..T-011 (US4 HIGH offenders)
                                  |
                                  v
                    T-012..T-024 (US4 MEDIUM + US6 STRUCT-*)
                                  |
                                  v
              T-025..T-032 (US5 comments + US6 CONV-NAME + hygiene)
                                  |
                                  v
                        T-033 (US2 MistHelper.py migration)
                                  |
                                  v
                        T-034..T-043 (Phase 8 verification)
```

### Within Each User Story

- No formal test-first requirement (no test file exists per NG-001).
- Helpers before orchestrator rewrite (e.g. within each Phase-4 task, add the four PCPP helpers before rewriting the orchestrator).
- After each task the three-command gate (see top of file) must pass.
- Analyzer score must climb monotonically or stay flat — never regress by more than one within-task step that is recovered by the next task.

### Parallel Opportunities

- T-002 and T-003 (baseline capture) can run in parallel — different artifact files.
- T-035 / T-036 / T-037 / T-041 / T-043 (final verification gates + doc update) can run in parallel — read-only against the primary file (or edit an unrelated file).
- T-033 (MistHelper.py factory-body diff) is technically parallelizable with any read-only Phase-8 task after Phase 6 completes, but by convention it lands first as part of the "compliance work complete" commit.
- Everything else touches `src/firmware/firmware_manager.py` and must serialize.

---

## Parallel Example: Phase 8 Verification Fan-Out

```bash
# After T-033 (MistHelper.py migration) lands and analyzer at 100.0 / A+:

# Terminal 1 (analyzer artifact):
Task: T-034 python -m tools.compliance_analyzer src/firmware/firmware_manager.py > artifacts/final_compliance.txt

# Terminal 2 (ruff artifact):
Task: T-035 python -m ruff check src/firmware/firmware_manager.py > artifacts/final_ruff.txt

# Terminal 3 (py_compile artifact):
Task: T-036 python -m py_compile src/firmware/firmware_manager.py; echo $? > artifacts/final_pycompile.txt

# Terminal 4 (callsite grep artifact):
Task: T-037 grep -n "FirmwareManager.create" MistHelper.py > artifacts/callsite_smoke.txt

# Terminal 5 (loop-variable grep artifact):
Task: T-041 grep -n "for r in " src/firmware/firmware_manager.py > artifacts/rename_smoke.txt

# Terminal 6 (doc update):
Task: T-043 edit .github/copilot-instructions.md between SPECKIT markers
```

All six terminals converge to a passing three-command gate (analyzer 100.0 / A+, ruff clean, py_compile 0) and a signed-off artifacts directory.

---

## Implementation Strategy

### MVP First — This Refactor Has No Intermediate-Grade MVP

Unlike the 1004 campaign which allowed a grade-B partial merge, `spec.md` FR-001 through FR-003 require exactly 100.0 / A+ with zero findings. **There is no ship-able intermediate state.** Phases 1-8 must all complete before the branch merges. The recommended incremental delivery within the same branch is:

1. Phase 1 (Setup) -> baseline captured. **Score 51.0 / F.**
2. Phase 2 (T-DATACLASS) -> config dataclass exists. **Score ~52 (dataclass fields add commented lines).**
3. Phase 3 (US3 constructor) -> constructor collapsed. **Score ~55.** `__init__` no longer flagged.
4. Phase 4 (US4 HIGH offenders) -> four HIGHs cleared. **Score ~70.**
5. Phase 5 (US4 MEDIUM + US6 STRUCT-*) -> all STRUCT-* buckets clear. **Score ~87.** Only CONV-* buckets remain.
6. Phase 6 (US5 comments + US6 CONV-NAME) -> CONV-* clears. **Score 100.0 / A+.** Compliance work done.
7. Phase 7 (MistHelper.py migration) -> production menus functional. Score unchanged (100.0 / A+, target file only).
8. Phase 8 (Verification) -> artifacts captured. Score unchanged.

### Recommended Commit Boundaries

- One commit per phase: `refactor(firmware-manager): phase 1 baseline`, `refactor(firmware-manager): phase 2 T-DATACLASS`, ..., `refactor(firmware-manager): phase 8 verification`. Eight commits total.
- OR: one commit per task if the reviewer prefers finer-grained review. Estimated 43 commits.
- The "grade A+" milestone commit is `refactor(firmware-manager): phase 6 US5+US6 comment coverage and CONV-NAME` — the branch is ship-ready compliance-wise from that point, pending only the Phase-7 factory-body diff to reconnect production menus.

### Sub-Task Splitting Convention

If a task's diff becomes unwieldy for review (rule of thumb: >500 changed lines or >5 methods touched), split it into `T-XXXa`, `T-XXXb`, etc. rather than renumbering the rest of the plan. Prime candidates for pre-emptive sub-splitting:

- **T-027** (comment sweep across all Phase-5 helpers): estimate ~40 helpers. Split into T-027a (Batches A-B), T-027b (Batches C-D-E), T-027c (Batches F-G).
- **T-011** (`_execute_msp_upgrade_plan` decomposition, 97 lines + CC 10): estimate 5-6 helpers. Split into T-011a (prepare + compute), T-011b (present + persist + orchestrator) if the diff exceeds 500 lines.

---

## Notes

- Every task edits `src/firmware/firmware_manager.py` unless otherwise noted. Two exceptions: T-033 edits `MistHelper.py` lines 18791-18807 only; T-043 edits `.github/copilot-instructions.md` between the SPECKIT markers only. Baseline/verification tasks (T-001, T-002, T-003, T-004, T-034..T-042) write to `specs/1005-firmware-manager-compliance/artifacts/`.
- Every task's success is measured against the standing three-command gate at the top of this file — plus the task's own "Done when:" line.
- No wrapper / delegator / shim helpers may be introduced (FR-007). If a PCPP slice would be a 1-line forward, inline it.
- Every executable line new or edited must carry `# WHY:` inline commentary (Constitution VI, AGENTS.md non-negotiable, FR-018).
- Every new operation must be bracketed by `logging.info` before / `logging.debug` after (Constitution VII, AGENTS.md non-negotiable, FR-019).
- All log strings must be ASCII-only lazy `%s` / `%d` form (FR-020). All `input(...)` calls must use `safe_input(..., context=...)` (FR-021). All filesystem paths must use `os.path.join(...)` or `pathlib.Path(...)` (FR-022).
- No `# noqa`, `# type: ignore`, or `# pragma: no cover` markers may be added by this refactor on lines the analyzer would otherwise flag (FR-006). The single pre-existing `# noqa: PLC0415` on the MistHelper.py deferred import predates this feature and is preserved (T-033).
- The `FirmwareManagerConfig` dataclass lives in `src/firmware/firmware_manager.py` (FR-010). No new module is created (NG-004).
- The MistHelper.py factory-body diff is the sole permitted off-file change (FR-011, NG-002). Any additional MistHelper.py edit discovered mid-implementation is a scope violation — halt and re-plan.
- Task IDs are gap-friendly. If a task needs to be split during implementation, assign `T-XXXa`, `T-XXXb` rather than renumbering.
