# Tasks: Terminal Session Replay Isolation

## Phase 1: Setup

- [x] T001 Check the clean worktree, current main, issue ownership, and `tests/e2e/websockets_tab/test_websockets_terminal.py`.
- [x] T002 Resolve the managed specification path with `.specify/scripts/powershell/create-new-feature.ps1`.

## Phase 2: Evidence

- [x] T003 Run the original focused test and full shard in `tests/e2e/websockets_tab/`.
- [x] T004 Decode the failed CI replay and record the controlled visibility experiment in `design/research.md`.

## Phase 3: User Story 1

**Goal**: Preserve replay and paste isolation when the native renderer pauses outside the viewport.

**Independent test**: Run the existing journey in normal and controlled visibility cases.

- [x] T005 [US1] Add the controlled visibility case in `tests/e2e/websockets_tab/test_websockets_terminal.py` and record its failure.
- [x] T006 [US1] Require viewport visibility before rendered replay text in `tests/e2e/websockets_tab/test_websockets_terminal.py`.
- [x] T007 [US1] Run the focused regression and complete `tests/e2e/websockets_tab/` shard without retries.

## Phase 4: Publication

- [x] T008 Add `changelog.d/issue-4508-terminal-replay-visibility.md` and run applicable local gates.
- [x] T009 Analyze `spec.md`, `plan.md`, and `tasks.md`, then prepare the scoped commit.

Publication status belongs to the GitHub issue, not this implementation checklist.
After the scoped commit, run the repository test-quality ratchet before the push.
Publish one PR for #4508 and inspect its exact-head checks.
Record the serial handoff on #4583.

## Dependencies

T001 precedes T002 and T003.
T004 requires T003.
T005 requires T002 and T004.
T006 requires the failing T005 control.
T007 requires T006.
T008 requires T007.
T009 requires T008.
Publication requires T009 and a passing committed test-quality ratchet.

## Parallel Execution

No implementation task runs in parallel with another implementation.
Independent lint and documentation checks can run together after T007.

## Implementation Strategy

Use one test-only repair and one issue-specific PR.
Do not change the production renderer or timeout.
Do not merge, enable auto-merge, or retry a held CI run.
