# Feature Specification: Firmware Manager Compliance Refactor

**Feature Branch**: `refactor/firmware-manager-compliance`
**Created**: 2026-07-02
**Status**: Draft
**Input**: User description: "Refactor `src/firmware/firmware_manager.py` to raise its compliance-analyzer grade from F (51.0/100) to A+ (100.0/100). 82 violations reported (6 High, 34 Medium, 42 Low). Preserve behavior; do not create wrappers/shims; real decomposition only; no `# noqa` or ignore flags."

## Summary

`src/firmware/firmware_manager.py` is the extracted implementation of the interactive firmware upgrade workflows for APs, switches, and SSR/session-smart routers. It is 2450 lines long, contains a single class `FirmwareManager` with 82 functions, and is currently graded **F (51.0 / 100)** by `tools.compliance_analyzer`. This is PR #3 of a five-part serial refactor campaign; each prior campaign (bulk AP upgrader, org AP upgrader) has lifted its target file from F to A+/100.0 using the same pattern: a frozen `slots` dataclass for constructor collaborators, phase-helper decomposition of oversized methods, and per-line `# WHY:` inline comments driven by the AGENTS.md standard.

The goal of this feature is to bring `firmware_manager.py` to **A+ (100.0 / 100)** — that is, **zero** violations of any severity across all seven analyzer rules (STRUCT-LENGTH, STRUCT-COMPLEXITY, STRUCT-BLOCKS, STRUCT-PARAMS, STRUCT-NESTING, CONV-COMMENTS, CONV-NAME). Every behavior consumed by `MistHelper.py` menu 195 / menu 196 / SSR upgrade menus / switch upgrade menus must be preserved. The only permitted change outside this file is a matching update to the `FirmwareManager.create(...)` factory in `MistHelper.py` to build the new configuration object.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reach A+ Compliance Grade (Priority: P1)

As a maintainer running the project's compliance analyzer as part of the code-review workflow, I need `src/firmware/firmware_manager.py` to score exactly 100.0/100 with grade A+ so the file is removed from the failing-grade dashboard and matches the standard set by the two prior campaign files (`bulk_ap_upgrader.py`, `org_ap_upgrader.py`).

**Why this priority**: The file currently scores 51.0/100 (grade F) with 82 recorded violations — 6 High, 34 Medium, 42 Low. Every audit run flags it as the worst offender in the `firmware/` package. Every downstream feature depends on this being fixed; nothing else in this spec has value without it. The prior two campaigns established that A+/100.0 is achievable and is the campaign's declared target, not merely "better than F".

**Independent Test**: Run `python -m tools.compliance_analyzer src/firmware/firmware_manager.py` from the repository root against the refactored file and confirm the numeric score reported is exactly 100.0/100, the grade letter is A+, and the per-severity totals are all zero (0 critical, 0 high, 0 medium, 0 low).

**Acceptance Scenarios**:

1. **Given** the refactored `firmware_manager.py` file on the `refactor/firmware-manager-compliance` branch, **When** a maintainer runs `python -m tools.compliance_analyzer src/firmware/firmware_manager.py`, **Then** the reported score is 100.0/100 and the reported grade is A+.
2. **Given** the analyzer's per-rule totals, **When** the maintainer inspects the JSON summary, **Then** every rule bucket (`CONV-COMMENTS`, `CONV-NAME`, `STRUCT-BLOCKS`, `STRUCT-COMPLEXITY`, `STRUCT-LENGTH`, `STRUCT-NESTING`, `STRUCT-PARAMS`) reports zero occurrences.
3. **Given** the refactored file, **When** a maintainer runs `python -m py_compile src/firmware/firmware_manager.py`, **Then** the command exits with status 0.
4. **Given** the refactored file, **When** a maintainer runs `python -m ruff check src/firmware/firmware_manager.py`, **Then** ruff reports zero errors and zero warnings.
5. **Given** the refactored file, **When** a reviewer greps for `# noqa`, `# type: ignore` (added by this refactor), or `# pragma: no cover` markers on lines that the analyzer would otherwise flag, **Then** none are present — the score comes from real structural change, not suppression.

---

### User Story 2 - Preserve MistHelper Callsite Compatibility (Priority: P1)

As the developer of `MistHelper.py` (lines 18795, 19809, 22097, 22154, 22237, 22246), I need the refactor to keep the `FirmwareManager.create(apisession, org_id)` factory shape working so menus that check firmware upgrade status, upgrade AP firmware, upgrade switch firmware, and upgrade SSR firmware continue to launch without modification beyond the single wrapper file.

**Why this priority**: The impl class is instantiated by production menu code through the `MistHelper.FirmwareManager.create(apisession, org_id)` staticmethod, which injects six callables (`safe_input_fn`, `select_site_fn`, `check_cache_fn`, `get_csv_path_fn`, `gateway_templates_fn`, `sites_fn`) as keyword arguments to the impl `__init__`. Silently breaking that call site would ship broken menus even if the compliance score passes. This must ship in the same change set as the constructor refactor. Menu 195 (bulk firmware upgrade) is a heavily used operator workflow; menu 196 was fixed in a prior commit and cannot regress here.

**Independent Test**: From the repository root, run `grep -n "FirmwareManager.create(" MistHelper.py` and confirm every match still resolves against the refactored impl without raising `TypeError`, `AttributeError`, or `ValueError`. Import the module and construct an instance via the factory: `python -c "from MistHelper import FirmwareManager; print(type(FirmwareManager.create(None, 'test-org-id')).__name__)"` — the call must succeed at construction time and return a `FirmwareManager` instance.

**Acceptance Scenarios**:

1. **Given** the refactored impl class in `src/firmware/firmware_manager.py`, **When** the `MistHelper.FirmwareManager.create(apisession, org_id)` factory in `MistHelper.py` (lines 18788-18807) is invoked, **Then** construction succeeds without raising an exception attributable to the refactor.
2. **Given** the factory's six injected callables (`safe_input_fn`, `select_site_fn`, `check_cache_fn`, `get_csv_path_fn`, `gateway_templates_fn`, `sites_fn`), **When** the factory builds an impl instance, **Then** every callable is stored on the instance (or the config object attached to the instance) and is invocable by the workflow methods with unchanged semantics.
3. **Given** any of the six callsites `FirmwareManager.create(...)` at MistHelper.py lines 19809, 22097, 22154, 22237, 22246 (plus the import at 18795), **When** the surrounding menu is invoked in dry-run mode, **Then** the menu proceeds past construction without raising a construction-time error.
4. **Given** the factory refactor, **When** a reviewer diffs `MistHelper.py`, **Then** the only permitted changes are inside the `FirmwareManager.create` staticmethod body (lines 18791-18807) and imports it touches — no menu-driver code paths are modified.
5. **Given** the refactored impl, **When** a reviewer inspects the `__init__` signature, **Then** it accepts at most 5 parameters (excluding `self`) — meeting the STRUCT-PARAMS limit — while still exposing enough injection surface for the factory to wire the six collaborators.

---

### User Story 3 - Consolidate Constructor Into Config Dataclass (Priority: P2)

As a maintainer, I need the current 8-parameter `__init__(self, apisession, org_id, safe_input_fn, select_site_fn, check_cache_fn, get_csv_path_fn, gateway_templates_fn, sites_fn)` constructor consolidated into a frozen `slots` dataclass — provisionally `FirmwareManagerConfig` — so the STRUCT-PARAMS violation clears and future collaborators can be added without breaching the 5-parameter limit again.

**Why this priority**: This is one of the two structural fixes required to hit A+. The current `__init__` reports both STRUCT-PARAMS (8 params vs 5 limit) and STRUCT-LENGTH (44 lines vs 25 limit). It also contains an inline `import sys as _sys` and mutates module-level globals via `sys.modules` — patterns that add hidden logical blocks. Consolidation into a dataclass matches the prior-art template from `specs/1004-bulk-ap-upgrader-compliance/` (`BulkAPUpgraderConfig`) and is required for the "no wrappers" rule while still keeping the injection surface intact.

**Independent Test**: Grep the refactored file for `def __init__(` — the resulting signature must accept `self` plus at most 5 named parameters. Grep for `@dataclass` or `@dataclasses.dataclass` — a `FirmwareManagerConfig` (or equivalently named) frozen `slots=True` dataclass must exist in the file or in an in-firmware-package sibling module, and each of the six legacy callables must map to a dataclass field.

**Acceptance Scenarios**:

1. **Given** the refactored file, **When** a reviewer inspects the `FirmwareManager.__init__` signature, **Then** it accepts no more than 5 parameters excluding `self`.
2. **Given** the refactored file, **When** the reviewer scans for a configuration dataclass, **Then** a `@dataclass(frozen=True, slots=True)` (or documented equivalent) exists whose fields correspond one-to-one with the previous six optional callables plus any required required-at-construction values.
3. **Given** the `FirmwareManager.__init__` body after refactor, **When** the analyzer measures it, **Then** it is <=25 executable lines, <=5 logical blocks, <=5 cyclomatic complexity, and <=4 nesting levels.
4. **Given** the module-globals side-effect currently performed inside `__init__` (populating `sys.modules[__name__].apisession`, `.org_id`, `.msp_privileges`, `.PROGRESS_EMITTER`), **When** the refactor moves it out of `__init__`, **Then** it lives in a dedicated helper (e.g. `_bind_module_globals`) that is <=25 lines and is called from `__init__` — the observable side effect is preserved.
5. **Given** the new dataclass, **When** a reviewer checks for a `__post_init__` or defensive default handling, **Then** any defaults (e.g. `safe_input_fn or input`) are moved into the dataclass so `__init__` receives fully-formed collaborators.

---

### User Story 4 - Decompose Oversized Workflow Methods (Priority: P2)

As a maintainer, I need the 36 methods that currently exceed STRUCT-LENGTH (25 lines) split into phase helpers, each of which is <=25 lines, <=5 logical blocks, <=5 cyclomatic complexity, and <=4 nesting levels, so the analyzer stops flagging every workflow entry point in the file.

**Why this priority**: STRUCT-LENGTH is the single largest rule-count driver (36 of 82 violations). Every high-severity STRUCT-LENGTH offender (`check_firmware_upgrade_status` at 61 lines, `_continuous_monitoring_mode` at 74 lines, `_upgrade_ap_firmware_by_gateway_template` at 69 lines, `_execute_msp_upgrade_plan` at 97 lines) is a workflow entry point that operators reach from the interactive menus. Splitting them into named phase helpers (following the `_stepN_*` pattern from `BulkAPFirmwareUpgrader`) makes the workflow readable for junior NOC engineers and clears the analyzer.

**Independent Test**: For each method listed in FR-013 below, count executable lines in the refactored version. Every method (original and extracted helper) must be <=25 lines. Re-run the analyzer and confirm zero STRUCT-LENGTH violations remain.

**Acceptance Scenarios**:

1. **Given** each STRUCT-LENGTH offender enumerated in FR-013, **When** measured after refactor, **Then** the method body is <=25 executable lines and every helper it delegates to is likewise <=25 lines.
2. **Given** each extracted helper, **When** a reviewer inspects it, **Then** it performs real work (parameter transformation, branching, iteration, logging, or I/O) — it is not a pure delegate that only forwards its arguments to another method.
3. **Given** the four HIGH-severity STRUCT-LENGTH offenders (`check_firmware_upgrade_status`, `_continuous_monitoring_mode`, `_upgrade_ap_firmware_by_gateway_template`, `_execute_msp_upgrade_plan`), **When** the analyzer runs, **Then** each is at or below the 25-line ceiling and no longer appears in the report at any severity level.
4. **Given** the refactored file, **When** a reviewer greps for methods whose body is a single `return self._other_method(...)` line, **Then** none exist as products of this refactor (excluding legitimate pre-existing thin methods that were never flagged).

---

### User Story 5 - Achieve 80%+ Inline Comment Coverage (Priority: P2)

As a reviewer performing an AGENTS.md compliance sweep, I need every executable line in the refactored file to carry an inline `# WHY: ...` comment so the file passes the 80%+ inline-comment floor enforced by `CONV-COMMENTS`. Coverage is currently 6.3%.

**Why this priority**: `CONV-COMMENTS` is one of the six HIGH-severity findings gating the A+ grade. Coverage is currently 6.3%, meaning ~93.7% of the file's ~1348 executable lines lack an inline `# WHY:` comment. Fixing it is mechanical but bulky. It depends on the structural decomposition being stable first (otherwise every line comment is thrown away when a method is split), which is why it is P2 rather than P1.

**Independent Test**: Run the compliance analyzer and confirm zero `CONV-COMMENTS` violations remain. Independently, a reviewer samples any 25 executable lines from the refactored file and finds an inline `# WHY: ...` (or equivalent `# ...`) comment on all 25, with each comment explaining why the line exists rather than what it literally does.

**Acceptance Scenarios**:

1. **Given** the refactored file, **When** the analyzer reports inline-comment coverage, **Then** the reported percentage is >=80% and no `CONV-COMMENTS` violation appears in the JSON summary.
2. **Given** any executable line in the refactored file, **When** a reviewer reads it, **Then** it carries an inline `# WHY: ...` comment or an equivalent trailing `# ...` that names the intent of the line rather than paraphrasing the code.
3. **Given** the refactored file's log emissions, **When** a reviewer scans them, **Then** every string is ASCII-only (no emoji, no curly quotes, no non-ASCII characters).
4. **Given** every existing `input(...)` call in the file, **When** the reviewer inspects it, **Then** it is wrapped in `safe_input(...)` (via `self._safe_input_fn` or the analog on the config object) with an explicit `context=` keyword tag identifying the prompt purpose.

---

### User Story 6 - Clear Remaining Complexity, Blocks, Nesting, and Naming Violations (Priority: P3)

As a maintainer, I need the 28 STRUCT-COMPLEXITY, 11 STRUCT-BLOCKS, 2 STRUCT-NESTING, and 3 CONV-NAME violations resolved through real decomposition and renaming — not suppression — so every remaining analyzer bucket lands at zero and the grade reaches A+.

**Why this priority**: These findings do not, individually, block a passing grade, but the campaign target is A+/100.0 — every violation bucket must land at zero. Most of these findings overlap with the STRUCT-LENGTH decomposition targeted by User Story 4: splitting a 60-line method typically also drops its complexity, block count, and nesting depth. The three CONV-NAME findings (single-letter `r` loop variables at lines 1364, 1373, 1381) are trivially renameable to descriptive identifiers (e.g. `result_row`, `result_record`).

**Independent Test**: Run the analyzer and confirm zero occurrences in each of these buckets: `STRUCT-COMPLEXITY`, `STRUCT-BLOCKS`, `STRUCT-NESTING`, `CONV-NAME`. Grep the refactored file for `for r in ` — zero matches.

**Acceptance Scenarios**:

1. **Given** the refactored file, **When** the analyzer runs, **Then** the JSON summary reports zero `STRUCT-COMPLEXITY`, zero `STRUCT-BLOCKS`, zero `STRUCT-NESTING`, and zero `CONV-NAME` violations.
2. **Given** the two STRUCT-NESTING offenders (`execute_firmware_upgrade_with_mode_selection` at line 750, `_parse_ssr_site_selection` at line 1740), **When** measured after refactor, **Then** each method's maximum nesting depth is <=4.
3. **Given** each STRUCT-COMPLEXITY offender (28 methods total, complexity range 6-10), **When** measured after refactor, **Then** each method's cyclomatic complexity is <=5.
4. **Given** the eleven STRUCT-BLOCKS offenders (block counts 6-8), **When** measured after refactor, **Then** each method contains <=5 logical blocks.
5. **Given** the three CONV-NAME violations at lines 1364, 1373, 1381 (single-letter `r`), **When** a reviewer greps the refactored file, **Then** no single-letter loop or comprehension variables remain in any modified code path.

---

### Edge Cases

- What happens if `MistHelper.FirmwareManager.create` is invoked with the current 8-kwarg pattern before the wrapper is updated? The impl's new `__init__` MUST fail fast with a `TypeError` naming the expected `FirmwareManagerConfig` parameter — no silent argument discard. The wrapper MUST be updated in the same commit so this scenario is not user-visible.
- What happens if a method's decomposition produces a helper that is itself 26+ lines? That is not acceptable — the helper MUST be split further. There is no "one more helper is close enough" exception.
- What happens if a `logging` call currently contains an f-string (e.g. `logging.info(f"...")`) instead of the lazy `%s` form flagged by `CONV-LOG-FSTRING` in AGENTS.md? The refactor MUST convert it to the `logging.info("... %s", value)` lazy form. (The current analyzer does not report `CONV-LOG-FSTRING` for this file, but AGENTS.md requires the lazy form; new logs added by the refactor MUST use lazy form.)
- What happens if the impl's `__init__` currently mutates `sys.modules[__name__].apisession`, `.org_id`, `.msp_privileges`, `.PROGRESS_EMITTER`? That side effect MUST be preserved — some methods in the file still use `global apisession` / `global org_id` and rely on those module-level names. The refactor MUST retain the side effect through a small helper method, not remove it.
- What happens if an extracted helper needs to see instance state that was previously local to the parent method? The helper MUST accept that state via parameters (respecting the 5-parameter limit) or read it from `self` — but the refactor MUST NOT introduce new module-level globals.
- What happens if a workflow method emits an interactive prompt via raw `input(...)`? It MUST be routed through `self._safe_input_fn(...)` (or `self._config.safe_input_fn(...)`) with `context=` set to a short kebab-case tag naming the prompt (e.g. `context="firmware-scope-select"`).
- What happens if a filesystem path is constructed via string concatenation? It MUST be rewritten to use `os.path.join(...)` or `pathlib.Path(...)`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The compliance analyzer (`python -m tools.compliance_analyzer src/firmware/firmware_manager.py`) MUST report a numeric score of 100.0/100 and a letter grade of A+ for the refactored file.
- **FR-002**: The analyzer's per-severity totals MUST all be zero: 0 critical, 0 high, 0 medium, 0 low.
- **FR-003**: The analyzer's per-rule totals MUST all be zero for every rule: `CONV-COMMENTS`, `CONV-NAME`, `STRUCT-BLOCKS`, `STRUCT-COMPLEXITY`, `STRUCT-LENGTH`, `STRUCT-NESTING`, `STRUCT-PARAMS`.
- **FR-004**: The refactored file MUST pass `python -m py_compile src/firmware/firmware_manager.py` with exit status 0.
- **FR-005**: The refactored file MUST pass `python -m ruff check src/firmware/firmware_manager.py` with zero errors and zero warnings.
- **FR-006**: The refactor MUST NOT add `# noqa`, `# type: ignore` on lines the analyzer would otherwise flag, or `# pragma: no cover` markers as a substitute for real structural fixes. Analyzer-quieting suppressions are prohibited.
- **FR-007**: The refactor MUST NOT introduce wrapper, delegator, or shim methods. A "wrapper/delegator/shim" is a helper whose entire body is a single call to another method with unchanged or trivially forwarded arguments and no additional logic. Every extracted helper MUST perform genuine work.
- **FR-008**: The `FirmwareManager.__init__` method MUST accept at most 5 parameters excluding `self`. The current 8-parameter list MUST be consolidated into a single frozen `slots` dataclass (provisionally named `FirmwareManagerConfig`) that carries the previously optional callables.
- **FR-009**: The `FirmwareManager.__init__` body MUST be <=25 executable lines, <=5 logical blocks, <=5 cyclomatic complexity, and <=4 nesting levels after refactor. Module-global binding logic currently inline in `__init__` MUST be moved to a dedicated helper (e.g. `_bind_module_globals`) that itself conforms to the size limits.
- **FR-010**: The new configuration dataclass MUST live in the same file (`src/firmware/firmware_manager.py`) unless a circular-import barrier requires a separate module inside `src/firmware/`, in which case placement MUST be justified in the plan phase.
- **FR-011**: The `MistHelper.FirmwareManager.create(apisession, org_id)` staticmethod at `MistHelper.py` lines 18791-18807 MUST be updated to construct the new configuration object and pass it to the refactored impl constructor. No other production code in `MistHelper.py` MUST be modified by this feature.
- **FR-012**: Every call site of `FirmwareManager.create(...)` in `MistHelper.py` (lines 19809, 22097, 22154, 22237, 22246) MUST continue to succeed at construction time without argument changes at the callsite.
- **FR-013**: Each of the following STRUCT-LENGTH offenders MUST be reduced to <=25 executable lines after refactor:
  - HIGH severity: `check_firmware_upgrade_status` (61 lines at line 182), `_continuous_monitoring_mode` (74 lines at line 244), `_upgrade_ap_firmware_by_gateway_template` (69 lines at line 522), `_execute_msp_upgrade_plan` (97 lines at line 1252).
  - MEDIUM severity: `__init__` (44 lines), `_is_firmware_downgrade` (36), `_show_org_level_upgrade_jobs` (49), `_load_template_sites_mapping` (30), `_prompt_template_selection` (56), `_execute_template_based_upgrade` (30), `execute_firmware_upgrade_with_mode_selection` (60), `_execute_msp_multi_org_upgrade` (45), `_select_msps_for_upgrade` (55), `_select_orgs_for_upgrade` (59), `_run_site_selection_loop` (26), `_select_sites_for_org_upgrade` (33), `_parse_selection_input` (27), `_display_upgrade_plan_summary` (33), `_bulk_upgrade_ap_firmware_by_site` (37), `execute_switch_firmware_upgrade_with_mode_selection` (48), `_bulk_upgrade_switch_firmware_by_site` (29), `_upgrade_switch_firmware_by_gateway_template` (53), `execute_ssr_firmware_upgrade_with_mode_selection` (59), `_parse_ssr_site_selection` (28), `_get_ssr_available_versions` (33), `_select_ssr_version_from_list` (27), `_confirm_ssr_upgrade` (39), `_load_org_ssr_inventory` (31), `_discover_site_ssr_devices` (26), `_validate_ssr_devices_for_version` (35), `_handle_ssr_upgrade_error_response` (40), `_call_ssr_upgrade_api` (34), `_process_ssr_site_upgrade` (50), `_run_ssr_site_upgrades` (29), `_bulk_upgrade_ssr_firmware_by_site` (56), `_upgrade_ssr_firmware_by_gateway_template` (57).
- **FR-014**: Each of the 28 STRUCT-COMPLEXITY offenders (methods with cyclomatic complexity 6-10) MUST be reduced to complexity <=5. Every method in the refactored file MUST report cyclomatic complexity <=5.
- **FR-015**: Each of the 11 STRUCT-BLOCKS offenders (methods with 6-8 logical blocks) MUST be reduced to <=5 logical blocks. Every method in the refactored file MUST report <=5 logical blocks.
- **FR-016**: The two STRUCT-NESTING offenders (`execute_firmware_upgrade_with_mode_selection` at line 750, `_parse_ssr_site_selection` at line 1740, both at depth 5) MUST be reduced to maximum nesting depth <=4. Every method in the refactored file MUST report nesting depth <=4.
- **FR-017**: The three CONV-NAME violations (single-letter loop variable `r` at lines 1364, 1373, 1381 inside `_split_results_by_status` and adjacent code) MUST be renamed to descriptive identifiers. No single-letter loop or comprehension variables MUST remain anywhere in the refactored file.
- **FR-018**: Inline-comment coverage MUST be >=80% as measured by the analyzer. Every executable line in the refactored file MUST carry an inline `# WHY: ...` (or equivalent trailing `# ...`) comment that explains why the line exists, not what it literally does.
- **FR-019**: Every method that performs I/O, mutation, an API call, a file operation, or a branch decision MUST emit `logging.info(...)` before the operation and `logging.debug(...)` after with a result summary, per AGENTS.md. New logging calls MUST use the lazy `%s`/`%d` form, not f-strings.
- **FR-020**: All log strings emitted by the refactored file MUST be ASCII-only. No Unicode characters, no emoji, no curly quotes, no non-ASCII dashes.
- **FR-021**: All `input(...)` calls in the refactored file MUST be routed through `safe_input(...)` (via `self._safe_input_fn` or the corresponding config field) and MUST pass an explicit `context=` keyword argument naming the prompt purpose in kebab-case.
- **FR-022**: All filesystem path construction in the refactored file MUST use `os.path.join(...)` or `pathlib.Path(...)`. Raw string concatenation with `/` or `\` separators is prohibited.
- **FR-023**: The refactor MUST NOT alter the observable side effects of any workflow: files written, log lines emitted at INFO level, `mistapi` calls made, prompts shown to the user, and module-global bindings (`sys.modules[__name__].apisession`, `.org_id`, `.msp_privileges`, `.PROGRESS_EMITTER`) MUST match the pre-refactor behavior for equivalent inputs.
- **FR-024**: Every extracted helper method MUST itself conform to all limits: <=5 parameters, <=25 lines, <=5 logical blocks, <=5 cyclomatic complexity, <=4 nesting levels. Splitting a large method into two 40-line helpers is not acceptable.
- **FR-025**: The public API surface consumed by external callers (`FirmwareManager` class name; `check_firmware_upgrade_status`, `execute_firmware_upgrade_with_mode_selection`, `execute_switch_firmware_upgrade_with_mode_selection`, `execute_ssr_firmware_upgrade_with_mode_selection`, and any other method named at a MistHelper.py callsite) MUST remain callable with the same argument shape.

### Key Entities

- **FirmwareManager**: The refactor's target class. Represents the interactive firmware upgrade workflow for APs, switches, and SSR devices — org-scope, site-scope, template-scope, and MSP-scope. Owns methods for status checks, upgrade planning, upgrade execution, and continuous monitoring. The refactor changes its internal structure but preserves its identity as the single entry point behind `MistHelper.FirmwareManager.create(...)`.
- **FirmwareManagerConfig** (proposed name; may be renamed in plan phase): A new `@dataclass(frozen=True, slots=True)` introduced to consolidate the six previously optional callable parameters (`safe_input_fn`, `select_site_fn`, `check_cache_fn`, `get_csv_path_fn`, `gateway_templates_fn`, `sites_fn`) plus any other collaborator state moved out of the constructor to satisfy STRUCT-PARAMS. Consumed by the refactored `__init__` in place of the flat parameter list.
- **Compliance Analyzer Report**: The tool output that validates the refactor. Represents per-file score, letter grade, and enumerated violation records with severity, rule ID, method name, line number, and metric value. Baseline captured at `specs/1005-firmware-manager-compliance/artifacts/baseline_compliance_report.md`; final version must show 0 violations across all buckets.
- **MistHelper Factory Wrapper**: The `class FirmwareManager` at `MistHelper.py` line 18788 with its `create(apisession, org_id)` staticmethod. Not part of `src/firmware/firmware_manager.py` but must be updated in lockstep so downstream callsites keep working; the update is the only permitted diff in `MistHelper.py` for this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The compliance-analyzer score for `src/firmware/firmware_manager.py` improves from 51.0/100 (grade F) to 100.0/100 (grade A+), a 49.0-point absolute improvement.
- **SC-002**: The total count of compliance-analyzer violations drops from 82 to 0 across all severity buckets (0 critical, 0 high, 0 medium, 0 low).
- **SC-003**: The analyzer's per-rule totals for `CONV-COMMENTS`, `CONV-NAME`, `STRUCT-BLOCKS`, `STRUCT-COMPLEXITY`, `STRUCT-LENGTH`, `STRUCT-NESTING`, and `STRUCT-PARAMS` all report 0.
- **SC-004**: Every method in the refactored file reports cyclomatic complexity <=5, executable-line length <=25, logical-block count <=5, nesting depth <=4, and parameter count <=5.
- **SC-005**: Inline-comment coverage as measured by the analyzer is >=80%.
- **SC-006**: `python -m py_compile src/firmware/firmware_manager.py` exits with status 0.
- **SC-007**: `python -m ruff check src/firmware/firmware_manager.py` reports zero errors and zero warnings.
- **SC-008**: All six existing callsites of `FirmwareManager.create(...)` in `MistHelper.py` (import at line 18795 plus factory calls at 19809, 22097, 22154, 22237, 22246) continue to instantiate and execute the class without raising `TypeError` or `AttributeError` attributable to the refactor.
- **SC-009**: A reviewer randomly sampling 25 executable lines from the refactored file finds an inline `# WHY: ...` (or equivalent trailing `# ...`) comment on at least 20 of them (80% floor).
- **SC-010**: A reviewer greps the refactored file for `# noqa`, `# type: ignore`, and `# pragma: no cover` markers added by this refactor on lines the analyzer would otherwise flag, and finds zero.
- **SC-011**: A reviewer greps the refactored file for `for r in ` and `for [a-z] in ` (single-letter loop variables) and finds zero matches.
- **SC-012**: A reviewer greps the refactored file for `logging.` and `.info(f"` / `.debug(f"` / `.warning(f"` / `.error(f"` (f-strings inside logging calls) and finds zero matches introduced by the refactor.
- **SC-013**: A reviewer greps the refactored file for non-ASCII characters inside string literals passed to `logging.` calls and finds zero matches.
- **SC-014**: A junior NOC engineer reading any single method in the refactored file understands within 60 seconds what the method does and why, without needing to read the whole class, by relying on the inline `# WHY: ...` comments and the method name.

## Non-Goals

The following are explicitly out of scope for this feature:

- **NG-001**: Adding new unit tests for `firmware_manager.py`. No `tests/unit/test_firmware_manager*.py` file exists today; this feature does not create one. A trivial smoke test (import + factory construction with mocked callables) MAY be added if it takes fewer than 20 lines total and does not exercise API-dependent code paths. Full test coverage is deferred to a follow-on feature.
- **NG-002**: Modifying any code in `MistHelper.py` outside the `class FirmwareManager` body at lines 18788-18807. Menu-driver code, other classes, and unrelated helpers MUST NOT be touched.
- **NG-003**: Modifying any other file in `src/firmware/` (e.g. `bulk_ap_upgrader.py`, `org_ap_upgrader.py`, `site_auto_upgrade.py`). Those files are governed by their own campaign spec directories.
- **NG-004**: Extracting helpers into a separate module unless a circular-import barrier forces it. The refactor's default is to keep everything in `src/firmware/firmware_manager.py`.
- **NG-005**: Changing the behavior of any workflow — files written, log lines, API calls, prompts, module-global bindings — beyond what is required to hit A+.
- **NG-006**: Adjusting the compliance analyzer's thresholds or rules to make the file pass. The analyzer is the authority; the code must move to the analyzer, not the other way around.
- **NG-007**: Renaming the `FirmwareManager` class or any of its public methods. Renaming private helpers is permitted during decomposition.
- **NG-008**: Merging or removing any of the file's 82 existing methods except by splitting or by absorbing pure single-line delegators (if any pre-exist) into their callers. Method count may grow substantially — that is expected.
- **NG-009**: Adding new runtime dependencies. The refactor uses only what is already imported at the top of the file plus `dataclasses` (standard library) and `pathlib` (standard library, if not already imported).
- **NG-010**: Fixing compliance issues in other files even when they surface incidentally during import-graph analysis. Cross-file issues belong to their own campaign PR.

## Assumptions

- The compliance analyzer tool at `tools/compliance_analyzer.py` (invoked as `python -m tools.compliance_analyzer`) is the authoritative grader. Its thresholds — max 5 parameters, max 25 lines, max 5 logical blocks, max complexity 5, max nesting 4, 80% inline-comment floor — are stable for the duration of this feature and will not be re-tuned mid-flight.
- Callers of `FirmwareManager` within this repository can be enumerated by grep. The six callsites in `MistHelper.py` are the complete set; there are no external consumers of the impl class outside the repository.
- The `safe_input` utility (`InputUtils.safe_input`) referenced in the factory wrapper exists in the codebase and honors the `context=` keyword.
- The `logging` module is already imported and configured at the file or package level; adding `logging.info`/`logging.debug` calls does not require new logger setup.
- No existing unit test file for `firmware_manager.py` exists (grep of `tests/unit` confirms only a string mention in `test_lint_diagram_refs.py`, no `test_firmware_manager*`). This feature therefore has no pre-existing test contract to preserve beyond the compliance analyzer's own output and the smoke-execution of the six MistHelper callsites.
- The `FirmwareManager.create(apisession, org_id)` factory in `MistHelper.py` is the only construction pattern in use. Direct `FirmwareManager(...)` instantiation with the current 8-kwarg pattern does not appear anywhere in production code and does not need a compatibility shim.
- The module-level global side effect (`sys.modules[__name__].apisession = ...` etc.) is intentional and required by legacy `global apisession` / `global org_id` declarations inside some methods. It is preserved but relocated out of `__init__` for line-count compliance.
- The refactor may increase total file line count due to added `# WHY:` inline comments, the new dataclass, and helper method boilerplate. There is no upper bound on total file length — only on per-method size.
- The prior-art template from `specs/1004-bulk-ap-upgrader-compliance/` (frozen `slots` dataclass + phase-helper decomposition + PCPP pattern) is the model. The plan phase for this feature will reuse it, adjusting only for firmware-manager-specific details (multiple workflow entry points instead of one, three device families instead of one).
- The refactor is performed on the branch `refactor/firmware-manager-compliance` off `main`. No sub-branches or worktrees are required.
- The file `src/firmware/firmware_manager.py` is 2450 lines long and contains one class with 82 functions as of the baseline compliance report dated 2026-07-02. Later plan / tasks / implement phases will operate against this baseline.
