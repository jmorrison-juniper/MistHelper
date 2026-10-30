# Tasks: Local close lifetime

**Input**: [Specification](spec.md), [plan](plan.md), and supporting documents in `design/`.

## Phase 1: Setup

- [x] T001 Confirm the isolated baseline and native failure in `design/research.md`. (delivered: design/research.md)

## Phase 2: Foundation

- [x] T002 Add a controlled portable lifetime regression in `tests/unit/websocket_streams/live/transport/runtime/lifetime/`. (delivered: tests/unit/websocket_streams/live/transport/runtime/lifetime/test_close_ownership.py, tests/unit/websocket_streams/live/transport/runtime/lifetime/test_close_edges.py)

## Phase 3: Stop an active terminal

**Story**: US1, priority P1.
**Independent test**: Close during active receive and require the existing terminal outcome within its original bound.

- [x] T003 [US1] Protect descriptor lifetime in `src/mist/realtime/websocket_streams/live/transport/runtime/reader/socket_runtime.py`. (delivered: src/mist/realtime/websocket_streams/live/transport/runtime/reader/socket_runtime.py)
- [x] T004 [US1] Share the runtime through `src/mist/realtime/websocket_streams/live/transport/runtime/reader/frame_reader.py`, `src/mist/realtime/websocket_streams/live/transport/shell_client.py`, and `src/mist/realtime/websocket_streams/live/transport/stream_client.py`. (delivered: src/mist/realtime/websocket_streams/live/transport/runtime/reader/frame_reader.py, src/mist/realtime/websocket_streams/live/transport/shell_client.py, src/mist/realtime/websocket_streams/live/transport/stream_client.py)
- [x] T005 [US1] Update explicit runtime construction in `tests/unit/websocket_streams/live/transport/runtime/test_frame_reader.py`. (delivered: tests/unit/websocket_streams/live/transport/runtime/test_frame_reader.py)
- [x] T006 [US1] Confirm the native reproduction and existing shell, screen, and event-stream tests. (delivered: analysis.md)

## Phase 4: Validation and documentation

- [x] T007 Add `changelog.d/issue-4510-local-close-lifetime.md` and record exact gate results in `analysis.md`. (delivered: changelog.d/issue-4510-local-close-lifetime.md, analysis.md)
- [x] T008 Check requirement coverage and preserve the local result in `analysis.md`. Do not publish or merge. (delivered: analysis.md)

## Dependencies

T001 precedes T002. T002 precedes T003. T003 precedes T004 and T005.
T004 and T005 precede T006. T006 precedes T007 and T008.

## Parallel Execution

T004 and T005 touch different files and can proceed after T003.
Execution remains serial in this isolated worktree.

## Implementation Strategy

Prove the portable failure first. Implement US1 as one bounded lifetime change.
Validate existing behavior before the local handover.
