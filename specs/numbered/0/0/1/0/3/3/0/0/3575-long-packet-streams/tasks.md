# Tasks: Long packet capture

**Input**: [spec.md](spec.md), [plan.md](plan.md), and the supporting records
under [design/](design/).

**Prerequisites**: The current package layout, local fake Mist service, current
capture cleanup, and open pull request ownership were checked before edits.

**Tests**: Tests are required by the issue and the repository constitution.
Every test uses local fakes, mocks, or controlled clocks.

## Phase 1: Setup

- [x] T001 Prepare the locked test environment with `uv sync --locked --extra dev` and record the command in `design/quickstart.md`. (delivered: `.venv/bin/python`)
- [x] T002 Write the updated specification and its quality checklist under `specs/numbered/0/0/1/0/3/3/0/0/3575-long-packet-streams/`. (delivered: `specs/numbered/0/0/1/0/3/3/0/0/3575-long-packet-streams/spec.md`)
- [x] T003 Record the current runner, event, cleanup, and retention decisions in `design/research.md`. (delivered: `specs/numbered/0/0/1/0/3/3/0/0/3575-long-packet-streams/design/research.md`)

## Phase 2: Foundational

**Purpose**: Preserve the current transport and capture identity contracts.

- [x] T004 Verify current package paths, fake cloud support, and open pull request ownership in `plan.md`. (delivered: `specs/numbered/0/0/1/0/3/3/0/0/3575-long-packet-streams/plan.md`)

## Phase 3: User Story 1 - Select a capture duration (Priority: P1)

**Goal**: Accept safe capture durations from 60 through 3600 seconds.

**Independent Test**: Check catalog metadata, form bounds, server validation,
and the exact duration sent in a local capture request.

### Tests for User Story 1

- [x] T005 [P] [US1] Test the capture duration field and label in `tests/unit/websocket_streams/catalog/test_ws_utility_catalog.py`.
- [x] T006 [P] [US1] Test duration boundaries, Boolean input, Unicode digits, and oversized text in `tests/unit/websocket_streams/intake/test_ws_field_checker.py`.
- [x] T007 [P] [US1] Test selected duration forwarding and default request timing in `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_triggers.py`.
- [x] T008 [P] [US1] Test duration selection and submitted form values in `tests/e2e/websockets_tab/test_websockets_page.py`.

### Implementation for User Story 1

- [x] T009 [US1] Add duration metadata and clear capture text in `src/mist/realtime/websocket_streams/catalog/model.py`, `src/mist/realtime/websocket_streams/catalog/utilities/utility_fields.py`, and `src/mist/realtime/websocket_streams/catalog/utilities/metadata/utility_text.py`.
- [x] T010 [US1] Bound integer text before conversion in `src/mist/realtime/websocket_streams/intake/fields/scalar_checker.py`.
- [x] T011 [US1] Pass the checked duration into `src/mist/realtime/websocket_streams/live/runners/utility/triggers/body_builder.py`.
- [x] T012 [US1] Publish the 3600-second capture limit in `src/mist/realtime/websocket_streams/live/sessions/settings.py` and `src/mist/realtime/websocket_streams/web/services/assembly/fallback.py`.
- [x] T013 [US1] Update settings and fallback assertions in `tests/unit/websocket_streams/live/sessions/test_ws_stream_settings.py` and `tests/unit/websocket_streams/web/test_ws_web_services.py`.
- [x] T014 [US1] Compare selected capture durations with SDK requests in `tests/contract/websocket_streams/test_ws_utility_trigger_parity.py`.

## Phase 4: User Story 2 - Receive only matching packet records (Priority: P1)

**Goal**: Keep captures active through quiet periods and finish on a matching
capture-end event or the selected duration.

**Independent Test**: Use a fake stream and controlled clock to verify quiet
periods, matching records, end events, and the 3599-second boundary.

### Tests for User Story 2

- [x] T015 [P] [US2] Test quiet-period retention, packet identity filtering, duration completion, and null-packet end events in `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py`.
- [x] T016 [P] [US2] Test that the capture clock starts after the successful response in `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py`.

### Implementation for User Story 2

- [x] T017 [US2] Record capture start and completion state in `src/mist/realtime/websocket_streams/live/runners/utility/runner/utility_runner.py`.
- [x] T018 [US2] Start timing after the capture response and keep quiet captures active in `src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py` and `src/mist/realtime/websocket_streams/live/runners/utility/runner/monitoring.py`.
- [x] T019 [US2] Finish captures normally on duration or matching end events in `src/mist/realtime/websocket_streams/live/runners/utility/runner/monitoring.py`.

## Phase 5: User Story 3 - Stop and release the capture (Priority: P1)

**Goal**: Preserve identifier-checked cleanup and report uncertain stops as
failures.

**Independent Test**: Stop local fake captures with matching and mismatched
identifiers. Verify the delete count and terminal state.

### Tests for User Story 3

- [x] T020 [P] [US3] Test capture-only lifetime extension and stuck-stop failure in `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py`.
- [x] T021 [P] [US3] Test that identifier mismatch, lookup failure, and delete failure do not report success in `tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py`.
- [x] T022 [P] [US3] Verify cleanup completes before the terminal state in `tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py`.

### Implementation for User Story 3

- [x] T023 [US3] Extend only capture session lifetime and fail an unconfirmed capture stop in `src/mist/realtime/websocket_streams/live/sessions/manager/lifecycle.py`.
- [x] T024 [US3] Report identifier and API stop failures without sending an unrelated delete in `src/mist/realtime/websocket_streams/live/runners/utility/runner/capture.py` and `src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py`.

## Phase 6: Polish and Cross-Cutting Concerns

- [x] T025 [P] Add the issue-specific release note in `changelog.d/issue-3575-long-packet-streams.md`.
- [x] T026 Update the Web Portal capture duration guidance in `documentation/wiki/Web-Portal.md`.
- [x] T027 Run focused unit, contract, and browser tests from `specs/numbered/0/0/1/0/3/3/0/0/3575-long-packet-streams/design/quickstart.md`.
- [x] T028 Run Ruff, Black, mypy, and applicable WebSockets guardrails for the Python paths listed in `specs/numbered/0/0/1/0/3/3/0/0/3575-long-packet-streams/plan.md`.
- [ ] T029 Run `tests/guardrails/test_spec_route_contract.py` to verify the managed specification route. (Blocked: `pwsh` is unavailable.)
- [x] T030 Commit the explicit feature file set from `specs/numbered/0/0/1/0/3/3/0/0/3575-long-packet-streams/plan.md` with a Conventional Commit subject and the required co-author trailer.
- [x] T031 Run the required test-quality preflight and changed-from-base ratchet after the local commit.
- [x] T032 Recheck the local commit and `origin/recovery/3575-handoff-20261004` without pushing or creating a pull request, using the files listed in `specs/numbered/0/0/1/0/3/3/0/0/3575-long-packet-streams/plan.md`.

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: Complete before implementation. The managed specification and
  local test environment are ready.
- **Foundational**: Complete before story work. Existing local fake services
  and current package ownership are confirmed.
- **User Story 1**: Delivers the duration input and request body.
- **User Story 2**: Depends on the duration from User Story 1.
- **User Story 3**: Uses the current capture identity and cleanup contract.
- **Polish**: Depends on all three stories and their focused tests.

### User Story Dependencies

- **US1**: Independent of the other stories.
- **US2**: Uses the duration introduced by US1.
- **US3**: Can be tested with the existing capture request and fake cloud.

### Parallel Opportunities

- T005 through T008 use separate test files and can be authored in parallel.
- T015 and T016 share one test file and should be authored together.
- T020 and T021 use separate test files and can be authored in parallel.
- Implementation changes to one shared runner or manager file remain sequential.
- No publication task can run until the user grants a serial slot.

## Parallel Example: User Story 1

```text
Task: T005 Test capture catalog duration metadata.
Task: T006 Test duration input boundaries.
Task: T008 Test the duration form in the local browser fixture.
```

## Implementation Strategy

1. Keep the current package and fake cloud. Do not copy the recovery transport.
2. Add tests for duration input and trigger construction.
3. Implement and verify User Story 1.
4. Add tests for full-duration monitoring and matching capture-end events.
5. Implement and verify User Story 2.
6. Add tests for capture-only retention and safe stop failures.
7. Implement and verify User Story 3.
8. Run the focused gates, commit locally, and run the test-quality ratchet.
9. Stop before push, pull request creation, merge, or auto-merge.
