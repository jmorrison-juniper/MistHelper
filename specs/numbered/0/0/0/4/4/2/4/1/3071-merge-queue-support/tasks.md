# Tasks: Protected merge queue validation

**Input**: [Specification](spec.md), [plan](plan.md), and the supporting artifacts under `design/`.

**Tests**: Required by FR-006. Synthetic mutations must prove rejection.

## Phase 1: Setup

- [x] T001 Confirm file ownership and the trigger-only handover for `.github/workflows/ci.yml`. (delivered: plan.md)
- [x] T002 Restore missing worktree dependencies and run the existing `tests/guardrails/test_ci_gate_triggers.py` selection. (delivered: design/research.md)

## Phase 2: Foundational

- [x] T003 Inspect event-dependent checkout and shared workflow behavior for `.github/workflows/ci.yml` and `.github/workflows/codeql.yml`. (delivered: design/contracts/workflows.md)

## Phase 3: User Story 1 - Validate the candidate

**Goal**: Both required-check workflows accept queue requests with stable context names.

**Independent Test**: Run the trigger and context contracts against both live YAML files and synthetic mutations.

- [x] T004 [US1] Add queue-trigger and required-name mutation tests to `tests/guardrails/test_ci_gate_triggers.py`. (delivered: tests/guardrails/test_ci_gate_triggers.py)
- [x] T005 [US1] Add `merge_group.checks_requested` to `.github/workflows/ci.yml` and `.github/workflows/codeql.yml`. (delivered: .github/workflows/ci.yml, .github/workflows/codeql.yml)

## Phase 4: User Story 2 - Preserve existing checks

**Goal**: Preserve existing events and protect candidate and main runs from cancellation.

**Independent Test**: Exercise pull request, main, and queue contexts with distinct references.

- [x] T006 [US2] Add cancellation, checkout, and malformed-input contracts to `tests/guardrails/test_ci_gate_triggers.py`. (delivered: tests/guardrails/test_ci_gate_triggers.py)
- [x] T007 [US2] Limit cancellation to pull requests in `.github/workflows/codeql.yml`. (delivered: .github/workflows/codeql.yml)

## Phase 5: User Story 3 - Separate activation

**Goal**: Document the owner boundary without claiming operational acceptance.

**Independent Test**: Review the rollout against FR-007 through FR-010 and confirm the settings diff is empty.

- [x] T008 [P] [US3] Document preparation, owner activation, evidence, recovery, and the instruction-path exception in `documentation/quality-gates.md`. (delivered: documentation/quality-gates.md)
- [x] T009 [P] [US3] Add `changelog.d/issue-3071-merge-queue-support.md` without changing the shared changelog. (delivered: changelog.d/issue-3071-merge-queue-support.md)

## Phase 6: Validation and Review

- [x] T010 Run applicable local gates and record actual results in `analysis.md`. (delivered: analysis.md)
- [ ] T011 Commit explicit paths and run the documented full-scope ratchet from `.github/copilot-instructions.md`.
- [ ] T012 Create a template-based pull request and request coordinator review with exact results from `analysis.md`.

## Phase 7: Owner-Controlled Acceptance

- [ ] T013 [US3] After separate owner activation, record two protected queued merges on #3071 using `documentation/quality-gates.md`. Blocked on owner approval and queue activation.

## Dependencies & Execution Order

T001 and T002 precede T003. T003 precedes both workflow stories.
T004 precedes T005. T006 precedes T007.
T008 and T009 can proceed independently after T003.
T010 requires T004 through T009.
T011 follows local validation. T012 follows the committed ratchet.
T013 follows coordinator review, preparation merge, and owner activation.

## Parallel Examples

US1 YAML changes and US2 test preparation share the guard, so one worker owns them.
US3 documentation and the release fragment can proceed independently in different files.
No parallel worker receives the reserved `ci.yml` sections.

## Implementation Strategy

Deliver workflow preparation as one bounded pull request.
Retain the serialized merge process until the owner verifies queue operation.
Do not mark T013 complete from local validation or a successful preparation merge.
