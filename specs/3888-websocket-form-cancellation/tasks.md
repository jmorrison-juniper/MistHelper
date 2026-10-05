# Tasks: WebSocket Operation Form Cancellation

**Input**: Design documents in `specs/3888-websocket-form-cancellation/`

**Prerequisites**: `plan.md`, `spec.md`, `checklists/research.md`,
`checklists/data-model.md`, `checklists/contracts/ui-cancellation.md`, and
`checklists/quickstart.md`.

**Ownership update**: PR #3814 and PR #3891 have merged, so the page controller in
`src/mist/realtime/websocket_streams/web/static/websockets.js` is available
for the required state and picker integration. This resolves the plan's
implementation ownership blocker.

**Scope constraints**: Keep the implementation in the existing template,
controller, and browser test module identified below. Do not change operation
selectors, catalog wording, `utility_text`, or `utility_discovery.py`. Do not
modify `tests/tools/websocket_dialog_audit/` or
`specs/3760-issue3862-websocket-dialog-audit/`. Use fake browser routes only;
do not start live operations, utilities, captures, or shell interactions.

## Phase 1: Setup

**Purpose**: Reuse the existing portal, controller, and browser test
infrastructure; no new runtime dependencies or project scaffolding are needed.

- [X] T001 Confirm implementation uses the existing files `src/mist/realtime/websocket_streams/web/templates/websockets_page.html`, `src/mist/realtime/websocket_streams/web/static/websockets.js`, and `tests/e2e/websockets_tab/test_websockets_terminal.py`; do not add direct children to their directories.

## Phase 2: Foundational

**Purpose**: No backend, persistence, picker-route, or shared infrastructure
changes are required. The existing form state, picker callbacks, fake portal
harness, and Playwright setup are the shared foundation.

**Checkpoint**: The existing target paths are confirmed; proceed to story
implementation without adding a second controller or state owner.

## Phase 3: User Story 1 - Cancel an unsubmitted operation selection
(Priority: P1)

**Goal**: Let a user discard any selected operation and all pending form
values without starting it.

**Independent Test**: As a normal user in the fake portal, select an
operation, enter selection-specific values, activate Cancel, and verify the
form is unselected and empty, Start is unavailable, and the session-start
route receives no request. Confirm the shared form exposes Cancel for each of
the 72 live operation entries.

### Tests for User Story 1

- [X] T002 [US1] Add a normal-user Playwright regression in `tests/e2e/websockets_tab/test_websockets_terminal.py` that selects an operation, populates target, parameter, repeatable, and confirmation fields where applicable, activates Cancel, asserts selection and values are cleared and Start is unavailable, verifies the fake `/api/websockets/sessions` route receives zero start requests, and confirms Cancel is presented for all 72 live operation entries.

### Implementation for User Story 1

- [X] T003 [P] [US1] Add a clearly labeled Cancel control to the shared form in `src/mist/realtime/websocket_streams/web/templates/websockets_page.html`; present it only for a selected, unsubmitted operation and preserve existing catalog selectors and wording.
- [X] T004 [P] [US1] Wire Cancel in `src/mist/realtime/websocket_streams/web/static/websockets.js` to clear authoritative pending selection (`state.selectedEntry`), selection-scoped target and parameter values including repeatable inputs, confirmation, notices/errors, and selected-entry presentation; return to unselected state, disable Start, and issue neither a start nor session-stop request.

**Checkpoint**: The user can discard the pending form selection with no
operation start, while the existing session lifecycle remains separate.

## Phase 4: User Story 2 - Keep canceled selections canceled (Priority: P1)

**Goal**: Ensure picker responses from canceled or replaced selections cannot
restore old state or affect the current selection.

**Independent Test**: Hold a picker response in the fake browser harness,
cancel before releasing it, and verify the form remains unselected and empty.
Also replace selection A with selection B before A's response arrives and
verify only B's picker results can affect the form.

### Tests for User Story 2

- [X] T005 [US2] Extend the fake-route Playwright regression in `tests/e2e/websockets_tab/test_websockets_terminal.py` with a deterministically delayed picker response; cancel before releasing it and assert selection, fields, and picker presentation remain cleared, then release a response for superseded selection A after selecting B and assert it cannot alter B.

### Implementation for User Story 2

- [X] T006 [US2] Add a selection-generation token in `src/mist/realtime/websocket_streams/web/static/websockets.js`; advance it on selection replacement and Cancel, capture it with entry identity for each picker request, discard stale success/empty/failure callbacks before controls, options, or shared picker-label state change, and retain the per-control request serial.

**Checkpoint**: Canceled and superseded picker results have no visible or
shared-state effects, while current picker reads continue to work.

## Phase 5: User Story 3 - Preserve live session cards (Priority: P2)

**Goal**: Keep form cancellation limited to unsent selections and preserve
unrelated submitted sessions and their controls.

**Independent Test**: Keep a fake live session card visible, select and cancel
a separate operation, then verify the same card identity and state remain
visible and no stop request is issued.

### Tests for User Story 3

- [X] T007 [US3] Add a Playwright assertion in `tests/e2e/websockets_tab/test_websockets_terminal.py` that keeps a fake live session visible while canceling a different unsubmitted selection, verifies the card identity and state are unchanged and the fake session-stop route receives zero requests, and confirms submitted-session controls still own lifecycle actions.

**Checkpoint**: Form cancellation leaves existing live cards and their
session lifecycle unchanged.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Add the required release record and validate the integrated
normal-user regression.

- [X] T008 Create exactly one release fragment at `changelog.d/issue-3888-websocket-form-cancellation.md` describing explicit cancellation of unsubmitted WebSocket operation forms; do not edit `CHANGELOG.md`.
- [X] T009 Run the normal-user Playwright regression with fake routes using `.venv/bin/python -m pytest tests/e2e/websockets_tab/test_websockets_terminal.py -k 'cancellation or cancel_is_hidden' -q`; it passed 2 tests with no live operation.
- [X] T010 Update `documentation/wiki/Web-Portal.md` to explain how Cancel clears an unsubmitted form without stopping a live session.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 confirms the existing files that will be edited.
- **Foundational (Phase 2)**: No implementation task is needed; existing
  portal and test infrastructure is sufficient.
- **User Story 1 (Phase 3)**: Begins after T001. T002 adds its regression
  before implementation; T003 and T004 then implement the shared form and
  authoritative cancellation behavior.
- **User Story 2 (Phase 4)**: Depends on T004 because stale-picker handling
  uses the same controller state and cancellation transition. T005 specifies
  the delayed-response regression before T006 adds the generation guard.
- **User Story 3 (Phase 5)**: Depends on the form cancellation behavior from
  T004. T007 validates the isolation from existing session cards.
- **Polish (Phase 6)**: T008 and T009 follow implementation and story-level
  regression work.

### User Story Dependencies

- **US1 (P1)**: Depends only on the existing portal setup confirmed by T001.
- **US2 (P1)**: Depends on US1's pending-selection cancellation state so
  picker responses can be fenced against the authoritative selection.
- **US3 (P2)**: Reuses US1 cancellation; it does not depend on US2's picker
  behavior, although the planned regression run follows all stories.

### Parallel Opportunities

- After T002 establishes the expected user behavior, T003 (template) and
  T004 (controller) touch different existing files and can proceed in
  parallel if the control's form contract is agreed first.
- T008's release-fragment draft can be prepared independently of code
  implementation, but final validation T009 requires the feature changes.
- T005 and T007 both edit the same existing browser test module and should be
  performed sequentially, not in parallel.
- T004 and T006 edit the same controller and should be performed
  sequentially.

## Parallel Example: User Story 1

```text
After T002 defines the expected behavior:
Task T003: Add the form Cancel control in
  src/mist/realtime/websocket_streams/web/templates/websockets_page.html
Task T004: Implement authoritative cancel handling in
  src/mist/realtime/websocket_streams/web/static/websockets.js
```

## Implementation Strategy

### MVP First (User Story 1)

1. Complete T001 and establish the user-facing expectations in T002.
2. Implement the shared-form control and authoritative state transition in
   T003-T004.
3. Validate US1 independently: cancel clears the pending selection and values
   and sends no start request.
4. Add US2 generation fencing and delayed-picker regression (T005-T006).
5. Add US3 live-card preservation regression (T007).
6. Add the release fragment and run the browser regression (T008-T009).

### Incremental Delivery

1. Deliver US1 as the MVP: safe cancellation of any pending catalog
   operation.
2. Deliver US2 next: stale picker callbacks cannot undo cancellation or a
   newer selection.
3. Deliver US3 next: prove form cancellation cannot affect a submitted
   session.
4. Complete the release record and regression run before considering the
   feature ready.
