# Portal API Contract: Multi-site WebSocket batches

**Issue**: #4259

**Status**: Proposed additive contract

All routes use the existing `/api/websockets` prefix.
Use the current portal authentication, authorization, and request protections.
Resolve the organization from the authenticated portal configuration.
Never return API tokens, WebSocket addresses, raw upstream errors, or private file paths.

## Existing Route Compatibility

| Existing route | Preserved behavior |
| - | - |
| `GET /api/websockets/catalog` | Current catalog and safety flags |
| `GET /api/websockets/sessions` | Current session list and limits |
| `POST /api/websockets/sessions` | Current Single Site start body and validation |
| `GET /api/websockets/sessions/{session_id}/messages` | Current cursor and gap behavior |
| `POST /api/websockets/sessions/{session_id}/stop` | Current asynchronous stop |
| `DELETE /api/websockets/sessions/{session_id}` | Current ended-session deletion |
| `GET /api/websockets/sessions/{session_id}/download` | Current Single Site JSONL download |
| `POST /api/websockets/sessions/{session_id}/input` | Current interactive terminal input |
| `GET /api/websockets/sessions/{session_id}/terminal` | Current terminal history |
| `POST /api/websockets/sessions/{session_id}/resize` | Current interactive resize |
| Existing per-site device, client, map, asset, and SDK-client routes | Current request and response shapes |
| `GET /api/websockets/mxedges` | Current organization or site picker |

Do not add batch keys to the existing Single Site start body.
Its validator rejects unknown keys.
Do not change the current repeatable channel maximum of 10 paths.
The Single Site site picker may continue to use `/api/operations/sites`.

Batch parents appear as one entry in the shared session list.
Only batch entries carry additive `mode` and `batch` fields.
Single Site entries retain their current payload.

## 1. Create a Batch Preview

`POST /api/websockets/batches/previews`

Return `201` after complete validated discovery.
This call performs read-only discovery and starts no stream or utility.

### Request fields

| Field | Required | Contract |
| - | - | - |
| `operation` | Yes | Object with existing catalog `kind` and `key` |
| `selection` | Yes | Site and resource selectors described below |
| `parameters` | Yes | Object containing only declared catalog parameters |
| `commands` | Shell only | Exact ordered command list |
| `scope_revision` | Yes | Nonnegative browser revision |

A selector has `mode: all` or `mode: selected`.
A selected site selector includes `ids`.
A selected resource selector includes explicit identity objects in `targets`.
Each identity object contains its site and required device or map parent.
Reject an empty selected list.
Reject foreign, unknown, duplicate-conflicting, or incompatible identity objects.
Deduplicate exact repeated identities.

Example for a site channel:

```json
{
  "operation": {"kind": "channel", "key": "site.stats.devices"},
  "selection": {
    "sites": {"mode": "selected", "ids": ["11111111-1111-4111-8111-111111111111"]}
  },
  "parameters": {},
  "scope_revision": 4
}
```

For device and client operations, `selection.resources` contains the corresponding selector.
Client identities require verified device or map association.
For a shell, resolve `all` into explicit device identities for operator review.
Do not start any target before the operator reviews the resolved list.
Organization-only operations omit the site selector and produce one organization target.

### Response fields

| Field | Contract |
| - | - |
| `preview_id` | Opaque server reference |
| `expires_at` | UTC deadline |
| `scope_revision` | Exact request revision |
| `operation` | Catalog identity and safe display metadata |
| `targets` | Complete frozen target list |
| `target_count` | Exact admitted candidate count |
| `excluded` | Safe counts and reasons for incompatible candidates |
| `confirmation` | Required phrase, safety class, and confirmation-required flag |
| `limits` | Target cap, concurrency range, shell byte limits, and disk cap |

No command text or fingerprint needs to return in the response.
The browser already holds the command list for the review panel.
The server retains its private exact copy.
If any requested discovery scope fails, reject the preview.
Do not return a usable partial preview for an `all` selection.

## 2. Start the Batch

`POST /api/websockets/batches`

Return `201` with the public session payload.

```json
{
  "preview_id": "server-issued-preview",
  "confirmation": "RUN 3 TARGETS",
  "concurrency": 3,
  "output": {"mode": "both", "group_by": "device"}
}
```

The `confirmation` example applies to a change or shell batch.
Require the exact phrase `RUN <target_count> TARGETS`.
Bind that phrase to the stored operation, parameters, ordered commands, and target set.
Read-only operations omit confirmation when the catalog permits it.
Always bind the preview to the exact execution snapshot.

Reject all unknown request keys.
Do not accept commands, targets, paths, or parameters at this endpoint.
A changed execution request requires a new preview.
Validate the preview, typed word, lock state, resource limits, and public session capacity atomically.
Consume the preview only when admission succeeds.
Allow no automatic retry after an ambiguous successful admission.
An explicit retry with a consumed preview returns `preview_consumed`.

### Additive batch session fields

```json
{
  "session_id": "public-parent-id",
  "mode": "multi_site",
  "batch": {
    "status": "running",
    "target_count": 3,
    "concurrency": 3,
    "counts": {"queued": 1, "running": 1, "completed": 1, "stopped": 0, "failed": 0},
    "artifact_status": "writing"
  }
}
```

The real response also retains the established session lifecycle fields.
Children do not appear as additional public sessions.

## 3. Read Batch Progress

`GET /api/websockets/batches/{session_id}`

Return `200` with the existing session payload and additive batch summary.
Mark the parent read time through the existing session manager.
Return `not_found` for an absent or expired session.
Return `not_batch` when the identifier belongs to Single Site work.

`GET /api/websockets/batches/{session_id}/targets?after=0&limit=100`

Return `200` with:

- `targets`: ordered execution records from [data-model.md](../data-model.md).
- `next_after`: next integer target-list cursor.
- `complete`: true after the last target-list page.
- `counts`: a current summary with all five target states.

Use stable preview order for this cursor.
Clamp the requested page size to 1 through 500.
State updates do not reorder targets.

Use the existing session messages route for output polling.
Keep its existing outer envelope, sequence cursor, limit clamp, and gap notice.
Batch message payloads contain the result envelope from the data model.
Every output, target error, status, and outcome carries target identity.
Do not put private child session objects in a response.

## 4. Stop and Delete

Use `POST /api/websockets/sessions/{session_id}/stop` for the parent.
Return the current payload with `202`, as the existing route does.
Repeated stop requests remain safe.
Atomically stop queued dispatch before signaling active targets.
Keep successful output and completed target states.
Apply current idle, lifetime, and stuck-stop cleanup.

Use `DELETE /api/websockets/sessions/{session_id}` after the batch ends.
Keep the existing `session_live` refusal for live sessions.
Remove the batch artifact tree through the safe session boundary.
If cleanup fails, retain a cleanup error record for retry.
Do not claim that files were removed when removal failed.

Batch shells reject input, resize, and interactive terminal requests with `not_terminal`, status `409`.
Single Site terminal behavior remains unchanged.

## 5. Downloads and Manifest

`GET /api/websockets/batches/{session_id}/artifacts`

Return `200` with artifact status, expiry, partial flag, and safe file manifest.
The manifest includes one outcome per target.

`GET /api/websockets/sessions/{session_id}/download`

For a batch, return redacted result envelopes as JSONL.
The default Single Site behavior remains unchanged.
For a grouped-only batch, merge the saved group records by parent sequence.
Do not create an unrequested permanent combined file.

`GET /api/websockets/batches/{session_id}/download?format=zip`

Return the selected saved layout and manifest as an archive.
Allow only `format=zip`.
Use `application/zip` and a server-created attachment name.
Return `artifact_not_ready`, status `409`, until the batch ends.
The manifest and combined session download can expose a consistent partial snapshot while the batch runs.
Capture the snapshot's last sequence before streaming it.
Do not hold the manager lock while streaming.

Archive entries contain safe relative paths only.
Do not accept a path or filename query parameter.
Refuse downloads after session expiry.
Pin files during an active response, then release the pin for cleanup.
Bound a download pin to the response deadline.

## Error Contract

Preserve the existing shape: `{"error": "Plain message.", "code": "stable_code"}`.
Add only safe context fields such as `field`, target identity, or an upstream status integer.

| Code | HTTP status | Meaning |
| - | - | - |
| `bad_request` | 400 | Invalid field, scope, parameter, selector, or command |
| `unknown_key` | 404 | Unknown catalog operation |
| `locked` | 403 | Existing feature lock |
| `confirmation` | 403 | Missing or incorrect typed word |
| `preview_expired` | 409 | Preview expired or invalidated |
| `preview_consumed` | 409 | Admission already used the preview |
| `preview_scope` | 403 | Authorization or snapshot binding differs |
| `target_limit` | 413 | Resolved target set exceeds 1000 |
| `limit_reached` | 429 | Current public session capacity is full |
| `picker_request_failed` | 502 | Mist refused discovery |
| `picker_service_failed` | 503 | Mist or SDK discovery failed |
| `picker_incomplete` | 503 | Discovery cannot prove every page |
| `not_batch` | 409 | Session is not a batch |
| `artifact_not_ready` | 409 | Final archive is not ready |
| `output_failed` | 507 | Required artifact storage failed |
| `not_found` | 404 | Session is unknown or expired |

Register new codes explicitly in the existing error-status mapping.
Do not change the status of an existing code.
Target failures after admission appear in progress and result records, not as a failed start response.
Keep the Single Site device-name confirmation unchanged.

Set channel concurrency to one because one connection multiplexes its target paths.
Reject an explicit channel concurrency above one.
Allow utility and shell batches to use concurrency one through five, with a default of three.
Show the effective value in the preview.
