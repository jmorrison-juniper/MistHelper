# Inventory, Browser Policy, and Report Contract

This contract defines a proposed test harness. No command or fixture below exists yet.
It adds no product endpoint and no Mist transport.

## Harness interface

Later tests live under `tests/tools/websocket_dialog_audit/`.
Default collection must run offline or skip live cases with a recorded reason.
The live entrypoint requires an explicit audit mode and an authorized base URL.
Never obtain a live URL from a default, guess, redirect, or public report.

Implemented pytest options:

- `--ws-audit-mode=isolated|live-inspection|live-readonly`
- `--ws-audit-base-url=<authorized portal URL>`
- `--ws-audit-artifacts=<restricted local directory>`

The bounded lifecycle admits only `site.stats.devices`; it has no generalized policy-file or operation option.

The options must not accept tokens or passwords.
Use existing local authentication through a restricted browser state or the existing authorized session.
Reject URL credentials, unapproved origins, path traversal, and unsafe artifact paths.
Authentication absence must block. Do not automate credential changes or weaken TLS checks.

## Inventory contract

1. Read the real catalog payload from the selected revision.
2. Enumerate actual `.ws-catalog-entry` buttons and their `data-key`.
3. Join keys to real source definitions, SDK signatures, and runner paths.
4. Record missing, duplicate, extra, locked, and unverified operations.
5. Inspect each form without granting permission to submit.

Catalog membership and safety labels are inputs, not an authority.
Use `#wsSelectedTitle`, `#wsSelectedDescription`, `#wsTargetFields`, and `#wsParameterFields` as current source anchors.
Use labels and visible controls to prove user-facing selector behavior.
Check `#wsStartForm`, `#wsStartButton`, and `#wsStartError`.
Treat anchor drift as a reported failure, not permission to substitute a fake page.

Required-field checks need an independent SDK and runner oracle.
Do not require a device or client selector when the verified operation does not need one.
Check that irrelevant stale fields disappear.
Check multiplicity, family filters, current choices, and label association.
Missing prerequisites must prevent submission, not merely disable a visual label.

There is no universal operation Cancel button in the inspected template.
Check the actual user path for abandoning or replacing a selection.
Distinguish page navigation from an explicit cancel control.
Do not use terminal paste cancellation to pass the operation cancellation check.
If the original user story has no supported cancel path, record evidence for later defect triage.

## Browser request policy

Install context routing before creating or navigating a page.
Set `service_workers="block"`.
Apply the policy to pages, popups, requests, redirects, and browser WebSockets.
Revalidate each redirected request and reject unapproved destinations.
Maintain an exact asset list from the real template and approved portal bootstrap.
Reject new background endpoints until their handlers are verified.

### Inspection mode

Allow exact same-origin GET page/assets and verified catalog/selector reads.
Abort every operation start, stop, input, resize, delete, and download request.
Reject generic `/api/operations/run`, operation streams, utility triggers, and direct Mist browser access.
Reject unknown GET endpoints as well as writes.
An automatic picker read uses the same policy as an explicit read.
Do not contact prohibited handlers to test whether they reject a request.

### Subscription mode

Permit the inspection GET set plus these narrow local lifecycle envelopes:

| Portal action | Required policy |
|---|---|
| POST `/api/websockets/sessions` | One exact `site.stats.devices` channel body with one populated returned site, no parameters, null confirmation and actual local title labels. One attempt, no redirects/retries. |
| GET `/api/websockets/sessions` | Fulfilled locally with only the own returned record; no unrelated sessions are read. |
| GET `/api/websockets/sessions/{owned_id}/messages` | Identifier belongs to the current journey. Query is bounded and verified. |
| POST `/api/websockets/sessions/{owned_id}/stop` | Identifier belongs to the current journey. Stop creates no Mist write. |

Validate the complete real start-request schema from the selected revision.
Do not invent target names, flatten arrays, or accept unknown body keys.
Do not allow `utility` or `shell`, even when the catalog calls them read-only.
Deny session DELETE, download, input, terminal, and resize routes.
Stop is the only permitted lifecycle cleanup action in live mode.
Never stop or clear unrelated sessions.

Selectors use only the eight verified SDK GET candidates listed in [research](../research.md).
Bind site and map values to the authorized organization and current parent selections.
Reject stale, malformed, duplicate, cross-scope, or unexpected query and body values.
Read source and installed SDK definitions before expanding the policy.

## Server egress contract

Browser routing cannot inspect server-side Mist traffic.
Isolated mode therefore blocks network egress and uses synthetic SDK selector records.
It keeps real catalogs and assets.
It captures rejected start attempts without constructing utility or shell runners.

The exact authorized live channel is instead verified through its real checked-request and runner path.
The parent checks deployed `2900f56` against the reviewed local base before the live run.
`ChannelStreamRunner` sends observation SUBSCRIBE through the existing transport.
Local Stop sets its owned stop event and closes that transport, without a Mist REST mutation.
No additional whole-server guard or user approval is required for this verified read-only scope.
Browser rejection traps prove zero transmission for other starts and foreign session controls.
An executable source regression verifies exact checked paths, runner selection and SUBSCRIBE-only frames.
Unknown or changed runner behavior requires a precise source-verification blocker, not a blanket server-guard requirement.

## Journey and cleanup contract

Use one approved target set and one owned live session at a time.
Record selection, subscription acknowledgement, observation, and stop as separate stages.
A session identifier is private local state.
A server response saying `live` is insufficient if acknowledgement is unverified.

Apply 15-second selection and connection limits, a 30-second observation limit, and a 90-second total deadline.
The implemented exact-key observation is five seconds. The outer pytest bound is 120 seconds,
including browser fixture setup and report teardown, not an extended observation permission.
Reserve cleanup time before observation starts.
In `finally`, request stop for the owned session and verify stopped UI state and no later delivery within five seconds.
Stop while connecting must prohibit late subscription and retries.
If cleanup fails, stop further live journeys and report failure.
Do not use shell, force restart, or an unverified fallback to recover.

## Isolated negative matrix

Use synthetic targets and failures for:

- Empty sites, devices, maps, assets, and SDK clients.
- HTTP 401, 403, 429, and 5xx selector responses.
- Duplicate display names, disappearing targets, and unavailable device families.
- Delayed responses, site/map changes, stale values, and abandoned forms.
- Unknown catalog keys, modified bodies, utilities marked read, capture, shell, and mutation attempts.
- Unknown origins, redirects, service workers, popups, WebSockets, and generic operation endpoints.
- Connection timeout, denied subscription, no-data, disconnect, stop during open, and late messages.

Do not manufacture these failures against live Mist.
Source and browser assertions must prove real form construction, not only test-double acceptance.

## Report contract and release gate

Produce restricted machine-readable JSON and a sanitized Markdown summary.
Use the entities and transitions in [data-model.md](../data-model.md).
Include the exact sanitized command, duration, status, evidence mode, stage outcome, and blocker.
Keep separate totals for isolated inspection, live inspection, and live subscription.
List the full inventory denominator and all exclusions.
Never combine blocked, skipped, no-data, or missing rendering evidence into a general pass count.

Process exit `0` means the requested bounded validation scope passed.
Exit `1` means an assertion or policy test failed.
Exit `2` means a capability or safety prerequisite blocked execution.
A partial report must remain available after failure or timeout.
Ordinary pytest skip behavior does not prove the audit passed.
A later report validator must reject blocked required scope and zero collected tests.

Before repair, reuse or create one distinct issue per confirmed defect and link #3862.
Before merge, require current local gates, required CI checks, resolved ownership, and authorized review.
Preserve the repository pull request template and exact evidence.
Missing, skipped, failed, cancelled, stale, or unknown required checks prohibit merge.
