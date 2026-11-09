# Research: Long packet capture

## Decision: Reuse the current utility runner

The current `UtilityStreamOpener` confirms its stream subscription before it
sends the capture REST request. The current `UtilityMessageFilter` selects
records by capture identifier. Reuse both contracts.

The recovery branch uses the retired top-level WebSocket package and a
separate transport. The current package lives under
`src/mist/realtime/websocket_streams/`. Do not copy the retired transport or
reintroduce its package paths.

## Decision: Use the existing capture request and event contracts

`CaptureBodyBuilder` currently sets a 60-second duration. The request builder
already sets the stream total to the requested duration plus ten seconds.
Expose the duration through the current catalog and pass the checked value to
the body builder.

The bundled Mist API example marks a stopped capture with its `capture_id` and
`pcap_dict: null`. Treat only a matching end event as normal completion.

## Decision: Check active status before a scope-wide stop

The bundled OpenAPI contract defines active status as one object from
`GET /api/v1/{sites|orgs}/{id}/pcaps/capture`. The `id` field identifies the
capture. The optional `enabled` field identifies a disabled capture when false.
The `/pcaps` collection lists completed captures and cannot prove active identity.

Read active status through the existing SDK session. Check the identifier and
reject a non-object status or a false or malformed `enabled` field. Then send
`DELETE /api/v1/{sites|orgs}/{id}/pcaps/capture`. The stop operation accepts no
capture identifier. Do not copy the recovery branch's private HTTP transport.

If the active identifier differs or cannot be confirmed, do not send a delete
and do not report a successful stop.

Warning: another operator can replace the active capture between the status
request and the stop request. The scope-wide stop can then stop that replacement.
The API offers no atomic identifier-specific stop. The identity guard reduces
risk but cannot remove this race.

## Decision: Extend only capture retention

The general session life limit is 30 minutes by default. A 3600-second capture
needs a capture-specific life allowance that includes stream completion and
cleanup margins. Keep the configured limit for every non-capture session.
Keep idle cleanup unchanged.

## Alternatives considered

- **Restore the recovery branch's transport**: Rejected because the current
  runner already confirms subscription before start and uses the current SDK
  session for REST calls.
- **Increase the global session limit**: Rejected because it would extend
  shell and non-capture stream sessions.
- **Keep the generic quiet and first-output limits**: Rejected because an idle
  capture would end before its selected duration.
- **Delete a capture without checking its identifier**: Rejected because the
  delete request is scope-wide.

## Test evidence

Use `FakeMistCloud`, fake API sessions, controlled clocks, Flask test clients,
and local Playwright fixtures. Do not call Mist or production services.
