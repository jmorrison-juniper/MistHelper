# Feature Specification: Decompose Next 5 Functions

**Feature Branch**: `[196-decompose-next5-functions]`  
**Created**: 2026-06-01  
**Status**: Draft  
**Input**: User description: "Create a new SpecKit feature specification in the MistHelper repository for decomposing and refactoring the next 5 highest-complexity functions from MistHelper.py (current ranks 6-10), into separate modules/sub-modules under src/ while preserving behavior."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Safer Maintenance of High-Complexity Logic (Priority: P1)

As a maintainer, I need the five target high-complexity functions decomposed into semantically named modules/classes under `src/` so that the logic is easier to reason about, test, and safely modify without changing user-visible behavior.

**Why this priority**: This directly reduces operational risk in heavily used workflows while preserving production behavior for junior NOC operators.

**Independent Test**: Can be fully tested by running parity tests for each of the five target workflows and confirming menu prompts, outputs, and side effects are unchanged.

**Acceptance Scenarios**:

1. **Given** baseline behavior for each target workflow, **When** the refactored code is executed through the same entry paths, **Then** prompts, branching behavior, output payloads/files, and side effects match baseline expectations.
2. **Given** the refactored code, **When** complexity is measured, **Then** each target function is at or below cyclomatic complexity 10.

---

### User Story 2 - Reliable Verification and Regression Safety (Priority: P2)

As a release engineer, I need explicit complexity and quality-gate verification evidence so I can approve the change with confidence and without manual guesswork.

**Why this priority**: This ensures objective evidence that refactoring quality and behavioral safety standards are met before merging.

**Independent Test**: Can be independently tested by executing the required verification command set and confirming all commands succeed with recorded evidence.

**Acceptance Scenarios**:

1. **Given** the completed refactor, **When** verification commands are executed, **Then** complexity thresholds and quality gates pass with documented results.
2. **Given** targeted and broader regression test suites, **When** tests run after refactoring, **Then** no regressions are introduced in touched behaviors.

---

### User Story 3 - Operationally Safe Refactor Execution (Priority: P3)

As an operations lead, I need explicit safety controls embedded in the refactor scope so that business-critical and potentially destructive flows are not unintentionally altered.

**Why this priority**: Network operations tooling must preserve safety semantics and decision points to prevent accidental operator-impacting changes.

**Independent Test**: Can be independently tested by validating that confirmation gates, error handling behavior, and logging/audit expectations remain intact for touched flows.

**Acceptance Scenarios**:

1. **Given** workflows that include confirmations, waits, and download side effects, **When** refactored code executes, **Then** safety gates and execution order remain unchanged.
2. **Given** failure and timeout conditions, **When** refactored paths are triggered, **Then** failure handling, retries, and user-facing messaging remain behaviorally equivalent.

### Edge Cases

- One or more target functions share helper logic that could cause accidental behavior drift when extracted.
- Refactoring reduces complexity in the parent function but shifts hidden complexity into improperly named or wrapper-like helpers.
- Timeout and polling branches in packet-capture workflows behave differently under transient API failures.
- Interactive prompt flows (`run_interactive_test`) may change prompt order or text if decomposition is not parity-checked.
- Wi-Fi client export flows may preserve content but change ordering or formatting in ways that impact downstream expectations.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST refactor the following target functions from `MistHelper.py` into semantically named modules/sub-modules under `src/` while preserving behavior: `wifi_clients` (~line 16092), `run_interactive_test` (~line 28046), `_wait_and_download_pcap_org` (~line 8397), `_wait_and_download_pcap` (~line 8223), and `_start_site_scan_capture_all_aps` (~line 7094).
- **FR-002**: The system MUST reduce each target function to cyclomatic complexity `<=10`.
- **FR-003**: The system MUST decompose logic into meaningful classes/modules and MUST NOT introduce thin wrappers that only delegate without adding semantic responsibility.
- **FR-004**: The system MUST preserve CLI and menu prompts exactly in intent and operator flow, including confirmations, error prompts, and progress messaging.
- **FR-005**: The system MUST preserve outputs and side effects for each target workflow, including generated files, API interactions, retries/polling behavior, and state changes.
- **FR-006**: The system MUST add or adjust unit and integration parity tests covering normal, edge, and failure paths for all five target workflows.
- **FR-007**: The system MUST include explicit radon verification commands for both `MistHelper.py` and extracted module paths, and execution evidence MUST be captured in implementation notes or PR validation artifacts.
- **FR-008**: The system MUST include and pass quality gates: syntax validation (`py_compile`), lint (`ruff`), formatting (`black`), targeted parity tests, and broader regression evidence.
- **FR-009**: The system MUST include explicit operational safety controls in scope, including preservation of confirmation gates, safe early returns on invalid confirmation/input paths, and equivalent error handling semantics.
- **FR-010**: Every AI-generated or modified executable line in touched blocks MUST include meaningful inline comments explaining intent (why), not just action (what).
- **FR-011**: Action logging MUST be present around key operations in touched blocks, with pre-action and post-action observability messages and equivalent error-context logging for failures.
- **FR-012**: The system MUST maintain backward compatibility for existing menu entry points and invocation patterns used by operators and automated runs.
- **FR-013**: The system MUST provide a clear mapping from each original function to its extracted modules/classes and associated tests.
- **FR-014**: The system MUST provide regression comparison evidence demonstrating behavior parity before and after refactor for all five targets.

### Required Verification Commands

- **VC-001 (Complexity Baseline/Result for monolith file)**: `python -m radon.complexity MistHelper.py -s -a`
- **VC-002 (Complexity for extracted modules under src)**: `python -m radon.complexity src -s -a`
- **VC-003 (Syntax gate)**: `python -m py_compile MistHelper.py`
- **VC-004 (Lint gate)**: `python -m ruff check MistHelper.py src`
- **VC-005 (Format gate)**: `python -m black --check MistHelper.py src`
- **VC-006 (Targeted parity tests)**: Execute targeted tests for all five decomposed workflows (unit + integration).
- **VC-007 (Broader regression evidence)**: Execute broader project regression evidence run (existing suite/flows relevant to touched areas) and record pass status.

### Key Entities *(include if feature involves data)*

- **Target Function Refactor Unit**: Represents one of the five designated high-complexity functions, including baseline complexity, extracted components, and parity criteria.
- **Extracted Module Component**: Represents a new semantic class/module under `src/` with explicit responsibility boundaries and associated tests.
- **Parity Evidence Record**: Represents proof artifacts for behavior equivalence (prompt/output/side-effect parity), complexity validation, and quality-gate results.
- **Operational Safety Control**: Represents guardrails that must remain intact (confirmations, safe exits, retry/failure handling, logging coverage).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All five target functions are measured at cyclomatic complexity `<=10`.
- **SC-002**: 100% of specified quality gates (VC-001 through VC-007) complete successfully with recorded evidence.
- **SC-003**: Parity test coverage exists for all five target workflows, and all parity tests pass.
- **SC-004**: No user-visible regressions are found in prompts, outputs, or side effects for targeted workflows during validation.
- **SC-005**: Operational safety controls for touched workflows remain intact with zero unintended bypass of confirmations or safety checks.
- **SC-006**: Reviewers can trace each original target function to extracted modules/classes and corresponding tests without ambiguity.

## Assumptions

- Existing behavior of the five target workflows in the current `main` branch is the parity baseline.
- Extracted modules/sub-modules will be placed under existing `src/` domains consistent with current project organization.
- Test harness and fixtures required for parity and integration validation are available or can be extended without changing product behavior.
- Broader regression evidence may use existing project test commands plus targeted execution focused on touched components.
- Refactor scope excludes introducing new operator features; this is decomposition and maintainability work only.
- Any unavoidable behavior discrepancy discovered during refactor is treated as a defect and fixed before completion.
