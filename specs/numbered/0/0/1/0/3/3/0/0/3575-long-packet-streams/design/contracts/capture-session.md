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

- On operator stop, check the active capture identifier with the existing lookup.
- Send one scope delete only when the identifier matches.
- Report a mismatch, request failure, or unconfirmed cleanup as failure.
- Close the stream and release owned resources before publishing a terminal state.

## Safety and verification

Tests use local fake services and controlled clocks. They do not use live Mist
credentials, external production endpoints, or production data.
