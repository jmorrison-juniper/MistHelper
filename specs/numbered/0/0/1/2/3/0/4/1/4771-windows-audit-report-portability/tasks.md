# Tasks: Windows Audit Report Portability

**Input**: Routed specification under `specs/numbered/0/0/1/2/3/0/4/1/4771-windows-audit-report-portability/`.

**Prerequisites**: `spec.md`, `plan.md`, `design/research.md`, `design/data-model.md`, and `design/quickstart.md`.

**Tests**: Required by the feature specification and repository constitution. Write focused regression tests before the matching implementation.

## Phase 1: Setup

No project setup is needed. The feature uses the existing Python environment and test modules.

## Phase 2: User Story 1 - Save a private audit report on Windows (Priority: P1)

**Goal**: Create the JSON and Markdown audit reports on Windows with owner-only access.

**Independent Test**: Simulate the Windows writer path with synthetic report data and verify both file contents and access-control calls.

### Tests for User Story 1

- [X] T001 [US1] Add synthetic Windows report creation and owner-only access tests in `tests/e2e/websockets_tab/dialog_audit/test_inventory.py`.

### Implementation for User Story 1

- [X] T002 [US1] Add Windows-safe directory and report file access in `tests/e2e/websockets_tab/dialog_audit/support/reporting.py`.

**Checkpoint**: Both report files can be created on the Windows path without POSIX-only flags.

## Phase 3: User Story 2 - Reject unsafe report paths (Priority: P1)

**Goal**: Reject symbolic links, reparse points, missing safety evidence, and ACL failures.

**Independent Test**: Inject symbolic links, reparse attributes, missing attributes, and ACL errors, then verify the writer rejects each case before changing prior report contents.

### Tests for User Story 2

- [X] T003 [US2] Add unsafe-path and fail-closed Windows tests in `tests/e2e/websockets_tab/dialog_audit/test_inventory.py`.

### Implementation for User Story 2

- [X] T004 [US2] Reject unsafe path components and fail when owner-only access cannot be enforced in `tests/e2e/websockets_tab/dialog_audit/support/reporting.py`.

**Checkpoint**: Every tested symbolic link or reparse point is rejected before report data changes.

## Phase 4: User Story 3 - Preserve report files after a failed write (Priority: P2)

**Goal**: Keep earlier report contents and remove staged files when a new write fails.

**Independent Test**: Inject a write or replace failure and compare prior report bytes and directory contents with their initial state.

### Tests for User Story 3

- [X] T005 [US3] Add failure and cleanup tests in `tests/e2e/websockets_tab/dialog_audit/test_inventory.py`.

### Implementation for User Story 3

- [X] T006 [US3] Stage both reports and roll back failed replacements in `tests/e2e/websockets_tab/dialog_audit/support/reporting.py`.

**Checkpoint**: A failed update preserves the earlier report pair and leaves no staging files.

## Phase 5: Polish and Validation

- [X] T007 Add the issue release fragment in `changelog.d/issue-4771-windows-audit-report-portability.md`.
- [X] T008 Run the focused regression, applicable lint and format checks, and offline synthetic smoke. Record exact outcomes in the handoff.
- [X] T009 Restore the prior `.specify/feature.json` content, verify the routed record, and commit the completed local change.
- [ ] T010 Run the focused writer test on native Windows. This task requires a Windows host and cannot be completed from the current macOS checkout.

## Dependencies and Execution Order

### Phase Dependencies

- Setup has no work.
- US1 follows its failing regression test.
- US2 follows US1 because both stories use the Windows file-access helper.
- US3 follows US1 because rollback applies to staged Windows and POSIX writes.
- Polish depends on the story work and focused validation.
- Native Windows validation requires a Windows host.

### User Story Dependencies

- **US1 (P1)**: T001 and T002 deliver successful Windows report output.
- **US2 (P1)**: T003 and T004 verify fail-closed path safety.
- **US3 (P2)**: T005 and T006 verify rollback and cleanup after report failures.

### Parallel Opportunities

- T002, T004, and T006 use the same test file, so add them in sequence.
- US1 and US2 implementation can proceed independently only after the shared helper is stable.
- US3 follows US1 because it changes the report replacement lifecycle.

### Parallel Example: User Story 1

```text
First add and run T002 in tests/e2e/websockets_tab/dialog_audit/test_inventory.py.
Then implement T003 in tests/e2e/websockets_tab/dialog_audit/support/reporting.py.
```

## Implementation Strategy

1. Add and run T001 before implementation.
2. Deliver US1 and verify the synthetic Windows path.
3. Deliver US2 and verify fail-closed path checks.
4. Deliver US3 and verify rollback and cleanup.
5. Run local validation and commit. Keep T010 open unless a native Windows host becomes available.
