# Tasks: Preserve API Usage After Failed Refresh

**Input**: [spec.md](spec.md), [plan.md](plan.md), and the documents under `design/`.

**Organization**: Tasks follow User Story 1. This change has no project setup or shared foundational work.

## Phase 1: Setup

No project initialization is required.

## Phase 2: Foundational

No shared infrastructure is required.

## Phase 3: User Story 1 - Keep rate limiting based on valid usage data (Priority: P1)

**Goal**: Preserve the last accepted usage state after an unsuccessful refresh and retain current behavior after a successful refresh.

**Independent Test**: Run the focused rate-limit tests with native 4xx, 5xx, and successful SDK responses. Confirm failures preserve every cache field and log a warning without network access.

### Tests for User Story 1

- [X] T001 [US1] Add native SDK response tests for unsuccessful 4xx and 5xx statuses, successful refresh, full cache preservation, and failure logging in `tests/unit/test_rate_limiting.py`. (delivered: tests/unit/test_rate_limiting.py)

### Implementation for User Story 1

- [X] T002 [US1] Validate the Mist SDK response status before reading usage data and preserve the cache on unsuccessful responses in `src/foundation/support/utils/rate_limiting.py`. (delivered: src/foundation/support/utils/rate_limiting.py)
- [X] T003 [P] [US1] Add the issue release note in `changelog.d/issue-4611-rate-limit-refresh-http-status.md`. (delivered: changelog.d/issue-4611-rate-limit-refresh-http-status.md)

**Checkpoint**: The independent test passes for unsuccessful and successful native SDK responses without a live Mist request.

## Phase 4: Polish & Cross-Cutting Concerns

- [X] T004 Run focused tests in `tests/unit/test_rate_limiting.py` and applicable Ruff, Black, mypy, complexity, Bandit, STE, process-folder, and test-quality checks for `src/foundation/support/utils/rate_limiting.py`, `tests/unit/test_rate_limiting.py`, `changelog.d/issue-4611-rate-limit-refresh-http-status.md`, and `specs/numbered/0/0/1/2/1/4/2/1/4611-rate-limit-refresh/`. Record exact results. (delivered: tests/unit/test_rate_limiting.py)

## Dependencies & Execution Order

### Phase Dependencies

- Setup and foundational phases require no changes.
- User Story 1 can begin immediately.
- Polish depends on the User Story 1 tests, implementation, and release note.

### User Story Dependencies

- User Story 1 has no dependencies on another story.

### Within User Story 1

- T001 must fail against the current implementation before T002 changes production behavior.
- T002 depends on T001.
- T003 can run in parallel with T001 and T002 because it changes a separate file.
- T004 depends on T001, T002, and T003.

### Parallel Opportunities

- T003 can run in parallel with the test and implementation tasks.
- T001 and T002 must remain ordered because the tests must demonstrate the defect before the fix.

## Parallel Example: User Story 1

```text
Task: Add the issue release note in changelog.d/issue-4611-rate-limit-refresh-http-status.md
```

## Implementation Strategy

### MVP First

1. Add native response tests and confirm they fail against the current implementation.
2. Check response status before reading usage data.
3. Run the independent test and the applicable local checks.
4. Add and validate the issue release note.

### Incremental Delivery

Deliver the single user story as one scoped change. Do not split it into multiple pull requests.
