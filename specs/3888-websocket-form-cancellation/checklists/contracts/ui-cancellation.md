# UI Contract: WebSocket Operation Form Cancellation

## Scope

This is a browser UI behavior contract for the existing WebSockets Operations
portal. It adds no HTTP endpoint, request body, response schema, or session
service behavior. The single shared operation form serves the live catalog.

## Control contract

- When a catalog entry is selected and has not been submitted, the form
  exposes a clearly labeled **Cancel** button.
- When submission begins, Cancel is no longer available for that selection;
  the existing session controls own the submitted operation's lifecycle.
- With no pending selection, the page does not suggest that this control
  cancels a live session.
- Cancel returns the form to its unselected presentation, clears all
  selection-dependent target and parameter values (including repeatable and
  confirmation inputs), removes selection-specific notices/errors and
  styling, and leaves Start unavailable.
- Cancel sends no operation-start request and does not create a session.
- Cancel sends no session-stop request and does not alter, remove, or hide an
  unrelated live session card.
- Existing session controls retain responsibility for submitted sessions.

## Asynchronous picker contract

For every picker read, the page controller associates the read with the
selection identity/generation that initiated it and the existing per-control
request serial.

Before any response changes a control, creates option nodes, or updates shared
picker-label state, all guards must pass:

1. The captured selection generation equals the active generation.
2. The captured entry identity equals the current pending entry.
3. The request serial remains current for its control.

If any guard fails, the response is ignored with no UI or shared-state side
effects. Cancellation increments/invalidates the active selection generation
before or while clearing the form. Re-selecting an entry also establishes a
new generation. This applies to successful, empty, and failed picker results.

## Browser acceptance checks

- Use a normal-user browser session and controlled fake routes.
- Assert one visible Cancel control for each of the 72 live catalog entries
  when selected; no new catalog entries are introduced.
- Observe the fake `/api/websockets/sessions` start route and assert that
  cancellation produces zero POSTs.
- Hold and later release picker responses across Cancel and across selection
  replacement. Assert stale results cannot restore or alter the current form.
- Keep a fake live session visible and assert its identity and state remain
  unchanged after a different pending selection is canceled.
- Do not use production Mist credentials, live operations, utility execution,
  packet capture, or shell sessions.

## Integration status

PR #3814 and PR #3891 have merged. The existing controller now owns this
contract, including authoritative selection clearing and the picker response
fence. No separate script or state owner is required.
