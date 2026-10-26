# Tasks: Capture cleanup completion

**Input**: [spec.md](spec.md), [plan.md](plan.md), and the supporting records under `design/`.

## Phase 1: Setup

- [x] T001 Inspect current source and ownership for `src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py`. (delivered: design/research.md)

## Phase 2: Foundational

- [x] T002 Create the deterministic barrier in `tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py` and record its unchanged-source failure. (delivered: design/research.md)

## Phase 3: User Story 1 - Completion after cleanup

**Goal**: Establish cleanup completion before a terminal outcome.
**Independent test**: Block the identity check and observe zero terminal notifications for site and organization captures.

- [x] T003 [US1] Delay terminal notification until cleanup ends. (delivered: src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py)
- [x] T004 [US1] Verify matching and foreign capture identities. (delivered: tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py)

## Phase 4: User Story 2 - Explicit cleanup failure

**Goal**: Report failed cleanup without a successful stop outcome.
**Independent test**: Raise a cleanup exception and observe exactly one safe failed notification.

- [x] T005 [US2] Handle cleanup exceptions separately. (delivered: src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py)
- [x] T006 [US2] Verify cleanup exceptions and execution errors. (delivered: tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py)

## Phase 5: Verification and publication

- [x] T007 [P] Add the release-note fragment. (delivered: changelog.d/issue-3769-capture-cleanup-completion.md)
- [ ] T008 Run the focused tests and applicable gates, then record exact results in `analysis.md`.
- [ ] T009 Prepare the explicit file manifest and PR evidence in `analysis.md` using `.github/PULL_REQUEST_TEMPLATE.md`.

## Dependencies

T002 requires T001. T003 and T005 require T002.
T004 requires T003. T006 requires T005.
T008 requires T004, T006, and T007. T009 requires T008.

## Parallel execution

T007 can run independently after the specification is approved.
Source changes for both user stories remain sequential because they share one lifecycle method.

## Implementation strategy

Use the failing barrier as the first proof.
Repair lifecycle ordering and explicit failure handling together.
Retain the unchanged existing utility tests as the regression contract.
Optional commit hooks remain deferred until the verified final commit.
After these implementation tasks, commit, check test quality, push, and create the requested PR.
Do not merge or enable auto-merge.
