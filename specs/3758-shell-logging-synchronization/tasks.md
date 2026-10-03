# Tasks: Shell Logging Synchronization

**Input**: Design documents from `specs/3758-shell-logging-synchronization/`

**Prerequisites**: `plan.md` and `spec.md`

**Tests**: Required by the specification.

**Organization**: Tasks follow user-story priority. The repair changes only two test modules.

## Phase 1: Setup

**Purpose**: Confirm the approved scope and preserve the known red result.

- [x] T001 Preserve the original failed result: 369 unique tests, 368 passed, one failed, zero skipped, zero errors, and 27.57 seconds. (delivered: specs/3758-shell-logging-synchronization/spec.md)

## Phase 2: Foundational

**Purpose**: Reuse the existing pytest fixtures and structured logger. No new infrastructure is required.

## Phase 3: User Story 1 - Capture the complete shell log (Priority: P1)

**Goal**: Take the log snapshot only after the exact terminal event reaches the real `caplog` binding.

**Independent Test**: Run the affected test and confirm the event appears before the snapshot. Preserve all original snapshot assertions and inputs.

### Implementation for User Story 1

- [x] T002 [US1] Add the exact-event helper with the existing two-second bound and 0.01-second polling. (delivered: tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py)
- [x] T003 [US1] Call the helper after STOPPED and before the snapshot. All nine original assertions and the original function AST remain unchanged except this call. (delivered: tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py)

## Phase 4: User Story 2 - Reject incomplete or unrelated logs (Priority: P2)

**Goal**: Prove that the actual helper accepts only the exact event from the exact logger.

**Independent Test**: Run deterministic controls for an event present before polling, an event delivered during polling, an absent event, a wrong event, and a wrong logger.

### Tests for User Story 2

- [x] T004 [P] [US2] Create deterministic controls with real structured logger delivery and a local clock. No global time, logger, capture, or fixture mutation occurs. (delivered: tests/unit/websocket_streams/live/runners/test_ws_shell_log_completion_3758.py)
- [x] T005 [US2] Run all five controls. Immediate and polled delivery pass. Missing, wrong-event, and wrong-logger controls refuse at exactly two controlled seconds. (delivered: tests/unit/websocket_streams/live/runners/test_ws_shell_log_completion_3758.py)

## Phase 5: Polish and Cross-Cutting Validation

**Purpose**: Prove the native repair, run targeted gates, and prepare a private offline handoff.

- [x] T006 Run the original native scope separately: 369 passed. Run the combined scope: 374 passed, including five new controls. Compare all membership IDs. (delivered: tests/unit/websocket_streams/live/runners/test_ws_shell_log_completion_3758.py)
- [x] T007 [P] Run Ruff on both changed modules: passed. (delivered: tests/unit/websocket_streams/live/runners/test_ws_shell_log_completion_3758.py)
- [x] T008 [P] Run Black on both changed modules: passed. (delivered: tests/unit/websocket_streams/live/runners/test_ws_shell_log_completion_3758.py)
- [x] T009 [P] Run scoped mypy: FAILED with the unchanged fixture error. Exact base fails identically. Configured CI scope passes. Issue #3760 tracks the separate error. (delivered: specs/3758-shell-logging-synchronization/plan.md)
- [x] T010 [P] Run Bandit. Configured scan excludes tests and proves nothing about these modules. Final direct scan checks 524 lines and reports 66 intentional B101 test assertions only. Retain FAILED, without suppression. (delivered: specs/3758-shell-logging-synchronization/plan.md)
- [x] T011 [P] Run pydocstyle and interrogate: passed. Measured 46 documented items with 100% docstring coverage. (delivered: tests/unit/websocket_streams/live/runners/test_ws_shell_log_completion_3758.py)
- [x] T012 [US1] Prepare the private offline draft under the CLI session artifact directory, `files/shell-sync/pr-draft.md`. Preserve all 23 template items and original failure evidence. (delivered: specs/3758-shell-logging-synchronization/plan.md)
- [ ] T013 Create one local commit with the two test modules and three SpecKit artifacts. The parent permits unchanged out-of-scope failures for this preservation commit. Do not push. Record completion in the private receipt without another source commit.
- [ ] T014 Run the required input preflight and committed-scope analyzer against `origin/main`, verified at `38d06c48aa01c553ff2fa4d16d819f82dd68dc94`. Include the two actual changed test modules without exclusions. Record completion in the private receipt.
- [ ] T015 Freeze the clean branch. Record the commit, tree, sole parent, paths, no upstream, and all limits in the private receipt. No publication grant exists. Record completion outside tracked files to keep exactly one commit.

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: T001 has no prerequisite.
- **Foundational**: No new foundation tasks are required.
- **User Story 1**: T002 follows T001. T003 follows T002.
- **User Story 2**: T004 follows T002 and can run beside T003. T005 follows T004.
- **Polish**: T006 follows T003 and T005. T007 through T011 can run in parallel after T003 and T004. T012 follows T006 and T007 through T011. T013 follows T012 and the parent preservation grant. T014 follows T013. T015 follows T014.

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on T001. This story is the MVP.
- **User Story 2 (P2)**: Depends on the helper from T002. It does not depend on the snapshot integration in T003.

## Parallel Opportunities

- T003 and T004 can proceed in parallel after T002 because they change different files.
- T007 through T011 can run in parallel after both story changes are complete. Each check reads the same two files and uses a separate tool.

## Implementation Strategy

1. Preserve the recorded pre-change red result in the offline handoff.
2. Add the exact-event helper and integrate it before the snapshot.
3. Add deterministic helper controls and prove immediate delivery, polled delivery, and bounded refusal.
4. Run the exact 369 original node IDs with the new controls. Require a green result.
5. Run the targeted gates, prepare the offline PR draft, and create one local commit.
6. Run the committed-scope test-quality gate. Record T013 through T015 completion in the private receipt. Freeze the branch without a push.

The MVP is User Story 1. Complete User Story 2 and all validation tasks before handoff.
