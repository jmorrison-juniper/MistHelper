# Contracts: Long packet streams

## Existing HTTP interface

`POST /api/websockets/sessions` retains the existing utility request shape.
Packet requests add `parameters.duration`.
The default remains 60 when the request omits the duration.
Valid durations are whole numbers from 60 through 3600.
Reject Boolean, fractional, Unicode-digit, and oversized values with `bad_request`.
Validate before connection or capture start.

`GET /api/websockets/sessions/{session_id}/messages` retains the message contract.
Packet records retain `kind=packet`, safe content, and the existing summary.
The card, counters, filter, download, and buffer gap behavior remain unchanged.

`POST /api/websockets/sessions/{session_id}/stop` retains its asynchronous response.
The card stays in `stopping` until the capture worker reports the result.
A timeout must not claim a confirmed cloud stop.

## Subscribe-first order

1. Validate the request and target permission.
2. Register SDK callbacks.
3. Connect with the current regional and authentication context.
4. Receive `channel_subscribed` for the exact private channel.
5. Send one explicit SDK capture start.
6. Validate the HTTP result and capture identity.
7. Deliver matching pending records.
8. Receive matching records until the terminal condition.

An open socket is not subscription confirmation.
Repeated confirmations and reconnects must not repeat step 5.
No confirmation, refusal, or stop before admission permits a capture start.

## Early stop

Read `getSiteCapturingStatus` or `getOrgCapturingStatus`.
Require a successful response and the accepted capture `id`.
If the active identifier differs, send no stop.
Report the identity conflict.

Call the matching SDK stop once.
Require a successful stop response without an error object or malformed body.
A disconnect or unsubscribe alone does not meet this contract.

## Identity and permission

The portal supplies `org_id`.
Verify the selected site belongs to that organization before capture work.
Keep the existing device family and safety checks.
Verify Mist Edge membership for the selected scope.
Reject another channel or another `capture_id` before card delivery.
Reject a start response that names another scope.

## Cleanup and timing

Bound subscription confirmation to 10 seconds.
Bound HTTP phases, rate waits, and SDK disconnect joins.
Use a five-second private socket timeout for connection and handshake.
Do not change the global socket timeout or another stream's socket factory.
Do not use the utility helper's 60-second timer.
Measure capture duration after the accepted start response.
The manager must not apply its 1800-second channel limit to a 3600-second capture.
Idle reads and the existing total session limit still apply.

Close all owned connections on completion, stop, timeout, disconnect, and error.
Do not disconnect another tab stream.
Do not modify the shared session transport.
Do not log packet contents, credentials, remote error text, or raw responses.
Keep SDK logs for owned capture threads at the metadata boundary.

## Browser behavior

Expose `ws-field-duration` with minimum 60, maximum 3600, and default 60.
Refuse invalid input before the browser sends a start request.
Use the actual `ws-output`, `ws-counters`, `ws-session-state`, and `ws-stop-button`.
Keep all record rendering as text.
Retain explicit failure text for a failed cloud stop.
