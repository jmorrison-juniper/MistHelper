# Capture session contract

## Form and start request

- Show a whole-number duration field for each packet capture.
- Set its default to 60 seconds and its bounds to 60 and 3600 seconds.
- Reject invalid form or JSON values before opening a stream or starting a capture.
- Keep current target, packet count, packet length, and filter rules.

## Start order and records

1. Confirm the subscription for the selected `site_pcaps` or `org_pcaps` channel.
2. Send one capture start request through the existing Mist API session.
3. Start the capture monitor clock after the successful response.
4. Show only records with the selected channel and capture identifier.
5. Keep the monitor open through quiet periods.
6. End normally on the requested duration or a matching null-packet end event.

## Stop and cleanup

- On operator stop, read the status object from `GET /api/v1/{sites|orgs}/{id}/pcaps/capture`.
- Match its identifier. Reject a non-object status or a false or malformed `enabled` field.
- Send one `DELETE` to that same endpoint only after the identifier matches.
- Report a mismatch, request failure, or unconfirmed cleanup as failure.
- Close the stream and release owned resources before publishing a terminal state.

Warning: the stop operation accepts no capture identifier. A replacement capture
between the status request and stop request can receive the scope-wide stop.
This check is not atomic cancellation.

## Safety and verification

Tests use local fake services and controlled clocks. They do not use live Mist
credentials, external production endpoints, or production data.
