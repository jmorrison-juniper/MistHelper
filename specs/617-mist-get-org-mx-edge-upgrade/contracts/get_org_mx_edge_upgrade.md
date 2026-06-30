# Contract: getOrgMxEdgeUpgrade

Phase 1 endpoint contract for the new MistHelper menu item. This document
is the authoritative HTTP + SDK contract that the implementation in
`MistHelper.py` and any future tests must conform to.

---

## 1. HTTP Contract

| Field           | Value                                                       |
|-----------------|-------------------------------------------------------------|
| **Method**      | `GET`                                                       |
| **URL template**| `https://{MIST_HOST}/api/v1/orgs/{org_id}/mxedges/upgrade/{upgrade_id}` |
| **Auth header** | `Authorization: Token {MIST_API_TOKEN}`                     |
| **Accept**      | `application/json`                                          |
| **Request body**| (none)                                                      |

### Path parameters

| Name         | Type | Required | Format       | Description                                       |
|--------------|------|----------|--------------|---------------------------------------------------|
| `org_id`     | str  | yes      | UUID v4      | Mist organization UUID. From user prompt or `.env`. |
| `upgrade_id` | str  | yes      | UUID v4      | UUID of the Mist Edge upgrade job to inspect.       |

### Query parameters

_None._

### Headers (set by mistapi SDK -- not user-supplied)

- `Authorization: Token <api_token>` (from `MIST_API_TOKEN`)
- `User-Agent: mistapi/<version>`
- `Accept: application/json`

The MistHelper code never composes the URL or headers by hand; the
`mistapi.APISession` object handles transport.

---

## 2. Success Response

### Status: `200 OK`

The response body is a single JSON object describing one Mist Edge upgrade
job. The shape below is reconstructed from the parallel write endpoints
(`cancelOrgMxEdgeUpgrade`, `updateOrgMxEdgeUpgrade`) documented in
`documentation/api/orgs/SDK_cancelOrgMxEdgeUpgrade.md` and
`documentation/api/orgs/SDK_updateOrgMxEdgeUpgrade.md`, plus the Juniper
public API reference page at
`https://www.juniper.net/documentation/us/en/software/mist/api/http/api/utilities/upgrade/get-org-mx-edge-upgrade`.

```json
{
  "id": "8f3a9c1d-1234-4abc-9def-1234abcd0001",
  "target_version": "4.2.31337",
  "status": "inprogress",
  "strategy": "serial",
  "created_time": 1751289600,
  "modified_time": 1751289660,
  "start_time": 1751289610,
  "end_time": null,
  "progress": [
    {
      "mxedge_id": "aaaa1111-2222-3333-4444-555566667777",
      "name": "mxedge-hq-01",
      "current_version": "4.2.31000",
      "status": "completed",
      "progress": 100,
      "start_time": 1751289611,
      "end_time": 1751289640,
      "error": null
    },
    {
      "mxedge_id": "bbbb2222-3333-4444-5555-666677778888",
      "name": "mxedge-hq-02",
      "current_version": "4.2.31000",
      "status": "upgrading",
      "progress": 42,
      "start_time": 1751289642,
      "end_time": null,
      "error": null
    }
  ]
}
```

### Top-level fields

| Field            | JSON Type        | Description                                                    |
|------------------|------------------|----------------------------------------------------------------|
| `id`             | string (UUID)    | Upgrade job UUID (matches `upgrade_id` path param).            |
| `target_version` | string           | Firmware version this job upgrades to.                         |
| `status`         | string           | Job-level status: `created`, `inprogress`, `completed`, `cancelled`, `failed`. |
| `strategy`       | string           | Roll-out strategy: `serial`, `parallel`, or vendor-specific.   |
| `created_time`   | integer (epoch s)| When the job record was created.                               |
| `modified_time`  | integer (epoch s)| When the job was last updated server-side.                     |
| `start_time`     | integer (epoch s)| When execution began (NULL until kicked off).                  |
| `end_time`       | integer (epoch s)| When execution finished (NULL while in-progress).              |
| `progress`       | array of object  | Per-Mist-Edge progress entries (see below). May be empty.      |

### `progress[i]` object fields

| Field             | JSON Type         | Description                                                       |
|-------------------|-------------------|-------------------------------------------------------------------|
| `mxedge_id`       | string (UUID)     | Mist Edge UUID this slice describes.                              |
| `name`            | string            | Human-readable hostname/label for the edge.                       |
| `current_version` | string            | Firmware currently installed on this edge.                        |
| `status`          | string            | Per-edge status: `pending`, `downloading`, `upgrading`, `completed`, `failed`. |
| `progress`        | integer (0-100)   | Completion percentage on this edge.                               |
| `start_time`      | integer (epoch s) | When this edge began its slice.                                   |
| `end_time`        | integer (epoch s) | When this edge finished its slice.                                |
| `error`           | string or null    | Plain-English error if `status="failed"`; otherwise `null`.       |

Unknown fields in either layer are logged at DEBUG and ignored. Missing
fields fall back to `None` in the flattener (`dict.get(...)`).

---

## 3. Error Responses

| Status | Mist Cause                                          | MistHelper Handling                                                                 |
|--------|-----------------------------------------------------|-------------------------------------------------------------------------------------|
| 401    | Missing / invalid API token                         | Log `ERROR` "Authentication failed -- check MIST_API_TOKEN in .env"; return 2.       |
| 403    | Token lacks read permission for the requested org   | Log `ERROR` "Authorization denied for org %s"; return 2.                            |
| 404    | `org_id` or `upgrade_id` does not exist             | Log `WARNING` "Upgrade %s not found in org %s"; write zero rows; return 0.          |
| 429    | Rate limit exceeded                                 | Adaptive delay system retries automatically via `delay_metrics.json` plumbing.       |
| 5xx    | Mist API transient failure                          | mistapi SDK retries per its built-in policy; MistHelper logs the exception and returns 3. |

No traceback is ever propagated to the user; `safe_input()` plus
`logging.exception(...)` keep the CLI calm and informative even under
upstream failure.

---

## 4. Exact mistapi Python Call Signature

The MistHelper code calls the SDK exactly once per menu invocation:

```python
import mistapi
from mistapi.api.v1.orgs import mxedges  # Module that owns the upgrade endpoints

# self.session is a mistapi.APISession built once at MistHelper startup.
response = mxedges.getOrgMxEdgeUpgrade(self.session, org_id, upgrade_id)

# response is a mistapi.__api_response.APIResponse.
upgrade_payload: dict = response.data or {}
```

### Signature reference

```python
mistapi.api.v1.orgs.mxedges.getOrgMxEdgeUpgrade(
    mist_session: mistapi.__api_session.APISession,
    org_id: str,
    upgrade_id: str,
) -> mistapi.__api_response.APIResponse
```

This mirrors the documented signatures of the parallel write operations in
the same module:

- `cancelOrgMxEdgeUpgrade(mist_session, org_id, upgrade_id)` -- see
  `documentation/api/orgs/SDK_cancelOrgMxEdgeUpgrade.md`.
- `updateOrgMxEdgeUpgrade(mist_session, org_id, upgrade_id, body)` -- see
  `documentation/api/orgs/SDK_updateOrgMxEdgeUpgrade.md`.

The `APIResponse` object exposes `.data` (the deserialized JSON body),
`.status_code`, `.headers`, and `.next` (None for non-paginated GETs --
this endpoint never paginates because it returns a single object). The
flattener consumes `.data` only.

---

## 5. Rate limiting & retries

Standard Mist API rate limits apply. MistHelper's adaptive delay system
(metrics file `delay_metrics.json`, tuning file `tuning_data.json`) governs
back-off per endpoint. `--fast` raises concurrency and lowers retries but
is safe for this single-object GET because the call is idempotent. No
special tuning is required for this endpoint.

---

## 6. Security

- The API token is read from `.env` at MistHelper startup and held in the
  `APISession` object. The new method never references the token directly.
- Neither the token, nor the fully composed URL, nor any header is emitted
  to logs.
- The two user-supplied UUIDs are logged at INFO so the audit trail
  identifies which job was inspected.
