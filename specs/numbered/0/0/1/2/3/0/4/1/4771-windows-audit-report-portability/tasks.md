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
- [X] T011 [US1] Open staged files with ACL and attribute access through a no-follow Windows handle, and add API-boundary and native-Windows tests in `tests/e2e/websockets_tab/dialog_audit/test_inventory.py`.

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

## Phase 5: User Story 4 - Validate report safety on native Windows (Priority: P1)

**Goal**: Run the real Windows helper and writer tests before merge without changing required CI.

**Independent Test**: Push a feature branch commit that changes a listed test input and confirm that two native tests pass with zero skips.

### Tests for User Story 4

- [X] T012 [US1] Add a native full-writer regression with synthetic evidence in `tests/e2e/websockets_tab/dialog_audit/test_inventory.py`.
- [X] T013 [US4] Add a workflow guard for the path filter, runner, permissions, timeout, and zero-skip behavior in `tests/guardrails/test_ci_gate_triggers.py`.

### Implementation for User Story 4

- [X] T014 [US4] Add a separate optional Windows workflow with a narrow path filter in `.github/workflows/windows-audit-report.yml`.

**Checkpoint**: The workflow must run both real Windows regressions and fail if either test skips.

---

## Phase 6: Polish and Validation

- [X] T007 Add the issue release fragment in `changelog.d/issue-4771-windows-audit-report-portability.md`.
- [X] T008 Run the focused regression, applicable lint and format checks, and offline synthetic smoke. Record exact outcomes in the handoff.
- [X] T009 Restore the prior `.specify/feature.json` content, verify the routed record, and commit the completed local change.
- [ ] T010 Run both native regressions through the branch-push workflow. Leave this task open until the Windows job reports two passed tests and zero skips.
- [X] T015 Update the native Windows workflow path in the #4771 records and release fragment.
- [ ] T016 Run the focused regression, workflow contract, applicable quality gates, and offline synthetic smoke. Record exact outcomes in the handoff.
- [ ] T017 Commit the reviewed local changes with a Conventional Commit subject and the required co-author trailer.

## Dependencies and Execution Order

### Phase Dependencies

- Setup has no work.
- US1 follows its failing regression test.
- US2 follows US1 because both stories use the Windows file-access helper.
- US3 follows US1 because rollback applies to staged Windows and POSIX writes.
- Polish depends on the story work and focused validation.
- Native Windows validation requires a Windows host.

### User Story Dependencies

- **US1 (P1)**: T001 and T002 deliver Windows report output. T011 follows T002 because it corrects the file handle used for DACL changes.
- **US2 (P1)**: T003 and T004 verify fail-closed path safety.
- **US3 (P2)**: T005 and T006 verify rollback and cleanup after report failures.
- **US4 (P1)**: T012 and T013 add native writer and workflow contract tests. T014 adds the separate workflow after those tests exist. T010 remains open until the branch-push run passes.

### Parallel Opportunities

- T002, T004, and T006 use the same test file, so add them in sequence.
- T012 and T013 use different files and can proceed independently.
- US1 and US2 implementation can proceed independently only after the shared helper is stable.
- US3 follows US1 because it changes the report replacement lifecycle.

### Sequential Example: User Story 1

```text
First add and run T001 in tests/e2e/websockets_tab/dialog_audit/test_inventory.py.
Then implement T002 in tests/e2e/websockets_tab/dialog_audit/support/reporting.py.
Then add T011 native handle coverage in tests/e2e/websockets_tab/dialog_audit/test_inventory.py.
```

## Implementation Strategy

1. Add and run T001 before implementation.
2. Deliver US1 and verify the synthetic Windows path.
3. Deliver US2 and verify fail-closed path checks.
4. Deliver US3 and verify rollback and cleanup.
5. Run local validation and commit. Keep T010 open until the native workflow reports success.
