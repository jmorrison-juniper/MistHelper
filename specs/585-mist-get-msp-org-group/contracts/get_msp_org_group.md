# Contract: getMspOrgGroup

**Feature**: 585-mist-get-msp-org-group
**Source**: `documentation/api/msps/GET_msps_msp_id_orggroups_orggroup_id.md`
**OpenAPI tag**: `MSPs Org Groups`

This document is the authoritative HTTP and SDK contract that the menu 96
implementation must conform to.

---

## HTTP Contract

| Field | Value |
|-------|-------|
| **Method** | `GET` |
| **URL template** | `https://{MIST_HOST}/api/v1/msps/{msp_id}/orggroups/{orggroup_id}` |
| **Pagination** | Not paginated (single record) |
| **Idempotent** | Yes (safe GET) |

### Path Parameters (required)

| Name | Type | Required | Format | Description |
|------|------|----------|--------|-------------|
| `msp_id` | string | yes | UUID v4 (`8-4-4-4-12` hex) | UUID of the MSP that owns the org group |
| `orggroup_id` | string | yes | UUID v4 | UUID of the org group to read |

### Query Parameters

None. The endpoint accepts no query string.

### Required Request Headers

| Header | Value | Notes |
|--------|-------|-------|
| `Authorization` | `Token {MIST_API_TOKEN}` | Issued by the Mist UI; loaded from `.env`; never logged |
| `Accept` | `application/json` | Set by the mistapi SDK automatically |

A session cookie + `X-CSRFToken` header is the only alternative authentication path
(per the enriched docs); MistHelper always uses the API-token path via
`mistapi.APISession`.

### Request Body

None. GET requests carry no body.

---

## Success Response (HTTP 200)

Returns a single JSON object representing the org group. Schema:

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
    "msp_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": ["b9d42c2e-88ee-41f8-b798-f009ce7fe909"]
    },
    "name": {
      "type": "string"
    },
    "org_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      }
    }
  },
  "required": ["name"],
  "description": "Organizations Group"
}
```

### Example 200 Response

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "msp_id": "b9d42c2e-88ee-41f8-b798-f009ce7fe909",
  "name": "North America Region",
  "org_ids": [
    "11111111-1111-1111-1111-111111111111",
    "22222222-2222-2222-2222-222222222222",
    "33333333-3333-3333-3333-333333333333",
    "44444444-4444-4444-4444-444444444444"
  ],
  "created_time": 1717200000.0,
  "modified_time": 1748736000.0
}
```

### Field-Level Notes

- `id`, `msp_id`, `created_time`, `modified_time` are `readOnly` (server-issued); they
  are persisted but never sent in any write op (write ops are out of scope here).
- `name` is the only `required` field per the schema; MistHelper does not enforce
  presence locally because the server never returns 200 without it.
- `org_ids` may be absent or empty; the menu method treats `payload.get("org_ids") or
  []` to normalize.

---

## Error Responses

| Status | Description (per OpenAPI) | MistHelper Handling |
|--------|---------------------------|---------------------|
| `400` | Bad Syntax | Logged at `ERROR` with the SDK's exception message; method returns without writing. UUID validation in the menu method makes this status unlikely. |
| `401` | Unauthorized | Logged at `ERROR` ("API token rejected -- check MIST_API_TOKEN in .env"); method returns. Token value is never logged. |
| `403` | Permission Denied | Logged at `WARNING` ("MSP read scope missing for this token"); method returns 0. |
| `404` | Not found. The API endpoint doesn't exist or resource doesn't exist | Logged at `WARNING` ("MSP %s / org group %s not found", redacted); method returns 0. No traceback. |
| `429` | Too Many Requests (5000 calls/hour threshold) | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) kicks in automatically; mistapi retries with back-off; menu method does not need explicit handling. |

All error logs use ASCII text and `%s` formatting; the API token and full request URL
are never emitted.

---

## mistapi SDK Call Signature

The exact Python call site in the new menu method:

```python
import mistapi                                                  # Already imported at the top of MistHelper.py

response = mistapi.api.v1.msps.org_groups.getMspOrgGroup(       # Module path mirrors the URL path (snake_case for compound segments)
    self.apisession,                                            # Authenticated APISession from .env credentials
    msp_id,                                                     # Path param 1 -- validated UUID
    orggroup_id,                                                # Path param 2 -- validated UUID
)
payload = response.data                                         # Parsed JSON body (dict matching the schema above)
```

- Return type: `mistapi.APIResponse`
- Result accessor: `response.data` (dict on 200; may be `{}` on edge cases)
- No keyword arguments, no `query` dict, no `body` dict (the SDK signature mirrors the
  zero-query-param contract of this endpoint).

---

## Conformance Checklist

The implementation PR for menu 96 must demonstrate:

- [ ] The single SDK call uses the exact signature shown above.
- [ ] Both path params are validated as UUIDs before the call.
- [ ] All four error status codes are logged at the documented severity level with no
      token leak.
- [ ] The 200 response is flattened into one `msp_org_groups` row plus zero-or-more
      `msp_org_group_members` rows.
- [ ] `DataExporter.write_with_format_selection(... api_function_name='getMspOrgGroup')`
      is invoked for each output table.
- [ ] The `ENDPOINT_PRIMARY_KEY_STRATEGIES['getMspOrgGroup']` entry (see
      `data-model.md`) is present and matches this contract.
