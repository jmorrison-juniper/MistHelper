# Feature Specification: Decompose Top-5 Complex Functions

**Feature Branch**: `[195-decompose-top5-functions]`  
**Created**: 2026-06-01  
**Status**: Draft  
**Input**: User description: "Decompose and refactor the 5 highest-complexity functions in `MistHelper.py` into separate modules/sub-modules under `src/` while preserving behavior and menu compatibility."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preserve Menu and CLI Behavior During Decomposition (Priority: P1)

As a NOC engineer, I need existing menu options, CLI workflows, prompts, outputs, and side effects to remain unchanged after refactoring, so I can keep operating MistHelper safely without retraining or runbook updates.

**Why this priority**: Operational continuity is critical; behavior drift in core menu flows can create outages or operational confusion.

**Independent Test**: Execute each target function via its current menu/CLI entry path before and after the refactor and confirm parity for prompts, output fields, logging outcomes, and side effects.

**Acceptance Scenarios**:

1. **Given** the current menu path invokes `start_org_packet_capture`, **When** the refactor is completed, **Then** the same menu path, prompt sequence, and capture side effects remain unchanged.
2. **Given** a CLI or menu path invokes `with_wan_overrides` or `device_events_52w`, **When** the refactor is completed, **Then** returned datasets, formatting expectations, and user-visible behavior remain equivalent.

---

### User Story 2 - Reduce Complexity for Maintainability (Priority: P1)

As a maintainer, I need the five target functions decomposed into semantically named modules and classes so the codebase is easier to test, reason about, and extend safely.

**Why this priority**: The current complexity levels are high enough to increase regression risk and maintenance burden.

**Independent Test**: Run complexity analysis on refactored code and verify each target function (or equivalent responsibility boundary) is reduced to CC <= 10 with no thin-wrapper anti-pattern.

**Acceptance Scenarios**:

1. **Given** the baseline complexity report, **When** decomposition is complete, **Then** each target function area has CC <= 10 for retained entry-point methods.
2. **Given** extracted modules under `src/`, **When** reviewing architecture and call paths, **Then** extracted classes contain real business logic and are not pass-through wrappers.

---

### User Story 3 - Prove Behavioral Parity with Regression Coverage (Priority: P2)

As a release approver, I need parity-focused unit/regression tests and quality-gate evidence so I can approve the refactor with confidence.

**Why this priority**: Complexity reduction is only acceptable if behavior remains stable and verifiable.

**Independent Test**: Run targeted unit/regression tests plus quality gates, including explicit radon verification for `MistHelper.py` and extracted modules.

**Acceptance Scenarios**:

1. **Given** updated test suites, **When** tests are executed, **Then** all new/adjusted tests pass and validate parity for each target function.
2. **Given** explicit complexity verification commands, **When** they are executed, **Then** reports confirm required complexity thresholds.

### Edge Cases

- What happens when packet-capture orchestration is interrupted mid-loop during `_execute_site_capture_loop`?
- How does the system preserve behavior when dependencies checked by `_early_dependency_check` are partially available?
- How does the refactor prevent accidental behavior changes in WAN override flows where mixed valid/invalid site data is encountered?
- How does the refactor preserve long-range event export behavior for empty, large, or paginated event sets in `device_events_52w`?
- How are sensitive values protected in logs and outputs when capture and WAN workflows surface environment or network details?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST decompose the following target functions into semantically named modules/sub-modules under `src/` while preserving existing menu/CLI invocation paths: `start_org_packet_capture`, `_early_dependency_check`, `with_wan_overrides`, `device_events_52w`, `_execute_site_capture_loop`.
- **FR-002**: System MUST reduce complexity so each retained target entry-point function or method has cyclomatic complexity <= 10.
- **FR-003**: System MUST avoid thin-wrapper anti-patterns; extracted classes/modules MUST encapsulate meaningful logic, validation, and orchestration.
- **FR-004**: System MUST preserve current prompts, menus, CLI interactions, output schemas, and side effects for all five target workflows.
- **FR-005**: System MUST preserve backward-compatible behavior for existing automation that depends on current menu numbering and command flows.
- **FR-006**: System MUST add or update unit and regression tests to validate parity for each target workflow, including success paths and representative failure paths.
- **FR-007**: System MUST include explicit complexity verification commands for `MistHelper.py` and extracted `src/` modules in project documentation or verification notes.
- **FR-008**: System MUST pass defined quality gates for syntax, linting, formatting, and test execution after refactor completion.
- **FR-009**: System MUST include risk controls for sensitive operations in packet capture and WAN override workflows, including safe confirmations where applicable and clear operator-visible safeguards.
- **FR-010**: System MUST enforce logging/privacy constraints by preventing secret/token/password leakage and ensuring sensitive identifiers are redacted or minimized in logs.

### Function-Specific Acceptance Requirements

- **FR-011 (start_org_packet_capture)**: Refactor MUST preserve organization-level packet capture initiation behavior, prompts, and resulting capture control side effects while reducing complexity to <= 10.
- **FR-012 (_early_dependency_check)**: Refactor MUST preserve dependency validation outcomes and user guidance behavior while reducing complexity to <= 10.
- **FR-013 (with_wan_overrides)**: Refactor MUST preserve WAN override export/report behavior, including field-level compatibility and flow control, while reducing complexity to <= 10.
- **FR-014 (device_events_52w)**: Refactor MUST preserve 52-week device events retrieval/output behavior (including pagination/empty-data handling) while reducing complexity to <= 10.
- **FR-015 (_execute_site_capture_loop)**: Refactor MUST preserve loop execution semantics, retry/iteration behavior, and termination conditions while reducing complexity to <= 10.

### Global Acceptance Requirements

- **FR-016**: A single verification run MUST provide evidence that all five function targets satisfy complexity, parity, and regression requirements.
- **FR-017**: Refactor documentation MUST map old responsibility boundaries to new module/class responsibilities for maintainers.
- **FR-018**: No user-facing menu labels, menu IDs, or CLI entry semantics for affected operations may change.

### Quality Gates and Verification Commands

The feature MUST define and execute a verification workflow that includes all project quality gates and explicit complexity checks.

Required complexity verification commands:

- `python -m radon cc MistHelper.py -s -a`
- `python -m radon cc src -s -a`
- `python -m radon cc MistHelper.py src -s -a`

Required quality-gate command set:

- `python -m py_compile MistHelper.py`
- `python -m ruff check MistHelper.py src`
- `python -m black --check MistHelper.py src`
- Project parity/regression test command(s) covering all five targets

### Key Entities *(include if feature involves data)*

- **RefactorTargetFunction**: Represents one of the five high-complexity functions and its compatibility contract (entry path, prompts, outputs, side effects, complexity threshold).
- **CompatibilityContract**: Defines behavior invariants that must not change (menu IDs, prompts, output fields, side effects, error handling semantics).
- **VerificationEvidence**: Captures test and complexity outputs proving parity and maintainability goals were met.
- **RiskControlPolicy**: Defines guardrails for sensitive/destructive operations and privacy-preserving logging behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All five target functions achieve cyclomatic complexity <= 10 as confirmed by explicit complexity verification output.
- **SC-002**: 100% of targeted parity/regression tests for the five workflows pass in the same run used for release approval.
- **SC-003**: 0 unintended changes are detected in menu compatibility for affected operations (menu IDs, labels, and invocation semantics remain unchanged).
- **SC-004**: 0 critical regressions are found in prompts, output schemas, or documented side effects across the five workflows.
- **SC-005**: 100% of required quality gates complete successfully for refactored files.
- **SC-006**: Sensitive fields in logs for affected workflows are redacted or omitted per policy in 100% of validated test scenarios.

## Assumptions

- Existing menu numbering and user-facing operation semantics in `MistHelper.py` are authoritative and must remain unchanged.
- Refactoring may relocate logic into `src/` but must keep public behavior stable for operators and scripts.
- Existing test infrastructure can be extended to add parity/regression coverage for the five target functions.
- Complexity is measured using radon cyclomatic complexity analysis output from project-local command execution.
- Sensitive-operation safeguards and logging/privacy rules already defined in project standards remain in force and are extended to all newly extracted modules.
