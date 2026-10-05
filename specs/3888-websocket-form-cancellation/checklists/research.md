# Research: WebSocket Operation Form Cancellation

## Decision 1: Cancellation belongs to the existing page-state owner

**Decision**: The pending operation must be cleared through the state owner in
`src/mist/realtime/websocket_streams/web/static/websockets.js`. The Cancel
control may be rendered in the Jinja template, but the existing controller
must perform the state transition.

**Rationale**: The WebSockets page uses one shared form for all catalog
entries. `selectEntry` stores the active entry in closure-private
`state.selectedEntry`, and `startSelected` checks that value before sending
`POST /api/websockets/sessions`. Clearing fields and labels in the DOM does
not clear the state used by the submit path. There is no public page-state API
or hook for another controller to call.

**Alternatives considered**:
- Clear controls in the template or a sidecar controller: rejected because
  the selected entry remains authoritative and can still be submitted.
- Intercept form submission in a sidecar: rejected because it masks one path
  without clearing the source of truth or supporting later selection
  transitions.
- Monkey-patch fetch: rejected because it is a brittle transport-level
  workaround, does not clear selection state, and does not guard callback
  side effects before they occur.

## Decision 2: Fence picker responses by selection identity

**Decision**: Add a monotonically increasing selection generation (or an
equivalent unique selection token) to the integrated page controller. Capture
it with the selected entry identity when a picker request starts. Before
processing any response, require both to match the active selection. Retain
the current per-select request serial for multiple reads belonging to the
same selection.

**Rationale**: Current picker callbacks compare the select's `data-ws-load`
serial and then call `fillPicker`. Replacing a form detaches its controls, but
the old callback can still process its detached select; `pickerOption` also
updates shared `state.labels`. Per-select ordering does not encode the
selection lifetime. A selection-level guard at the callback boundary can
discard obsolete replies before they update fields or shared state.

**Alternatives considered**:
- Rely only on detached old select elements: rejected because the callback
  still executes and can update shared labels; it also does not state the
  contract that obsolete results have no side effects.
- Replace the existing serial: rejected because serials remain useful for
  overlapping reads on one still-active select; selection identity addresses
  a different lifetime boundary.

## Decision 3: Cancel is not a session stop action

**Decision**: Cancel is available only while the user is preparing an
unsubmitted selection. It clears selection-specific values, confirmation,
warning/error text, and selected-entry presentation, and disables Start. It
does not call session lifecycle routes or mutate session-card state.

**Rationale**: The form and session cards represent separate lifecycles.
Existing session controls own stopping a submitted session.

**Alternatives considered**:
- Reuse or redirect to the selected-session Stop control: rejected because
  it conflates unsubmitted form state with an already-running operation.

## Decision 4: Integrate in the existing controller

**Decision**: Keep cancellation and picker fencing in the page controller
that owns the pending selection.

**Rationale**: PR #3814 and PR #3891 have merged. The existing controller is
available and already owns `state.selectedEntry`, the submit guard, picker
serial checks, callbacks, and shared label updates.

**Alternatives considered**:
- Add only a Cancel button and clear its target nodes: rejected because the
  Start handler would still see a selected entry.
- Add a dedicated controller: rejected because it would create a second
  state owner and could not guard the existing callback side effects.

## Repository and tool choices

- Existing picker endpoints remain unchanged; no new API dependency or
  persistent model is required.
- Use the existing fake portal and Playwright infrastructure; delay a picker
  response deterministically rather than contacting Mist or starting an
  operation.
- Reuse the existing browser test module to avoid adding a file to the
  already overfull `tests/e2e/websockets_tab/` directory.
- No implementation ownership gate remains. No `NEEDS CLARIFICATION` remains
  for the design.
