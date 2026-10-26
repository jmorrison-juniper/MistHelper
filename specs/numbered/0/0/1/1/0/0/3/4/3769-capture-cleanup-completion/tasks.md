# Tasks: Capture cleanup completion

**Input**: [Specification](spec.md), [plan](plan.md), and supporting records under `design/`.

## Phase 1: Setup

- [x] T001 Resolve the managed route and prepare `spec.md` and `plan.md`. (delivered: spec.md, plan.md)

## Phase 2: Foundational proof

- [x] T002 Prove four cleanup-order failures in `tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py`. (delivered: tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py)

## Phase 3: User Story 1 - Report stop after cleanup

**Goal**: No terminal result occurs while matching capture cleanup remains blocked.

**Independent test**: Run the four deterministic barrier cases.

- [x] T003 [US1] Defer terminal notification in `src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py`. (delivered: src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py)
- [x] T004 [US1] Verify matching and different capture identities in `tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py`. (delivered: tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py)

## Phase 4: User Story 2 - Report cleanup failure

**Goal**: A cleanup exception produces an explicit failed result and error log.

**Independent test**: Inject stream-close, capture-read, and capture-delete exceptions.

- [x] T005 [US2] Add cleanup-failure classification in `src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py`. (delivered: src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py)
- [x] T006 [US2] Cover cleanup failures and existing outcome classifications in `tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py`. (delivered: tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py)

## Phase 5: Final verification

- [x] T007 Add `changelog.d/issue-3769-capture-cleanup-completion.md` and run the applicable local gates. (delivered: changelog.d/issue-3769-capture-cleanup-completion.md)
- [x] T008 Compare `spec.md`, `plan.md`, and `tasks.md` in `analysis.md`. (delivered: analysis.md)

## Dependencies

T001 precedes T002. T002 precedes production changes.
T003 precedes T004. T005 precedes T006.
T004 and T006 precede T007. T007 precedes T008.

## Parallel execution

Both stories change the same production class and regression module, so execute them sequentially.
Independent read-only gates can run in parallel after the implementation.

## Implementation strategy

Establish the failure first.
Apply the smallest lifecycle repair.
Preserve the unchanged live utility suite as integration evidence.
Publish one verified repair without merge or auto-merge.
