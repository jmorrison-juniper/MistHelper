# Feature Specification: Org AP Upgrader Compliance Remediation

**Feature Branch**: `refactor/org-ap-upgrader-compliance`
**Spec Directory**: `specs/1006-org-ap-upgrader-compliance/`
**Created**: 2026-07-02
**Status**: Draft
**Target Module**: `src/firmware/org_ap_upgrader.py`
**Reference Pattern**: PR #3 (`src/firmware/firmware_manager.py`) — same successful shape

## Problem Statement

The org-level AP firmware upgrader module (`src/firmware/org_ap_upgrader.py`, 2393 LOC, 157 functions, one class `OrgLevelAPFirmwareUpgrader`) currently scores **60.0 / D-** on the project compliance analyzer. The baseline report at `specs/1006-org-ap-upgrader-compliance/artifacts/baseline_compliance_report.md` enumerates **27 violations**:

- **2 high**: 1 CONV-COMMENTS at file scope (inline comment coverage is only 16.0% — 12 concrete uncommented lines cited at 11, 13, 14, 15, 16, 17, 18, 71, 72, 73, 75, 76), and 1 STRUCT-PARAMS on `__init__` at line 41 (11 parameters, limit 5).
- **11 medium** STRUCT-LENGTH violations on functions exceeding 25 lines: `__init__` (45 lines @ L41), `_execute_msp_mode` (28 @ L178), `_confirm_msp_orgs` (31 @ L232), `_execute_org_upgrades` (42 @ L264), `_select_orgs_from_msp` (31 @ L448), `_step1_select_site_scope` (32 @ L761), `_fetch_org_aps` (27 @ L883), `_apply_version_selection` (28 @ L1340), `_configure_canary_phases` (26 @ L1928), `_execute_upgrades` (28 @ L2242), `_process_upgrade_response` (26 @ L2347).
- **14 low** STRUCT-COMPLEXITY violations on functions exceeding cyclomatic complexity 5: `run` (CC 6 @ L122), `_fetch_msp_orgs` (CC 6 @ L480), `_print_msp_summary` (CC 6 @ L670), `_fetch_org_aps` (CC 6 @ L883), `_get_org_inventory` (CC 6 @ L911), `_fetch_site_aps` (CC 6 @ L960), `_build_model_version_mapping` (CC 6 @ L1173), `_organize_by_version` (CC 7 @ L1458), `_step6_configure_upgrade` (CC 6 @ L1487), `_parse_time_input` (CC 7 @ L1597), `_try_parse_after` (CC 6 @ L1637), `_parse_canary_phase_values` (CC 7 @ L1906), `_print_dry_run_entry` (CC 6 @ L2199), `_process_upgrade_response` (CC 6 @ L2347).

The 16.0% inline comment coverage is the root cause of the CONV-COMMENTS high violation and drops the overall grade to D-. The 11-parameter `__init__` and eleven oversized functions prevent maintainer review under the project's 25-line function budget, while the fourteen CC>5 functions push branching decisions beyond the analyzer's target. Together they place this module at a **40-point deficit** from the project's A+ / 100.0 requirement.

MistHelper.py already depends on this module through **four lazy-import shims** (line 20237 docstring `"""Thin wrapper that delegates to src.firmware.org_ap_upgrader."""` and lines 20247, 20269, 20289, 20305 all doing `from src.firmware.org_ap_upgrader import OrgLevelAPFirmwareUpgrader as _Impl`). Any refactor must preserve those callsites verbatim and keep the public API surface byte-identical so NOC operators experience zero behavioral drift.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - NOC Engineer Runs the Upgrader Unchanged (Priority: P1)

A network operations engineer opens MistHelper, navigates to the org-level AP firmware upgrader menu, and runs the tool end-to-end (MSP mode, single-org mode, dry-run, canary phases, upgrade execution). The refactored module must behave byte-identically to the current implementation: same prompts, same order, same messages, same confirmations, same upgrade payload, same log lines, same return values, same exceptions.

**Why this priority**: The upgrader is a production tool that operators depend on to push firmware to APs across multiple orgs. Any observable change to prompt order, wording, timing, or output would surprise operators mid-upgrade and could cause them to abort or misroute a firmware push. Behavioral parity is the non-negotiable acceptance condition for merging.

**Independent Test**: Run the module through every menu entry point exercised by the 4 MistHelper.py lazy-import shims (lines 20247, 20269, 20289, 20305). Compare stdout/stderr, log lines, API payloads sent to Mist, and menu return codes against a baseline capture taken from `main` HEAD before the refactor. Diff must be empty for all user-visible artifacts.

**Acceptance Scenarios**:

1. **Given** an operator selects the org AP upgrader menu, **When** the refactored `OrgLevelAPFirmwareUpgrader(...).run()` executes with the same arguments and input keystrokes as the baseline, **Then** stdout, log lines, and Mist API payloads are identical to the baseline capture.
2. **Given** the operator is in MSP mode and confirms upgrades across multiple orgs, **When** `_execute_msp_mode` / `_confirm_msp_orgs` / `_execute_org_upgrades` run, **Then** every prompt appears in the same order with the same text, and the final upgrade payload matches the baseline byte-for-byte.
3. **Given** the operator picks canary phase timing, **When** `_configure_canary_phases` / `_parse_canary_phase_values` / `_parse_time_input` / `_try_parse_after` execute, **Then** the parsed phase objects and error branches match baseline behavior for every input the baseline test corpus covers.
4. **Given** the operator triggers dry-run output, **When** `_print_dry_run_entry` runs, **Then** every printed line matches the baseline character-for-character.

### User Story 2 - Maintainer Reviews the Module (Priority: P2)

A maintainer opens `src/firmware/org_ap_upgrader.py` for code review or extension. Every function is at most 25 lines, has cyclomatic complexity at most 5, takes at most 5 parameters, and every executable line carries a `# WHY:` inline comment explaining intent. The 11-parameter `__init__` has been replaced by a frozen, `slots=True`, `kw_only=True` `OrgAPUpgraderConfig` dataclass with `__post_init__` validation. Long orchestration functions have been decomposed using the Prepare / Compute / Persist / Present (PCPP) pattern and phase-helper extraction, mirroring the shape of `FirmwareManagerConfig` in PR #3.

**Why this priority**: Once the module ships to A+, every future edit inherits the compliance floor. Reducing per-function surface area and lifting comment coverage from 16% to the analyzer target directly cuts the time a reviewer spends locating the intent of any given line and prevents complexity regressions from slipping in.

**Independent Test**: Run the compliance analyzer (`python -m tools.compliance_analyzer src/firmware/org_ap_upgrader.py`) and verify a score of 100.0 / A+ with zero violations across all four rules (CONV-COMMENTS, STRUCT-PARAMS, STRUCT-LENGTH, STRUCT-COMPLEXITY). Independently, `git grep -nE "# noqa|# type: ignore|# pragma: no cover" src/firmware/org_ap_upgrader.py` must return zero matches.

**Acceptance Scenarios**:

1. **Given** a reviewer opens any function in the refactored module, **When** they read line by line, **Then** every executable line has a same-line `# WHY:` comment explaining intent, and no function exceeds 25 lines or CC 5.
2. **Given** the reviewer inspects `__init__`, **When** they read the constructor, **Then** it takes at most 5 parameters, delegating grouped state to an `OrgAPUpgraderConfig` frozen slots kw_only dataclass with `__post_init__` validation of each field.
3. **Given** the reviewer greps for suppressions, **When** they run `git grep -nE "# noqa|# type: ignore|# pragma: no cover"` against the module, **Then** zero matches are returned.

### User Story 3 - CI Gate Operator Merges the PR (Priority: P3)

The CI gate operator (or automated CI job) runs the standard project quality gates on the PR: compliance analyzer, ruff, black, mypy strict, pytest. Every gate passes cleanly without threshold relaxation, config edits, or suppression comments. Baseline analyzer artifacts (`baseline_compliance_report.md`, `baseline_lint.txt`) remain in `specs/1006-org-ap-upgrader-compliance/artifacts/` so the delta from 60.0 / D- to 100.0 / A+ is auditable in the PR history.

**Why this priority**: Merging cleanly through the existing CI matrix, with no analyzer config changes, is the only way to guarantee the improvement is real rather than accounting. The audit trail (baseline vs. final analyzer report side-by-side in the spec directory) is what allows a future reviewer to trust that the score jump is legitimate.

**Independent Test**: On the feature branch, run in sequence: `python -m tools.compliance_analyzer src/firmware/org_ap_upgrader.py` (expect 100.0 / A+, 0 violations), `ruff check src/firmware/org_ap_upgrader.py` (expect exit 0), `black --check src/firmware/org_ap_upgrader.py` (expect exit 0), `mypy --strict src/firmware/org_ap_upgrader.py` (expect exit 0), and the module's associated pytest suite (expect same pass count as `main`). Confirm `git diff main -- pyproject.toml setup.cfg tools/compliance_analyzer/` shows no analyzer-threshold changes.

**Acceptance Scenarios**:

1. **Given** the CI gate operator runs the compliance analyzer against the refactored module, **When** the tool exits, **Then** it reports 100.0 / A+ with zero violations for all four rules.
2. **Given** the CI gate operator runs ruff, black, and mypy strict against the refactored module, **When** each tool exits, **Then** each exits with code 0 and no warnings.
3. **Given** the CI gate operator runs the existing pytest suite, **When** the run completes, **Then** the pass count matches the pre-refactor baseline (no regressions, no skipped tests, no `# pragma: no cover`).
4. **Given** the CI gate operator diffs against `main`, **When** they inspect analyzer configuration files, **Then** no analyzer thresholds, budgets, or rule enablements have been relaxed.

### Edge Cases

- **Long orchestration functions where every line matters** (e.g., `_execute_org_upgrades` at 42 lines, `__init__` at 45 lines): decomposition must preserve execution order and log sequence — helper extraction is a mechanical refactor, not a semantic rewrite.
- **Functions with CC 7 driven by input validation** (`_organize_by_version`, `_parse_time_input`, `_parse_canary_phase_values`): guard-clause extraction and small validator helpers must not change which inputs raise vs. return None vs. accept a default.
- **The 11-parameter `__init__` includes runtime handles** (session, logger, config paths, mode flags): the `OrgAPUpgraderConfig` dataclass must hold only stateless configuration; live handles remain direct constructor parameters within the 5-parameter budget.
- **MistHelper.py lazy imports use `as _Impl` aliasing**: the class name `OrgLevelAPFirmwareUpgrader` and module path `src.firmware.org_ap_upgrader` must not change.
- **ASCII-only log constraint**: any new log strings introduced during decomposition must remain ASCII (no unicode arrows, checkmarks, or emoji).
- **`input()` usage during interactive prompts**: any prompt call must go through `safe_input(context=...)` with an explicit context string; direct `input(...)` calls are forbidden.

## Requirements *(mandatory)*

### Functional Requirements

**Public API preservation**

- **FR-001**: The class `OrgLevelAPFirmwareUpgrader` MUST retain its current fully-qualified path `src.firmware.org_ap_upgrader.OrgLevelAPFirmwareUpgrader` so the four lazy imports in MistHelper.py (lines 20247, 20269, 20289, 20305) continue to resolve unchanged.
- **FR-002**: The constructor call signature `OrgLevelAPFirmwareUpgrader(...)` as invoked by MistHelper.py MUST remain compatible; if the underlying `__init__` is decomposed to accept a config dataclass, a compatibility path MUST still accept the current argument list (either through positional/keyword acceptance or by having MistHelper.py pass a config object that the refactor builds — no shim wrapper class or delegator module allowed).
- **FR-003**: The instance method `.run()` MUST retain its current signature, return contract, and side-effect sequence byte-identical to `main` HEAD as observed by stdout, log lines, and Mist API payloads.
- **FR-004**: The docstring on line 20237 of MistHelper.py (`"""Thin wrapper that delegates to src.firmware.org_ap_upgrader."""`) MUST remain accurate — the refactor MUST NOT introduce a delegator or wrapper class inside `src/firmware/org_ap_upgrader.py` itself.

**Compliance remediation**

- **FR-005**: Every executable line of code in `src/firmware/org_ap_upgrader.py` MUST carry a same-line `# WHY:` inline comment describing intent, sufficient to bring inline comment coverage from 16.0% to the analyzer threshold that resolves CONV-COMMENTS.
- **FR-006**: Every function in the refactored module MUST have at most 5 parameters (STRUCT-PARAMS resolution for `__init__`).
- **FR-007**: Every function in the refactored module MUST span at most 25 lines (STRUCT-LENGTH resolution for the 11 listed functions).
- **FR-008**: Every function in the refactored module MUST have cyclomatic complexity at most 5 (STRUCT-COMPLEXITY resolution for the 14 listed functions).
- **FR-009**: The refactor MUST introduce an `OrgAPUpgraderConfig` frozen `slots=True` `kw_only=True` dataclass with a `__post_init__` method that validates each field, mirroring the `FirmwareManagerConfig` pattern established in PR #3.
- **FR-010**: Long orchestration functions (`__init__`, `_execute_msp_mode`, `_confirm_msp_orgs`, `_execute_org_upgrades`, `_select_orgs_from_msp`, `_step1_select_site_scope`, `_fetch_org_aps`, `_apply_version_selection`, `_configure_canary_phases`, `_execute_upgrades`, `_process_upgrade_response`) MUST be decomposed using the Prepare / Compute / Persist / Present (PCPP) pattern and phase-helper extraction, mirroring PR #3's shape.
- **FR-011**: High-CC functions (`run`, `_fetch_msp_orgs`, `_print_msp_summary`, `_fetch_org_aps`, `_get_org_inventory`, `_fetch_site_aps`, `_build_model_version_mapping`, `_organize_by_version`, `_step6_configure_upgrade`, `_parse_time_input`, `_try_parse_after`, `_parse_canary_phase_values`, `_print_dry_run_entry`, `_process_upgrade_response`) MUST have their branching reduced via guard clauses and small predicate/validator helpers.

**Operational conventions**

- **FR-012**: Every observable operation in the module MUST log `logging.info` before the operation begins and `logging.debug` after it completes. Existing log lines MUST be preserved; new log lines introduced by decomposition MUST follow the same before/after pattern.
- **FR-013**: All log message strings MUST be ASCII-only (no unicode arrows, checkmarks, box characters, or emoji).
- **FR-014**: Every interactive input prompt MUST use `safe_input(context=...)` with an explicit context string. Direct `input(...)` calls are forbidden.

**Non-negotiables (what MUST NOT happen)**

- **FR-015**: No `# noqa`, `# type: ignore`, or `# pragma: no cover` comments MAY be introduced anywhere in `src/firmware/org_ap_upgrader.py`. `git grep -nE "# noqa|# type: ignore|# pragma: no cover" src/firmware/org_ap_upgrader.py` MUST return zero matches on the final tree.
- **FR-016**: No wrapper, delegator, alias, or shim module or class MAY be introduced inside `src/firmware/org_ap_upgrader.py`. The refactor MUST land as an in-place rewrite of the existing module.
- **FR-017**: No analyzer threshold, budget, rule toggle, or exclusion in `pyproject.toml`, `setup.cfg`, `tools/compliance_analyzer/`, or any other configuration file MAY be relaxed to reach A+ / 100.0. The score gain MUST come entirely from source-level improvements.
- **FR-018**: The four MistHelper.py lazy-import shims at lines 20237, 20247, 20269, 20289, and 20305 MUST remain unchanged. No new imports, no reordering, no comment edits, no whitespace churn on those lines.

### Key Entities

- **`OrgLevelAPFirmwareUpgrader`** (existing class): the single public class exposed by the module. Public API surface is its constructor and its `.run()` method. Nothing else is imported by MistHelper.py.
- **`OrgAPUpgraderConfig`** (new frozen slots kw_only dataclass): groups the stateless configuration parameters previously taken as positional/keyword args on `__init__`, with `__post_init__` field validation. Direct mirror of `FirmwareManagerConfig` in PR #3.
- **Phase helpers** (new private module-scoped or class-scoped functions): extracted from the eleven oversized orchestration functions. Each helper covers one PCPP stage (Prepare / Compute / Persist / Present) or one canary phase / MSP org / upgrade step.
- **Validator/predicate helpers** (new small private functions): extracted from the fourteen high-CC functions to lift branching out of the caller and into named single-responsibility helpers.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The compliance analyzer, run against `src/firmware/org_ap_upgrader.py` on the feature branch tip, reports **100.0 / A+** with **zero** violations across CONV-COMMENTS, STRUCT-PARAMS, STRUCT-LENGTH, and STRUCT-COMPLEXITY. Delta from baseline: +40.0 points, D- to A+, 27 violations to 0.
- **SC-002**: Inline comment coverage on the module reaches the CONV-COMMENTS threshold that makes the analyzer stop reporting the rule — every executable line carries a `# WHY:` comment.
- **SC-003**: All 11 listed STRUCT-LENGTH functions span ≤ 25 lines after refactor; all 14 listed STRUCT-COMPLEXITY functions have cyclomatic complexity ≤ 5; `__init__` takes ≤ 5 parameters.
- **SC-004**: `ruff check`, `black --check`, and `mypy --strict` all exit cleanly against the refactored module. No warnings, no errors, no config relaxation.
- **SC-005**: The existing pytest suite for this module passes with the same pass count as `main` HEAD. No skipped tests, no new `# pragma: no cover`, no test-file edits that mask behavior change.
- **SC-006**: `git grep -nE "# noqa|# type: ignore|# pragma: no cover" src/firmware/org_ap_upgrader.py` returns zero lines on the feature branch tip.
- **SC-007**: `git diff main..HEAD -- MistHelper.py` shows zero changes to the four lazy-import shims at lines 20237, 20247, 20269, 20289, and 20305.
- **SC-008**: A NOC engineer running the upgrader through every entry point exercised by the four MistHelper.py lazy imports observes byte-identical stdout, log lines, and Mist API payloads compared to a `main` HEAD baseline capture.
- **SC-009**: `git diff main..HEAD -- pyproject.toml setup.cfg tools/compliance_analyzer/` shows no analyzer threshold, budget, or rule-enablement changes.

## Non-Goals

- **NG-001**: No behavioral changes. The refactor is byte-identical externally; every prompt, log line, API payload, exception, and return value stays exactly as it is on `main` HEAD.
- **NG-002**: No new features. No new menus, no new upgrade modes, no new logging levels, no new configuration options.
- **NG-003**: No changes to menu wiring inside MistHelper.py beyond preserving the four existing lazy-import shims verbatim. Menu numbers, menu ordering, menu prompts, and menu-to-module wiring all remain untouched.
- **NG-004**: No introduction of wrapper modules, delegator classes, or alias re-exports. The refactor lands in-place inside `src/firmware/org_ap_upgrader.py`.
- **NG-005**: No changes to analyzer thresholds, ruff/black/mypy configuration, or CI job definitions.
- **NG-006**: No relocation of `OrgLevelAPFirmwareUpgrader` to a different module path. The class stays at `src.firmware.org_ap_upgrader.OrgLevelAPFirmwareUpgrader`.
- **NG-007**: No introduction of unicode characters into log output, print output, or any user-facing string.

## Assumptions

- **A-001**: The analyzer rules and thresholds encoded in `tools/compliance_analyzer/` are the authoritative definition of the compliance target. A score of 100.0 with zero violations under the current ruleset is the acceptance bar.
- **A-002**: The `FirmwareManagerConfig` pattern from PR #3 (frozen `slots=True` `kw_only=True` dataclass with `__post_init__` validation, PCPP orchestration decomposition, phase-helper extraction) is the reference shape for this refactor. Any deviation must be justified in the plan phase.
- **A-003**: The four MistHelper.py lazy-import shims (line 20237 docstring, lines 20247/20269/20289/20305 `from ... import OrgLevelAPFirmwareUpgrader as _Impl`) are the complete set of external callsites. No other code in the repo imports this module directly.
- **A-004**: The existing pytest suite adequately covers the module's behavior for regression detection. Any gap in behavioral coverage must be surfaced in the plan phase, not silently accepted.
- **A-005**: Baseline artifacts already staged in `specs/1006-org-ap-upgrader-compliance/artifacts/` (`baseline_compliance_report.md`, `baseline_lint.txt`) capture the pre-refactor state and remain unchanged for the audit trail.
- **A-006**: The `safe_input(context=...)` helper is already available in the codebase and is the standard replacement for direct `input()` calls in this module.
- **A-007**: `logging.info` before / `logging.debug` after is the project's operational logging convention and matches usage elsewhere in `src/firmware/`.

## Reference: PR #3 Pattern (firmware_manager)

The successful precedent for this refactor is PR #3, which took `src/firmware/firmware_manager.py` to A+ / 100.0 using the following shape — reproduce it here:

1. **Introduce `OrgAPUpgraderConfig`**: a frozen `slots=True` `kw_only=True` `@dataclass` grouping the stateless configuration fields previously spread across `__init__`'s 11 parameters. Implement `__post_init__` field validation for each field so misconfiguration fails fast at construction.
2. **Shrink `__init__` to ≤ 5 parameters, ≤ 25 lines**: accept the config dataclass plus the live runtime handles (session, logger, etc.) that cannot live in a frozen dataclass.
3. **PCPP decomposition on orchestration functions**: split each of the 11 oversized functions into Prepare / Compute / Persist / Present helpers. Preserve execution order and log sequence byte-for-byte.
4. **Phase-helper extraction**: canary phases, MSP org iteration, per-org upgrade steps, and dry-run rendering each become small named helpers of ≤ 25 lines and CC ≤ 5.
5. **Guard-clause branching reduction**: the 14 CC-6/CC-7 functions get their branching lifted into predicate/validator helpers so the caller drops to CC ≤ 5.
6. **`# WHY:` on every executable line**: mechanical pass across the module to bring inline comment coverage over the CONV-COMMENTS threshold.
7. **Zero suppressions, zero config relaxation**: the final tree contains no `# noqa`, no `# type: ignore`, no `# pragma: no cover`, and no analyzer/ruff/black/mypy config edits.
