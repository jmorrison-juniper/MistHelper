# Request lifecycle and result handling

## Contents

1. [HTTP requests and retries](#http-requests-and-retries)
2. [Pagination, time, and exports](#pagination-time-and-exports)
3. [Asynchronous operations and WebSocket](#asynchronous-operations-and-websocket)
4. [Packet captures and webhooks](#packet-captures-and-webhooks)
5. [Troubleshooting](#troubleshooting)

## HTTP requests and retries

Read the [saved overview](../../../../documentation/Overview%20_%20API%20_%20Mist.html) and the selected operation contract first.
The procedures below add client safety controls. They do not invent server guarantees.

### Request procedure

1. Validate the approved host, scope, parameters, and payload.
2. Set an explicit connection timeout and read timeout.
3. Log the operation and target scope without secret values.
4. Send the request through the approved authenticated session.
5. Record the status, duration, response type, and sanitized result summary.

Check the response before you transform or export it.
An HTML proxy error is not JSON. A JSON error object is not an empty collection.
Keep the original status and sanitized error context when a parser or transformation fails.
Do not let a secondary parsing exception hide the original HTTP error.

### Status handling

The overview documents 200, 400, 401, 403, 404, and 429.
The exact endpoint remains authoritative for additional success and failure statuses.

| Result | Required action |
| - | - |
| Documented success | Validate the response shape, item results, and completion condition. |
| HTTP 400 | Inspect parameter types, locations, conditions, and payload syntax. Do not repeat the unchanged request. |
| HTTP 401 | Check the configured region and authenticated session. Stop repeated credential attempts. |
| HTTP 403 | Check privileges, scope, source-IP restrictions, and feature access. Do not escalate access automatically. |
| HTTP 404 | Check the exact route and resource scope. Do not assume deletion or construct alternate routes. |
| HTTP 429 | Honor `Retry-After` and reduce request load. Keep the total request budget bounded. |
| HTTP 5xx or connection failure on a read | Apply a bounded retry only when the operation is safe to repeat. |
| Timeout or connection loss on a write | Treat the result as uncertain. Reconcile state before another write. |
| Unexpected media type or schema | Preserve sanitized evidence and report a contract mismatch. |

Do not retry an empty successful result merely to obtain nonempty data.
Do not retry every POST because its name contains `get` or `show`.
Read the actual effects and the output mechanism.

### Rate limits

The [rate-limit section](../../../../documentation/Overview%20_%20API%20_%20Mist.html#rate-limit) states 5,000 requests per hour with an hourly reset.
Its HTTP 429 example includes `Retry-After: 798`.
The [usage operation](../../../../documentation/api/self/GET_self_usage.md) exposes `requests` and `request_limit` for the current identity.

Use the actual quota and response headers when available.
Do not assume that a tenant, deployment, or token has a larger quota than the local source states.
Do not rotate tokens or regions to evade a limit.

Estimate the cost before a broad export. Include discovery, pages, retries, polling, and verification requests.
Share the rate budget across workers that use the same credential context.
Use bounded concurrency rather than one worker per device without a limit.

For retryable reads, use capped exponential delay with jitter and a maximum attempt count.
Honor a valid server delay before a shorter client retry delay.
If the delay exceeds the task deadline, report the deferred request instead of retrying early.
Use a cancellable scheduler or the client's documented retry facility.

These delay controls are client policy, not a claim about Mist's internal algorithm.
Do not combine several retry layers without measuring their total attempt count and deadline.

### Write safety and idempotency

Do not assume that the service supports an idempotency key, ETag, transaction, dry-run flag, or atomic bulk update.
Use such a feature only when the selected operation documents it.

Before a change, read the relevant configuration and compare the intended result.
If the desired state already exists, report that result without an unnecessary write.
If another actor changes the resource after the preview, reassess the difference before submission.

After an uncertain write, inspect the documented state or job record.
Do not reissue an upgrade, claim, import, invitation, or capture merely because the response was lost.
If the state cannot be determined, report `unknown` and request an operator decision.

### Bulk and partial results

The [inventory assignment response](../../../../documentation/api/orgs/PUT_orgs_org_id_inventory.md) includes `success`, `error`, `reason`, and `op`.
HTTP 200 does not mean that every requested device succeeded.
An upgrade can report separate queued, successful, and failed target sets.

1. Preserve the requested target set before submission.
2. Classify each returned target from the documented response fields.
3. Identify targets with no final result.
4. Verify successful changes through the relevant read operation.
5. Report successful, failed, pending, and unknown targets separately.

Do not assume that `reason` aligns by index with `error` unless the contract establishes that relationship.
Do not retry successful items when only a subset failed.
Do not claim rollback for a bulk API that provides no transaction guarantee.

## Pagination, time, and exports

Sources: [query parameters](../../../../documentation/Overview%20_%20API%20_%20Mist.html#pagination),
[header pagination](../../../../documentation/Overview%20_%20API%20_%20Mist.html#pagination-by-http-header), and
[inventory notice](../../../../documentation/Org%20_%20API%20_%20Mist.html#pagination-notice).

### Select the response model

| Model | Evidence | Collection rule |
| - | - | - |
| Array with pagination headers | `X-Page-Page`, `X-Page-Limit`, and `X-Page-Total`. | Keep headers with the page and use the documented page mechanism. |
| Object with `results` | Body pagination fields such as `limit`, `page`, `total`, or `next`. | Read only the documented collection and continuation fields. |
| One object | The response describes one resource or summary. | Do not iterate object keys as rows. |
| Binary or text | The operation returns a file, XML, or command text. | Use the media-type-specific handler. |

The overview describes a default limit of 100 and a first page of 1.
Verify endpoint-specific defaults and bounds before selecting a larger page size.
Do not treat MistHelper's configurable page size as a universal API maximum.

The inventory notice warns that an unpaginated request can later return only the first default page.
Always request explicit supported pagination for an exhaustive inventory.
Do not rely on a historical full-list response.

### Page-number collection

1. Freeze the scope, filters, time range, and requested page size.
2. Request the first documented page.
3. Validate the returned metadata and collection type.
4. Accumulate the records and advance the documented page value.
5. Stop only when the documented completion rule proves that no required page remains.

Use the returned effective page size when the server adjusts the requested size.
If a total exists, check the retrieved count against it.
If no total exists, use the endpoint's documented terminal condition.
A short page can indicate completion only when that operation's pagination contract supports the inference.
If completion cannot be established, report a partial result.

Detect repeated page contents or unchanged page metadata.
Bound the page count and total duration to prevent an infinite loop.
If records change during a current-state listing, report that the export is not an atomic snapshot.

### Continuation links

Some search responses contain `next`. Read the exact continuation contract before use.
Resolve a relative continuation against the approved API origin.
Validate the scheme, host, and permitted path of every absolute continuation.
Do not attach a token to an untrusted continuation or redirect.
Preserve the server's continuation parameters rather than reconstructing them from guesses.

Track previously used continuations and stop on a cycle.
If a continuation expires, restart only under an explicit bounded policy that accounts for duplicates.
Do not silently combine incompatible pages from different time windows.

### Search, count, and filter semantics

A count response can group records by a `distinct` attribute. It is not automatically a listing.
Use a count operation when the user wants counts and its filters meet the task.
Use a search operation when the user needs individual records or event details.

Verify every filter name, supported `distinct` value, device type, sort field, and wildcard rule.
Do not copy filters between organization and site endpoints without evidence.
Do not assume that a result cap equals the total number of matching records.
If a documented search limit prevents completeness, use supported narrower windows or report the limit.

Preserve overlapping-window duplicates until the source identity establishes a safe deduplication key.
Do not deduplicate all time-series records by device ID. That deletes valid observations.
Do not deduplicate inventory by display name. Different devices can share a name.

### Time and units

The [timestamp section](../../../../documentation/Overview%20_%20API%20_%20Mist.html#timestamp) states that timestamps use UTC.
The [time-range section](../../../../documentation/Overview%20_%20API%20_%20Mist.html#time-range) documents `start`/`end`, `end`/`duration`, and `duration` forms.
The [aggregation section](../../../../documentation/Overview%20_%20API%20_%20Mist.html#aggregation) explains fixed time bins and adjusted response boundaries.

- Validate that `start` precedes `end`.
- Distinguish epoch seconds from milliseconds and from formatted text.
- Confirm relative-time support on the actual parameter before using values such as `-1d`.
- Fix an absolute end time for a historical multi-page query when the endpoint permits it.
- Preserve the actual returned start, end, interval, timezone, and units.
- Do not assume that a local site timezone changes the API timestamp convention.
- Do not invent inclusive or exclusive boundary semantics when the source does not define them.
- Do not compare bytes with bits, rates with counters, or percentages with fractions without conversion evidence.

An aggregation interval such as `1h` aligns to fixed bins in the saved overview.
Do not label the requested interval boundaries as exact when the API returns adjusted boundaries.

### Exports and data quality

Preserve the organization, site, resource identity, retrieval time, and source operation in combined outputs.
Retain the raw response shape where the task requires auditability and policy permits storage.
Apply a deliberate flattening rule for nested maps and lists.
Do not silently discard nested members, null values, or mixed device types.

For CSV, protect cells that spreadsheet applications interpret as formulas.
For JSON, preserve numeric types and Unicode values while keeping logs compatible with the repository's ASCII policy.
For databases, use the endpoint's approved natural or composite key strategy.
Report export failures independently from API failures.

## Asynchronous operations and WebSocket

### Separate transport success from completion

An HTTP response can acknowledge a request before the device completes it.
An SDK response object does not prove that a firmware image runs or that a capture file is ready.
Read the endpoint's polling route, stream channel, status fields, and terminal conditions.

| Result mechanism | Required correlation |
| - | - |
| Device command stream | The site, device, channel, and returned `session`. |
| Capture stream or capture list | The scope and capture identifier. |
| Upgrade status | The upgrade ID and the target-device set. |
| Synthetic result history | The target, test type, request time, and documented result identifiers. |
| Import or claim job | The returned job ID and the documented status resource. |

Do not assume that every asynchronous response contains a `channel`.
For example, [pingFromDevice](../../../../documentation/api/utilities/POST_sites_site_id_devices_device_id_ping.md) returns `session`.
Its description documents the separate device command channel.

### Device command sequence

The documented channel is `/sites/{site_id}/devices/{device_id}/cmd`.
The WebSocket endpoint is `/api-ws/v1/stream`, not `/api/v1/stream`.

1. Validate the command, target, limits, and permitted authentication method.
2. Connect to the verified regional WebSocket service.
3. Subscribe to the documented command channel before submission when the channel is known.
4. Submit the approved REST command and record the returned `session`.
5. Collect only messages for that channel and session until the documented terminal condition or deadline.

Buffer a small, bounded set of early messages when a result can arrive before the REST response.
Do not accept another command's output merely because the device matches.
Do not treat silence as successful completion.
If the endpoint defines no terminal signal, report the bounded collection and its limitation.

The saved overview shows `subscribe` and `unsubscribe` messages.
It shows `channel_subscribed`, `data`, and `channel_unsubscribed` event types.
The command example places the correlation value in `data.session` and output text in `data.raw`.

Verify the real message shape for the selected operation.
Handle malformed frames, unrelated events, disconnects, and oversized output without unbounded memory growth.
Unsubscribe and close the connection when the task ends.

### WebSocket authentication and recovery

The [saved Python example](../../../../documentation/Overview%20_%20API%20_%20Mist.html#sample-python-code) uses Basic authentication.
This example does not prove that every REST authentication method works unchanged on every WebSocket deployment.
Verify token support and header handling before implementing a token-based stream.
Do not obtain a password or bypass MFA simply to copy the old example.

Use bounded reconnect attempts and a shared deadline.
Resubscribe only to this task's authorized channels.
Do not automatically repeat the REST command after reconnecting.
Report lost output when the source does not guarantee replay.

### Polling and cancellation

Poll only the documented status operation at a bounded interval.
Respect rate limits and stop on terminal state, cancellation, deadline, or lost authorization.
If the task ends before completion, preserve the job identifier for later inspection.

Cancellation is a separate state-changing operation.
Confirm that the user authorized cancellation of that specific job.
Read the cancellation semantics before claiming recovery.
Already completed device changes can remain in place after cancellation.

## Packet captures and webhooks

### Capture sources

- [Saved capture guide](../../../../documentation/Site%20_%20API%20_%20Mist.html#packet-capture).
- [Start a site capture](../../../../documentation/api/utilities/POST_sites_site_id_pcaps_capture.md).
- [Read capture status](../../../../documentation/api/utilities/GET_sites_site_id_pcaps_capture.md).
- [Stop a site capture](../../../../documentation/api/utilities/DELETE_sites_site_id_pcaps_capture.md).
- [List completed captures](../../../../documentation/api/utilities/GET_sites_site_id_pcaps.md).
- [Organization capture](../../../../documentation/api/utilities/POST_orgs_org_id_pcaps_capture.md).

Warning: a packet capture can expose credentials and personal data. Obtain approval for the target and collection scope before capture.

### Capture procedure

1. Select the documented capture type for the device family and diagnostic question.
2. Specify a bounded duration, packet limit, packet length, and supported filter.
3. Inspect the current capture status without stopping another operator's capture.
4. Start the approved capture once and record its identifier.
5. Verify completion and store only the approved artifacts.

The saved Site guide separates wireless-client, association, wired, radiotap, scan-radio, gateway, switch, and Mist Edge captures.
Do not reuse an AP payload for a gateway or switch.
Read the selected type's field names and limits in its own section.
Do not infer capture duration or packet length limits from a different capture type.

The site stream channel is `/sites/{site_id}/pcaps`.
Correlate messages by `capture_id`. Inspect `lost_messages` when the response supplies it.
The documented stop message includes `pcap_dict: null`.
Interpret that signal only within the selected capture's lifecycle.

The capture list can return `url` and `pcap_url`.
Validate a download URL before retrieval. Use a separate unauthenticated client for a signed external download when its contract permits that.
Never forward the Mist token to object storage merely because the API returned its URL.
Treat signed download URLs as secrets and filenames as untrusted input.

If cleanup requires a stop, stop only the capture owned by this task.
Report missing files, expiry, partial packets, message loss, and interrupted collection explicitly.
Do not claim that a capture succeeded merely because a start request returned HTTP 200.

### Webhook sources and signatures

Sources: [saved Webhooks](../../../../documentation/Site%20_%20API%20_%20Mist.html#webhooks),
[site webhook schema](../../../../documentation/api/sites/POST_sites_site_id_webhooks.md), and
[topic definitions](../../../../documentation/api/constants/GET_const_webhook_topics.md).

A webhook sends data from Mist to a receiver. It is not a client WebSocket subscription.
Select the supported topic and the correct organization or site scope.
Creating a webhook changes configuration and can disclose data to an external destination.
Confirm the receiver ownership and the permitted data topics before creation.

For `http-post` with a configured `secret`, the schema describes these headers:

| Header | Documented computation |
| - | - |
| `X-Mist-Signature-v2` | `HMAC_SHA256(secret, body)` |
| `X-Mist-Signature` | `HMAC_SHA1(secret, body)` |

Prefer the v2 signature for a new receiver.
Verify the signature over the raw request body before parsing or reserializing JSON.
Use a constant-time comparison and the documented signature encoding.
If the local source does not establish that encoding, verify it before deployment.
Do not accept an unsigned request when the receiver requires signatures.

Receiver recommendations:

- Bound the request size and processing time.
- Validate the event structure and scope before storing the data.
- Acknowledge only after the receiver safely accepts the event under its chosen persistence policy.
- Design for duplicate or out-of-order delivery without claiming an undocumented delivery guarantee.
- Record the receipt time and event time separately.
- Redact secrets and personal data from receiver logs.

Use the documented delivery search or count operations to investigate delivery failures.
A webhook ping sends data to the receiver. Do not run it without approval for that active test.
Do not create a public receiver or open a firewall merely to validate this skill.

## Troubleshooting

Start with the smallest failing component. Preserve the exact operation and sanitized response before changing code.

| Symptom | Checks | Safe next action |
| - | - | - |
| HTTP 401 | Host, token format, session, MFA, and credential lifecycle. | Repair configuration without printing the secret. |
| HTTP 403 | Tenant scope, role, `src_ips`, and supported feature access. | Ask the authorized operator to resolve access. |
| HTTP 404 | Exact source route, ID type, region, and parent scope. | Report a route conflict rather than probing guessed alternatives. |
| HTTP 400 | Required fields, conditional fields, body shape, and media type. | Correct the contract mismatch before another request. |
| HTTP 429 | Shared request budget, retries, polling, and `Retry-After`. | Reduce load and defer work within the deadline. |
| A switch or gateway is missing | Device type defaults and pagination. | Repeat only the corrected authorized listing. |
| Fewer rows than expected | Page metadata, total, filters, time bins, and search caps. | Report incompleteness until the missing range is explained. |
| Duplicate rows | Changing snapshots, overlapping windows, and natural keys. | Deduplicate only with a verified identity rule. |
| HTTP 200 with failed items | Per-item `success`, `error`, `reason`, or job target states. | Report partial failure and reconcile each target. |
| No command output | WebSocket host, subscription acknowledgement, channel, session, and device connectivity. | Report timeout or lost output, not success. |
| An old test result appears | Test ID, type, device, and timestamp correlation. | Reject the unrelated historical result. |
| A stale firmware version appears | Configured version versus observed running version. | Read device statistics or the approved running-version resolver. |
| A template change has no effect | Assignment, derived configuration, variables, and device overrides. | Locate the actual configuration owner before another write. |
| A capture is busy | Active capture scope and owner. | Ask for coordination rather than stopping it. |
| A capture download fails | URL expiry, destination validation, permissions, and media type. | Refresh through the documented listing if authorized. |
| A webhook signature fails | Raw body, secret, header version, and signature encoding. | Reject the request and inspect sanitized receiver evidence. |
| An SDK call raises `TypeError` | Installed version, module, and callable signature. | Correct the integration, not the API payload by guesswork. |
| A TLS request fails | Hostname, trust chain, proxy, and approved CA bundle. | Repair trust configuration. Keep certificate verification enabled. |

For Python runtime failures, use the workspace's debugger and diagnostics when available.
Do not add secret-bearing debug prints or run a destructive operation to reproduce a problem.
