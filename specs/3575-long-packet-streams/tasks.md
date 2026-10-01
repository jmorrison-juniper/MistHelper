# Tasks: Long packet streams

**Input**: [spec.md](spec.md) and [plan.md](plan.md).

**Prerequisites**: The live issue claim, exact reservation, and current SDK research.

**Tests**: The user requires red and green evidence with local controlled fixtures.

## Phase 1: Setup

- [x] T001 Verify ownership and the exact file reservation for `specs/3575-long-packet-streams/spec.md`. (delivered: specs/3575-long-packet-streams/spec.md)
- [x] T002 Restore the missing test dependencies through `scripts/bootstrap_worktree.py`. (delivered: .venv/bin/python)
- [x] T003 Complete the current SpecKit templates under `specs/3575-long-packet-streams/`. (delivered: specs/3575-long-packet-streams/plan.md)

## Phase 2: Foundational

- [x] T004 Build controlled SDK and clock fixtures in `tests/unit/websocket_streams/live/captures/support/sdk.py`. (delivered: tests/unit/websocket_streams/live/captures/support/sdk.py)
- [x] T005 Prove the old 60-second cutoff and start-before-subscribe order in `tests/unit/websocket_streams/live/captures/test_packet_order.py`. (delivered: tests/unit/websocket_streams/live/captures/test_packet_order.py)
- [x] T006 Define checked capture plans and shared events in `src/websocket_streams/live/captures/model.py`. (delivered: src/websocket_streams/live/captures/model.py)

## Phase 3: User Story 1 - Choose the capture duration

**Goal**: Receive records throughout the selected interval.

**Independent Test**: Deliver records at 59, 61, 119, and 3599 seconds.

- [x] T007 [US1] Test duration boundaries and invalid values in `tests/unit/websocket_streams/live/captures/test_packet_duration.py`. (delivered: tests/unit/websocket_streams/live/captures/test_packet_duration.py)
- [x] T008 [US1] Add duration fields and accurate text in `src/websocket_streams/catalog/utilities.py` and `src/websocket_streams/catalog/utility_text.py`. (delivered: src/websocket_streams/catalog/utilities.py)
- [x] T009 [US1] Refuse unsafe integer text in `src/websocket_streams/intake/fields.py`. (delivered: src/websocket_streams/intake/fields.py)
- [x] T010 [US1] Select the capture runner and preserve the full interval in `src/websocket_streams/live/sessions/manager.py`. (delivered: src/websocket_streams/live/sessions/manager.py)
- [x] T011 [US1] Update capture limits in `src/websocket_streams/live/sessions/settings.py` and `tests/unit/websocket_streams/live/sessions/test_ws_stream_settings.py`. (delivered: src/websocket_streams/live/sessions/settings.py)
- [x] T012 [US1] Validate the browser duration in `src/websocket_streams/web/static/websockets.js`. (delivered: src/websocket_streams/web/static/websockets.js)

## Phase 4: User Story 2 - Receive the first packet records

**Goal**: Confirm the exact subscription before one capture start.

**Independent Test**: Delay confirmation and deliver records before the start response.

- [x] T013 [US2] Build scope-checked SDK payloads in `src/websocket_streams/live/captures/control.py`. (delivered: src/websocket_streams/live/captures/control.py)
- [x] T014 [US2] Implement bounded events and SDK connection ownership in `src/websocket_streams/live/captures/transport.py`. (delivered: src/websocket_streams/live/captures/transport.py)
- [x] T015 [US2] Implement the subscription-first worker in `src/websocket_streams/live/captures/runner/driver.py` and `src/websocket_streams/live/captures/runner/lifecycle.py`. (delivered: src/websocket_streams/live/captures/runner/lifecycle.py)
- [x] T016 [US2] Prove ordering, first records, and correlation in `tests/unit/websocket_streams/live/captures/test_packet_order.py`. (delivered: tests/unit/websocket_streams/live/captures/test_packet_order.py)
- [x] T017 [US2] Prove a real short local stream in `tests/unit/websocket_streams/live/captures/support/local_stream.py`. (delivered: tests/unit/websocket_streams/live/captures/support/local_stream.py)

## Phase 5: User Story 3 - Stop and release the capture

**Goal**: Confirm the matching cloud stop and release owned resources.

**Independent Test**: Stop through the existing controller and count SDK actions and resources.

- [x] T018 [US3] Implement active identity and stop response checks in `src/websocket_streams/live/captures/control.py`. (delivered: src/websocket_streams/live/captures/control.py)
- [x] T019 [US3] Prove stop, refusal, timeout, disconnect, and cleanup in `tests/unit/websocket_streams/live/captures/test_packet_stop.py`. (delivered: tests/unit/websocket_streams/live/captures/test_packet_stop.py)
- [x] T020 [US3] Prove the real route contract in `tests/contract/websocket_streams/test_long_packet_streams.py`. (delivered: tests/contract/websocket_streams/test_long_packet_streams.py)
- [x] T021 [US3] Prove duration, card updates, and cloud stop in Chromium in `tests/e2e/websocket_streams/test_long_packet_streams.py`. (delivered: tests/e2e/websocket_streams/test_long_packet_streams.py)

## Phase 6: Cross-Cutting Checks

- [x] T022 Verify request permissions, resource limits, and unchanged adjacent WebSockets behavior in `tests/unit/websocket_streams/`. (delivered: tests/unit/websocket_streams/live/captures/test_packet_stop.py)
- [x] T023 Add the unique release note in `changelog.d/issue-3575-long-packet-streams.md`. (delivered: changelog.d/issue-3575-long-packet-streams.md)
- [x] T024 Run coverage, local quality commands, and specification consistency for `src/websocket_streams/` and `specs/3575-long-packet-streams/`. (delivered: specs/3575-long-packet-streams/plan.md)
- [x] T025 Prepare the local commands and publication condition in `specs/3575-long-packet-streams/design/quickstart.md`. (delivered: specs/3575-long-packet-streams/design/quickstart.md)

## Dependencies

T004 and T005 precede source implementation.
T006 precedes T010, T013, T014, and T015.
T007 precedes duration implementation.
T013 through T015 precede the stop, route, and browser proofs.
The verified local checks precede the local commit.
The post-commit ratchet precedes any authorized publication.

## Parallel Execution

The unit, route, and browser checks can run independently after implementation.
Source edits remain sequential because the runner classes share state contracts.
No separate agent or shared specification commit is needed.

## Implementation Strategy

Prove the current defects first.
Complete all three user stories in one local change.
Keep publication outside the local task until the parent grants it.
