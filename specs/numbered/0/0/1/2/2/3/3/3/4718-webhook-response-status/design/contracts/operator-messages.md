# Contract: Operator messages

## Error messages on rejection

These messages keep their current wording. The repair changes no character.

- List call: `The cloud returned HTTP %s for organization webhooks at org %s`. The first value is the integer HTTP status, or `missing or invalid`. The second value is the organization identifier. The current lines are exporter lines 77 to 81 (R01).
- Delivery call: `The cloud returned HTTP %s for organization webhook deliveries at org %s`. The values match the list call. The current lines are exporter lines 139 to 143 (R04).

## Notices on valid responses

These notices keep their current wording.

- List call with a valid empty result: `! No webhooks configured for this organization`. The notice is asserted at test line 355 (R11).
- Delivery call with a valid empty result: `! No organization webhook delivery data found`. The notice is asserted at test line 355 (R11).
- Delivery write success: `! %d organization webhook delivery records exported to %s`.

## Debug lines (new)

The debug lines follow each SDK call. The helper writes them (T009).

- Valid HTTP status: `%s returned HTTP %s`. The first value is the call name. The second value is the integer status. Example: `listOrgWebhooks returned HTTP 200`.
- Missing or invalid HTTP status: `%s returned no valid HTTP status`. The first value is the call name. Example: `searchOrgWebhooksDeliveries returned no valid HTTP status`.

The debug lines never echo the raw invalid value.

## Words that rejection must not log

The rejected-status test checks these four strings in the captured log text (test line 329, R10):

- `No webhooks configured`
- `No organization webhook delivery data`
- `exported`
- `persisted`

A rejected initial response must not write any of these strings in any log line. The debug lines of T009 use neither word.

## Logging rules

- Use ASCII text only.
- Use `%s` formatting, not f-strings, in each logging call.
- Do not log a token, a password, a session object, or a response body.
