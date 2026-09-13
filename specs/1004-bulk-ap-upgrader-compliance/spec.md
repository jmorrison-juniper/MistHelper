# Feature Specification: Bulk AP Upgrader Compliance Refactor

**Feature Branch**: `refactor/bulk-ap-upgrader-compliance`
**Created**: 2026-07-01
**Status**: Draft
**Input**: User description: "Refactor `src/firmware/bulk_ap_upgrader.py` to raise its compliance-analyzer grade from F (50.0/100) to at least B (>=80.0/100). 62 violations reported. Preserve behavior; do not create wrappers/shims; real decomposition only."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Restore Compliance Grade to Passing (Priority: P1)

As a maintainer running the project's compliance analyzer as part of the code-review workflow, I need `src/firmware/bulk_ap_upgrader.py` to score at least a B (>=80.0/100) so the file stops appearing on the failing-grade dashboard and blocking downstream module audits.

**Why this priority**: The file currently scores 50.0/100 (grade F) with 62 recorded violations. Every audit run flags it as one of the worst offenders in the `firmware/` package. Fixing the top-severity structural issues is the only path to green-lighting the module for downstream consumers of the AP-upgrade workflow (`org_ap_upgrader`, `site_auto_upgrade`, menu 195). Nothing else in this feature has value without this outcome.

**Independent Test**: Run `python -m tools.compliance_analyzer src/firmware/bulk_ap_upgrader.py` from the repository root against the refactored file and confirm the numeric score reported is >=80.0 and the grade letter reported is B or better. No other module needs to change for this validation.

**Acceptance Scenarios**:

1. **Given** the refactored `bulk_ap_upgrader.py` file on the `refactor/bulk-ap-upgrader-compliance` branch, **When** a maintainer runs `python -m tools.compliance_analyzer src/firmware/bulk_ap_upgrader.py`, **Then** the reported score is >=80.0/100 and the reported grade is B or better.
2. **Given** the refactored file, **When** a maintainer runs `python -m py_compile src/firmware/bulk_ap_upgrader.py`, **Then** the command exits with status 0 and no syntax errors.
3. **Given** the refactored file, **When** a maintainer runs `python -m ruff check src/firmware/bulk_ap_upgrader.py`, **Then** ruff reports zero errors and zero warnings.
4. **Given** the refactored file, **When** a maintainer greps for `def __init__(` in the file, **Then** the constructor signature accepts at most 5 parameters (excluding `self`), matching the AGENTS.md parameter-count ceiling.

---

### User Story 2 - Preserve Existing Caller Contracts (Priority: P1)

As a developer of `MistHelper.py` menu 195 (and any other caller that instantiates `BulkAPFirmwareUpgrader` and invokes `.execute()`), I need the refactor to preserve or cleanly migrate the public entry points so my menu keeps launching the bulk-upgrade workflow without regression.

**Why this priority**: The class is instantiated by production menu code with a fixed positional/keyword argument shape. Silently breaking that call site would ship a broken menu even if the compliance score passes. This must ship in the same change set as the constructor refactor.

**Independent Test**: Locate every call site of `BulkAPFirmwareUpgrader(` in the repository (`grep -rn "BulkAPFirmwareUpgrader(" src/ MistHelper.py`), confirm each caller is either compatible with the new signature or updated to construct the new configuration object, and instantiate + `.execute()` the class from a REPL to verify no `TypeError` is raised at import or at construction time.

**Acceptance Scenarios**:

1. **Given** any existing caller of `BulkAPFirmwareUpgrader(...)`, **When** the caller is executed against the refactored class, **Then** construction succeeds without raising `TypeError`, `AttributeError`, or `ValueError` attributable to the refactor.
2. **Given** the refactored class, **When** a developer calls `.execute()` on an instance, **Then** the 11-step workflow (`_step1_determine_sites` through `_step11_write_results`) still runs in the same order and produces the same observable side effects (file writes, log emissions, API calls) as the pre-refactor version for equivalent inputs.
3. **Given** the refactored module, **When** any test in the existing test suite that touches `bulk_ap_upgrader` is executed, **Then** the test passes without modification.

---

### User Story 3 - Meet AGENTS.md Documentation and Logging Standards (Priority: P2)

As a reviewer performing an AGENTS.md compliance sweep, I need every executable line in the refactored file to carry an inline `# why` comment and every meaningful operation to be bracketed by `logging.info(...)` (before) and `logging.debug(...)` (after) so the file passes the mandatory documentation and observability rules that gate the module for merge.

**Why this priority**: Inline-comment coverage is currently 0.2% against an 80% floor. This is one of the two HIGH-severity findings driving the F grade. Without it, User Story 1 cannot pass even if every method is decomposed. However, it depends on the structural decomposition being stable first, which is why it is P2 rather than P1.

**Independent Test**: Run the compliance analyzer's inline-comment metric in isolation (or grep-count executable lines vs. lines ending in `# ...` comments) on the refactored file and confirm coverage is >=80%. Independently, grep for `logging.info(` and `logging.debug(` around each public method entry and confirm the before/after pattern is present.

**Acceptance Scenarios**:

1. **Given** the refactored file, **When** the compliance analyzer reports inline-comment coverage, **Then** the reported percentage is >=80%.
2. **Given** any public or private method in the refactored file that performs I/O, mutation, or a branch decision, **When** a reviewer reads the method body, **Then** `logging.info(...)` appears before the operation and `logging.debug(...)` appears after with a result summary.
3. **Given** the refactored file, **When** a reviewer scans emitted log strings, **Then** all strings are ASCII-only (no emoji, no non-ASCII characters).
4. **Given** any `input(...)` call in the refactored file, **When** the reviewer inspects the call, **Then** it is wrapped in `safe_input(...)` with an explicit `context=` keyword tag.

---

### User Story 4 - Resolve Top MEDIUM-Severity Function Complexity (Priority: P2)

As a maintainer, I need the eight-to-ten worst MEDIUM-severity function-complexity offenders decomposed into smaller helpers so the compliance analyzer stops flagging them and the file grade clears B.

**Why this priority**: HIGH-severity fixes alone will not lift the score above 80. The compliance analyzer weighs MEDIUM findings, and the top ~8 function-length/complexity offenders are the biggest remaining drag. Fixing all 62 findings is out of scope; fixing the top ones named in the input is in scope.

**Independent Test**: For each targeted method listed in the "In-Scope MEDIUM Offenders" section below, measure its post-refactor line count and logical-block count. Confirm each is <=25 lines and <=5 logical blocks. Then re-run the compliance analyzer and confirm the file grade is B or better.

**Acceptance Scenarios**:

1. **Given** each in-scope MEDIUM offender listed in this spec, **When** measured after refactor, **Then** the method body is <=25 executable lines and contains <=5 logical blocks and <=4 levels of nesting.
2. **Given** the refactored file, **When** a reviewer checks that no helper is a pure delegate/wrapper/shim (i.e., a one-line method that only forwards to another), **Then** every extracted helper does real work — parameter transformation, branching, iteration, or I/O.
3. **Given** the refactored file, **When** the compliance analyzer runs, **Then** at least the ten MEDIUM offenders explicitly enumerated in this spec are no longer reported.

---

### User Story 5 - Address LOW-Severity Findings Where Touched (Priority: P3)

As a maintainer, I need the LOW-severity findings (single-letter loop variables at lines 587 and 595, and STRUCT-COMPLEXITY findings) fixed where the surrounding code is already being touched by higher-priority work, without expanding scope beyond what is necessary to reach grade B.

**Why this priority**: LOW findings do not, by themselves, block a B grade, but fixing them opportunistically inside code that is already being modified is nearly free and prevents the file from regressing when a future compliance rule tightens.

**Independent Test**: Grep the refactored file for `for v in` and confirm no single-letter loop variables remain in `_get_versions_for_model` (originally lines 584-608). Confirm named replacements exist and are descriptive.

**Acceptance Scenarios**:

1. **Given** the refactored file, **When** a reviewer greps for single-letter loop or comprehension variables, **Then** none remain in code paths that were modified by this feature.
2. **Given** the refactored file, **When** the compliance analyzer runs, **Then** STRUCT-COMPLEXITY findings that overlap the touched code paths are resolved even if the overall count of remaining STRUCT-COMPLEXITY findings elsewhere in the file is non-zero.

---

### Edge Cases

- What happens if a caller passes the 10 legacy positional arguments to the new constructor? The constructor MUST fail fast with a clear `TypeError` naming the expected configuration object, not silently discard arguments.
- How does the refactor handle callers that construct `BulkAPFirmwareUpgrader` via keyword arguments only? The specification requires either (a) the new configuration object accepts the same keyword names for a transition period, or (b) all in-repo callers are updated in the same commit as the constructor change.
- What happens if extracting a helper method would create a wrapper/delegator (a helper that only forwards to another method with no transformation)? The refactor MUST NOT create such a helper; it MUST either inline the logic or restructure the split.
- How does the refactor handle a method that currently has 34 lines but only 3 logical blocks? It is not required to be split further than the 25-line ceiling demands; a `# pragma: no cover` or analyzer-suppressor is NOT an acceptable substitute for real decomposition.
- What happens if a log message currently contains a non-ASCII character (emoji, curly quote, en-dash)? It MUST be rewritten to ASCII-only equivalents (e.g., `-` for en-dash, plain quotes, `[OK]` instead of a check-mark) as part of this feature.
- What happens if a target method's current implementation depends on shared mutable state (`self._current_config`, `self._model_ranges`, etc.)? Extracted helpers may read and write that state, but the refactor MUST NOT introduce new hidden mutation channels or module-level globals.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The compliance analyzer (`python -m tools.compliance_analyzer src/firmware/bulk_ap_upgrader.py`) MUST report a numeric score >=80.0 and a letter grade of B or better for the refactored file.
- **FR-002**: The refactored file MUST pass `python -m ruff check src/firmware/bulk_ap_upgrader.py` with zero errors and zero warnings.
- **FR-003**: The refactored file MUST pass `python -m py_compile src/firmware/bulk_ap_upgrader.py` with exit status 0.
- **FR-004**: The `BulkAPFirmwareUpgrader.__init__` method MUST accept at most 5 parameters (excluding `self`). The current 10-parameter list MUST be consolidated into a single dataclass or configuration object.
- **FR-005**: The `BulkAPFirmwareUpgrader.__init__` method body MUST be <=25 executable lines. Setup logic that exceeds this budget MUST be extracted into private helper methods that themselves conform to the size limits.
- **FR-006**: The refactored file's inline-comment coverage MUST be >=80% as measured by the compliance analyzer. Every executable line MUST carry an inline `# ...` comment explaining WHY the line exists, not WHAT it does.
- **FR-007**: Every public and private method that performs I/O, mutation, an API call, a file operation, or a branch decision MUST emit `logging.info(...)` before the operation and `logging.debug(...)` after with a result summary.
- **FR-008**: All log strings emitted by the refactored file MUST be ASCII-only. No Unicode characters, no emoji, no curly quotes, no non-ASCII dashes.
- **FR-009**: All `input(...)` calls in the refactored file MUST be wrapped in `safe_input(...)` and MUST pass an explicit `context=` keyword argument that names the prompt purpose.
- **FR-010**: All filesystem path construction in the refactored file MUST use `os.path.join(...)` or `pathlib.Path(...)`. Raw string concatenation with `/` or `\\` separators is prohibited.
- **FR-011**: The refactor MUST NOT introduce wrapper, delegator, or shim methods. A helper method is defined as a "wrapper/delegator/shim" if it consists solely of a single call to another method with unchanged or trivially forwarded arguments and no additional logic. All extracted helpers MUST perform genuine work (parameter transformation, branching, iteration, logging, or I/O).
- **FR-012**: The following in-scope MEDIUM-severity offenders MUST each be reduced to <=25 executable lines, <=5 logical blocks, <=5 cyclomatic complexity, and <=4 levels of nesting after refactor:
  - `execute` (currently 32 lines / 9 logical blocks at line 106)
  - `_select_strategy` (currently 43 lines at line 724)
  - `_estimate_api_calls` (currently 43 lines at line 850)
  - `_offer_additional_model_versions` (currently 46 lines / 8 blocks at line 1297)
  - `_fetch_ap_model_families` (currently 42 lines / 7 blocks at line 1231)
  - `_configure_auto_upgrade_schedule` (currently 38 lines at line 1463)
  - `_step11_write_results` (currently 50 lines at line 1624)
  - `_apply_version_selection` (currently 34 lines at line 651)
  - `_upgrade_version_group` (currently 34 lines at line 1121)
  - `_log_upgrade_results` (currently 34 lines at line 1184)
- **FR-013**: Single-letter loop variables at the pre-refactor line numbers 587 and 595 (inside `_get_versions_for_model` and adjacent code) MUST be renamed to descriptive identifiers. This rule applies to any single-letter loop or comprehension variable in code paths modified by this feature.
- **FR-014**: The public API surface consumed by external callers — the class name `BulkAPFirmwareUpgrader` and the `.execute()` method — MUST remain callable. Either (a) the constructor accepts a configuration object plus preserved keyword arguments for backward compatibility, or (b) every in-repo caller of `BulkAPFirmwareUpgrader(...)` is updated within this same feature branch.
- **FR-015**: The 11-step workflow ordering (`_step1_determine_sites` -> `_step2_discover_aps` -> ... -> `_step11_write_results`) driven by `execute()` MUST be preserved. The refactor MUST NOT reorder, merge, or skip steps.
- **FR-016**: Every extracted helper method MUST itself conform to the size limits: <=5 parameters, <=25 lines, <=5 logical blocks, <=5 cyclomatic complexity, <=4 nesting levels. Splitting a large method into two 40-line helpers is NOT acceptable.
- **FR-017**: The refactor MUST NOT alter the observable side effects of the workflow: files written by `_step11_write_results`, log lines emitted at INFO level, `mistapi` calls made in `_step8_execute_upgrades`, and prompts shown to the user MUST match the pre-refactor behavior for equivalent inputs.
- **FR-018**: Any new dataclass or configuration object introduced to consolidate the constructor parameters MUST live in the same file (`src/firmware/bulk_ap_upgrader.py`) unless a separate module is required to avoid a circular import, in which case placement MUST be justified in the plan phase.

### Key Entities

- **BulkAPFirmwareUpgrader**: The refactor's target class. Represents the interactive multi-step AP firmware upgrade workflow. Attributes include site selection state, discovered APs, firmware stats, upgrade strategy, and results. The refactor changes its internal structure but preserves its identity as the single entry point for the workflow.
- **BulkAPUpgraderConfig** (proposed name; may be renamed in plan phase): A new dataclass or configuration object introduced to hold the 10 legacy constructor parameters. Attributes correspond one-to-one with the legacy parameters. Consumed by the refactored `__init__` in place of the flat parameter list.
- **Compliance Analyzer Report**: The tool output that validates the refactor. Represents per-file score, letter grade, and enumerated violation records with severity, rule ID, method name, line number, and metric value.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The compliance-analyzer score for `src/firmware/bulk_ap_upgrader.py` improves from 50.0/100 (grade F) to >=80.0/100 (grade B or better), a minimum absolute improvement of 30 points.
- **SC-002**: The total count of compliance-analyzer violations for the file drops from 62 to a number consistent with grade B (empirically, <=15 remaining LOW-severity findings; zero HIGH-severity findings; at most 2 MEDIUM-severity findings, none of which appear in the in-scope list under FR-012).
- **SC-003**: 100% of the ten MEDIUM-severity function-complexity offenders enumerated in FR-012 no longer appear in the analyzer report after refactor.
- **SC-004**: 100% of HIGH-severity findings currently reported against `__init__` at line 43 (parameter count and body length) and against inline-comment coverage are resolved.
- **SC-005**: All existing production callers of `BulkAPFirmwareUpgrader` (currently at least `MistHelper.py` menu 195 and any callers in `src/firmware/`) continue to instantiate and execute the class without raising `TypeError` or `AttributeError` attributable to the refactor.
- **SC-006**: `python -m ruff check src/firmware/bulk_ap_upgrader.py` reports zero errors and zero warnings.
- **SC-007**: `python -m py_compile src/firmware/bulk_ap_upgrader.py` exits with status 0.
- **SC-008**: All existing automated tests that reference `bulk_ap_upgrader` continue to pass without test-code modification.
- **SC-009**: A reviewer randomly sampling 25 executable lines from the refactored file finds an inline `# why` comment on at least 20 of them (80% floor).
- **SC-010**: A reviewer scanning the refactored file for `logging.info(` before and `logging.debug(` after every non-trivial operation finds the pattern consistently applied in the ten targeted refactor sites listed in FR-012.

## Assumptions

- The compliance analyzer tool at `tools/compliance_analyzer.py` (invoked as `python -m tools.compliance_analyzer`) is the authoritative grader. Its current thresholds — max 5 parameters, max 25 lines, max 5 logical blocks, max complexity 5, max nesting 4, 80% inline-comment floor — are stable for the duration of this feature and will not be re-tuned mid-flight.
- Callers of `BulkAPFirmwareUpgrader` within this repository can be enumerated by grep. There are no external consumers of this class outside the repository, so no downstream deprecation notice is required beyond in-repo updates.
- The eleven `_stepN_*` workflow methods are already well-decomposed (they are named as steps and each has a bounded responsibility). Their internal implementations may need refactoring individually, but the workflow shape is out of scope for change.
- No caller depends on the internal names of extracted private helper methods. Only the class name `BulkAPFirmwareUpgrader` and the `.execute()` method are considered public API.
- The `safe_input` utility referenced in AGENTS.md exists in the codebase and is importable. Its `context=` keyword is honored by the wrapper.
- The `logging` module is already imported and configured at the file or package level; adding INFO/DEBUG calls does not require new logger setup.
- Test coverage for `bulk_ap_upgrader.py` is currently thin. This feature does not add new tests; the acceptance test is the compliance analyzer's own output plus manual smoke-execution of menu 195. Adding test coverage is a follow-on feature.
- LOW-severity STRUCT-COMPLEXITY findings that do not overlap the touched code paths (roughly 20-25 of the 26 reported) will remain unaddressed by this feature. They are explicitly deferred to a future compliance sweep. The B grade must be reachable without touching them.
- The refactor is performed on the existing branch `refactor/bulk-ap-upgrader-compliance` off `main`. No sub-branches or worktrees are required.
- The file `src/firmware/bulk_ap_upgrader.py` is 1673 lines long as of the start of this feature. The refactor may increase line count due to added `# why` comments and helper method boilerplate; there is no upper bound on total file length, only on per-method size.
