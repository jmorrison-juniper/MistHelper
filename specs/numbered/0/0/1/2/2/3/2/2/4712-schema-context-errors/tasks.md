# Tasks: Schema context errors

## Phase 1 - Setup

- [x] T001 Check live ownership and clean status for the reserved source and test paths.
- [x] T002 Restore `.venv` with the offline locked dependency set.

## Phase 2 - Foundational

- [x] T003 Specify the issue under `specs/numbered/0/0/1/2/2/3/2/2/4712-schema-context-errors/spec.md`.

## Phase 3 - User Story 1

- [x] T004 [US1] Add failure and strategy tests in `tests/unit/config/foundation/persistence/storage/db/test_database_schema_context_errors.py`.
- [x] T005 [US1] Remove the broad handler in `src/foundation/persistence/db/database_schema_utils.py`.

## Phase 4 - User Story 2

- [x] T006 [US2] Verify names, absence, and cleanup in `tests/unit/config/foundation/persistence/storage/db/test_database_schema_context_errors.py`.

## Phase 5 - Delivery

- [x] T007 Add `changelog.d/issue-4712-schema-context-errors.md` and record exact local results.
- [x] T008 Commit the reserved paths and export committed source and test files with SHA-256 values.
- [x] T009 [US1] Update the handed-off expectation in `tests/unit/db/test_database_schema_utils.py` without other test changes.

## Dependencies and Execution

T001 through T003 precede T004.
T004 precedes T005 so the regression can fail before the repair.
T005 precedes T006.
T007 and T008 follow verification.
Run this small repair serially to preserve the file reservation.
