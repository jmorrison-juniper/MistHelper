# Portal Contract: Guest Authorizations

## Entry, Rights, and Access

No guest-data route or workflow may exist until G1-G5 in [research](../research.md) pass.
This includes read-only listings, search, previews, imports, and disabled write controls connected to live data.
Do not use a feature flag to bypass the gates.
The current offline projection has no route and needs no new portal registration.

Future integration uses the existing portal and session.
Approve accountable operator access or explicitly approve the shared-token/no-login model before integration.
Check organization, site, WLAN, and action permission on every request.
CSRF validation does not replace identity or authorization.
Reject missing, changed, or cross-organization scope before disclosure or SDK submission.

## Conditional Journeys

| Journey | Operator interaction | Required observable result |
| --- | --- | --- |
| Review | Select permitted site and guest WLAN | Only verified returned facts, with unknown fields explicit |
| Search | Enter MAC address, hostname, or IP address | Only supported permitted client matches |
| Grant | Validate device and duration, review scope, type exact confirmation | One bound change or a visible rejected/unknown outcome |
| Edit | Select verified writable fields and confirm | No unsupported field submission |
| Extend | Review the verified duration and expiry rule, then confirm | No invented extension or timezone semantics |
| Revoke | Review target and confirm the approved operation | Ended access only after verified termination evidence |
| Import | Upload within limits, review each row, confirm the fixed batch | Ordered writes and one outcome per row |

The exact confirmation words require approval in the future operation contract.
Every cloud-changing action requires an exact operation-specific typed word.
Import uses one batch confirmation bound to reviewed content, scope, and duration.
It does not require a different operator decision for each unchanged row.
Changing any reviewed input invalidates confirmation.

## Outcome Rules

Invalid input, wrong confirmation, cancellation, denied permission, and stale selection produce zero writes.
Escape returned and operator-provided text before display.
Do not show a full device identifier unless the approved disclosure contract requires it.
Do not show historical expired counts from an incomplete current list.

An accepted cloud write and failed audit write are separate outcomes.
Display both facts without overall success, stop subsequent writes, and prohibit automatic retry.
G4 must approve pre-write audit readiness, post-write recovery, and the operator reconciliation procedure.
Do not invent an existing durable audit service from an ordinary application log.

## Browser and Integration Evidence

Every interactive element needs a stable `data-testid` and accessible label.
Test selection changes, denied reads, canceled and wrong confirmations, unsupported fields, and out-of-scope tampering.
Test missing credentials, permission errors, service errors, timeouts, rate limits, and failed audit persistence.
Test CSV byte/row boundaries, encoding, duplicate normalization, reviewed-content changes, and partial outcomes.
Use fictional data and mocked SDK responses. Retain screenshots or traces for browser failures.
The current projection serialization test does not satisfy these future integration tests.
