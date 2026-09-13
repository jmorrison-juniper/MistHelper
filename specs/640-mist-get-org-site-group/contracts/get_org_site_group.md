# Contract: getOrgSiteGroup

**Feature**: `640-mist-get-org-site-group`
**operationId**: `getOrgSiteGroup`
**Source**: `documentation/api/orgs/GET_orgs_org_id_sitegroups_sitegroup_id.md`

## HTTP Contract

| Attribute      | Value                                                     |
|----------------|-----------------------------------------------------------|
| Method         | `GET`                                                     |
| URL Template   | `https://{MIST_HOST}/api/v1/orgs/{org_id}/sitegroups/{sitegroup_id}` |
| Auth Header    | `Authorization: Token {MIST_API_TOKEN}`                   |
| Alt Auth       | `X-CSRFToken` cookie (browser session; not used by MistHelper) |
| Accept Header  | `application/json`                                        |
| Body           | None                                                      |
| Pagination     | None -- single-object response                            |
| Rate Limit     | 5000 API calls per hour per token (429 on exceed)         |

### Path Parameters

| Name           | Type   | Required | Format | Description                             |
|----------------|--------|----------|--------|-----------------------------------------|
| `org_id`       | string | Yes      | UUID   | Owning organization identifier.         |
| `sitegroup_id` | string | Yes      | UUID   | Site group identifier within the org.   |

### Query Parameters

None.

### Request Headers (added by mistapi.APISession)

| Header          | Value                             | Notes                     |
|-----------------|-----------------------------------|---------------------------|
| `Authorization` | `Token <token>`                   | Loaded from `.env`.       |
| `Accept`        | `application/json`                | SDK default.              |
| `User-Agent`    | `mistapi-python/<version>`        | SDK default.              |

## 200 Response Schema (Success)

Content-Type: `application/json`. Body is a single JSON object (not an array).

```json
{
  "type": "object",
  "properties": {
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": ["53f10664-3ce8-4c27-b382-0ef66432349f"]
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": ["a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"]
    },
    "site_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "Site UUIDs that belong to this group."
    }
  },
  "required": ["name"],
  "description": "Sites Group"
}
```

### Example 200 Body

```json
{
  "created_time": 1710000000.0,
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "modified_time": 1720000000.0,
  "name": "Retail-East",
  "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "site_ids": [
    "11111111-1111-1111-1111-111111111111",
    "22222222-2222-2222-2222-222222222222"
  ]
}
```

## Error Responses

| Status | Meaning                             | MistHelper Handling                                                                                       |
|--------|-------------------------------------|-----------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax                          | `logging.warning(...)`; return early; no traceback.                                                        |
| 401    | Unauthorized (bad or missing token) | `logging.error("Unauthorized -- verify MIST_API_TOKEN in .env")`; return early. Token is never logged.    |
| 403    | Permission Denied                   | `logging.warning("Permission denied for org %s -- token lacks read scope", org_id)`; return early.        |
| 404    | Not found (unknown org or group)    | `logging.warning("Site group %s not found in org %s", sitegroup_id, org_id)`; return early.               |
| 429    | Rate limit exceeded                 | Adaptive back-off in mistapi.APISession handles retry per delay_metrics.json / tuning_data.json. If retries exhausted, `logging.error(...)`; return early. |
| 5xx    | Server-side failure                 | `logging.exception("Unexpected server error from Mist")`; return early. Full traceback logged (safe -- no secrets in URL / headers as logged). |

No error branch raises to the caller; every branch returns cleanly so the
menu loop can accept the next selection without a traceback.

## mistapi Python Call Signature

Module import path (top of MistHelper.py, already present):

```python
import mistapi
import mistapi.api.v1.orgs.sitegroups
```

Call site inside `OrgTemplateExportUtils.export_org_site_group()`:

```python
response = mistapi.api.v1.orgs.sitegroups.getOrgSiteGroup(  # sole permitted Mist transport
    self.mist_session,                                       # APISession from .env
    org_id,                                                  # validated UUID
    sitegroup_id,                                            # validated UUID
)                                                            # returns mistapi.APIResponse
payload = response.data or {}                                # dict on 200; {} on empty / error
```

Return type: `mistapi.APIResponse` with attributes:

| Attribute       | Type    | Description                                       |
|-----------------|---------|---------------------------------------------------|
| `data`          | dict    | The 200 response body (empty dict on non-200).    |
| `status_code`   | int     | HTTP status code.                                 |
| `raw_data`      | str     | Raw response text (used only for debug traces).   |
| `headers`       | dict    | Response headers (used for rate-limit metrics).   |

The single-object shape means MistHelper wraps `payload` in a one-element
list before passing to `DataExporter.write_with_format_selection()` so the
exporter's row-oriented API contract is honored.

## Contract Test Anchors (for Phase 2 tasks)

- Given a 200 response with `site_ids: []`, the flattened row has
  `site_ids=""` and `site_count=0`.
- Given a 200 response with `site_ids: [uuid1, uuid2]`, the flattened row
  has `site_ids="uuid1;uuid2"` and `site_count=2`.
- Given a 404 response, the method returns without writing any row and
  logs exactly one WARNING line naming the missing `sitegroup_id`.
- Given a 429 response after retry exhaustion, the method returns without
  writing any row and logs exactly one ERROR line; the API token never
  appears in the log output.
- Repeated invocation with the same `id` upserts (no duplicate row in
  `org_site_groups`).
