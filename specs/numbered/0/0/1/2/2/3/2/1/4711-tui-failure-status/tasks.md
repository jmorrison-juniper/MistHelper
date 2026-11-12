# Tasks: TUI completion reporting

## Phase 1: Setup

- [x] T001 Confirm issue ownership and the reserved paths in `plan.md`.
- [x] T002 Restore the local environment from `uv.lock` without network access.

## Phase 2: Foundation

- [x] T003 Define completion outcomes in `design/contracts/reporting.md`.

## Phase 3: User Story 1

**Goal**: Report success only after normal completion.

**Independent test**: Simulate every outcome with sockets and DNS blocked.

- [x] T004 [US1] Reproduce the false success reports in `tests/unit/config/foundation/support/refactors/runtime/console/test_tui_launcher_failure_status.py`.
- [x] T005 [US1] Correct completion reporting in `src/foundation/support/refactors/tui_launcher.py`.
- [x] T006 [US1] Verify restoration, session failure, debug behavior, and repeated calls in `tests/unit/config/foundation/support/refactors/runtime/console/test_tui_launcher_failure_status.py`.

## Phase 4: Completion

- [x] T007 Add the release note in `changelog.d/issue-4711-tui-failure-status.md`.
- [x] T008 Record applicable local gate results and specification consistency in `analysis.md`.
- [x] T009 Commit the explicit file set and export committed source and tests to the session artifact directory.

## Dependencies

T001 and T002 precede T003.
T003 precedes T004.
T004 precedes T005.
T005 precedes T006.
T006 and T007 precede T008.
T008 precedes T009.

## Parallel Execution

T007 can proceed independently after T003 because it owns a separate file.
One agent handles this bounded repair to avoid overlapping changes.

## Implementation Strategy

Reproduce the error first.
Apply one production-file repair.
Verify all contract outcomes, then create the local commit and offline export.
