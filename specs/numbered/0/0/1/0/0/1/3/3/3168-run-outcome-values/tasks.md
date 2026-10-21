# Tasks: Explicit Portal Run Outcomes

**Input**: [spec.md](spec.md), [plan.md](plan.md), and design artifacts under `design/`.

## Phase 1: Setup

- [X] T001 Confirm the explicit handler result contract in `design/contracts/handler-outcome.md` and the existing `OperationOutcome` fields in `src/foundation/models/operation_outcome.py`.

## Phase 2: Foundational

- [X] T002 Add a handler outcome slot to portal run records in `web_portal/services/operation.py`.

## Phase 3: User Story 1 - Report empty results

**Goal**: A handler-returned outcome controls completion without a matching log marker.

**Independent Test**: Run the alert digest menu handler with a `no_output` value and verify the run completes with its reason.

- [X] T003 [US1] Add a portal executor test using the alert digest handler and a no-output outcome in `tests/unit/web_portal/test_portal_silent_completion.py`.
- [X] T004 [US1] Capture the handler return value and apply every `OperationOutcome` state in `web_portal/services/operation.py`.
- [X] T005 [US1] Verify typed empty-result, completed, failed, and missing-input outcomes in `tests/unit/web_portal/test_portal_silent_completion.py`.
- [X] T006 [US1] Verify the explicit result through the Flask status route in `tests/e2e/web_portal/test_issue_4037_menu_93_output.py`.

## Phase 4: User Story 2 - Keep legacy handlers safe

**Goal**: Handlers without an `OperationOutcome` keep the current marker and file checks.

**Independent Test**: Run an unmigrated handler with a recognized no-data marker and verify completion plus a cumulative fallback log count.

- [X] T007 [US2] Add tests for the unchanged legacy marker path and its cumulative fallback log count in `tests/unit/web_portal/test_portal_silent_completion.py`.
- [X] T008 [US2] Increment and log a lock-protected legacy marker fallback count in `web_portal/services/operation.py`.
- [X] T009 [US2] Verify that an unmigrated handler with no file or marker still fails in `tests/unit/web_portal/test_portal_silent_completion.py`.
- [X] T010 [US2] Verify the legacy marker list against current handler wording in `tests/unit/web_portal/test_portal_silent_completion.py`.

## Phase 5: User Story 3 - Ignore prose changes for migrated handlers

**Goal**: A migrated handler's returned outcome remains authoritative when its log wording changes.

**Independent Test**: Reword the alert digest log message and verify the run still completes with the returned outcome.

- [X] T011 [US3] Add a reworded-log regression test for the migrated alert digest handler in `tests/unit/web_portal/test_portal_silent_completion.py`.

## Phase 6: Polish

- [X] T012 Add the issue release note to `changelog.d/issue-3168-explicit-handler-outcomes.md`.
- [X] T013 Run the portal unit and Flask-client tests, lint, format, compile, type, and Markdown checks listed in `design/quickstart.md`.
- [X] T014 Run the read-only artifact analysis for `spec.md`, `plan.md`, and `tasks.md`.

## Dependencies

```text
                         T001 -> T002 -> T003 -> T004 -> T005, T006
                                                  T004 -> T007 -> T008 -> T009, T010
                                                  T004 -> T011
                         T005, T006, T008, T009, T010, T011 -> T012 -> T013 -> T014
```

Each story depends on the foundational run-record field and typed-outcome path. No implementation tasks can run in parallel because they edit the same service and test files.

## Parallel Execution

No implementation task can run in parallel without touching a file another task edits. Run the story tests in order, then complete validation.

## Implementation Strategy

Complete User Story 1 first to establish value-based outcome handling. Complete User Story 2 next to preserve and measure the legacy path. Complete User Story 3 to prove log prose no longer controls migrated run state. The legacy wording test protects the current marker-to-handler contract.
