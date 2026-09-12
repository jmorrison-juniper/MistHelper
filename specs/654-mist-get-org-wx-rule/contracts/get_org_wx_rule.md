# Endpoint Contract: getOrgWxRule

**Feature**: 654-mist-get-org-wx-rule
**Source**: `documentation/api/orgs/GET_orgs_org_id_wxrules_wxrule_id.md`
**operationId**: `getOrgWxRule`

## HTTP Contract

| Field                | Value                                                          |
|----------------------|----------------------------------------------------------------|
| Method               | `GET`                                                          |
| URL template         | `/api/v1/orgs/{org_id}/wxrules/{wxrule_id}`                    |
| Full URL example     | `https://api.mist.com/api/v1/orgs/a97c1b22-a4e9-411e-9bfd-d8695a0f9e61/wxrules/53f10664-3ce8-4c27-b382-0ef66432349f` |
| Request body         | None                                                           |
| Pagination           | Not paginated                                                  |
| Rate limiting        | Standard Mist API limits (5000 calls/hour per token)           |

### Required Path Parameters

| Name        | Type          | Required | Description                                            |
|-------------|---------------|----------|--------------------------------------------------------|
| `org_id`    | string (uuid) | Yes      | Owning organization UUID.                              |
| `wxrule_id` | string (uuid) | Yes      | Unique WxLAN rule id inside that organization.         |

### Query Parameters

None.

### Required Headers

| Header          | Value                                             |
|-----------------|---------------------------------------------------|
| `Authorization` | `Token <api_token>` -- loaded from `.env` by mistapi. Alternative: session cookie + `X-CSRFToken` header. |
| `Accept`        | `application/json` (mistapi sets this).            |
| `Content-Type`  | Not required for GET.                             |

## 200 Success Response Schema

Content type: `application/json`. Body is a single `Wrule` object (not an array).

Required fields (per OpenAPI): `order`, `src_wxtags`.

```json
{
  "type": "object",
  "properties": {
    "action":           { "type": "string",  "enum": ["allow", "block"] },
    "apply_tags":       { "type": "array",   "items": { "type": "string" } },
    "blocked_apps":     { "type": "array",   "items": { "type": "string" } },
    "created_time":     { "type": "number",  "readOnly": true },
    "dst_allow_wxtags": { "type": "array",   "items": { "type": "string" } },
    "dst_deny_wxtags":  { "type": "array",   "items": { "type": "string" } },
    "dst_wxtags":       { "type": "array",   "items": { "type": "string" } },
    "enabled":          { "type": "boolean", "default": true },
    "for_site":         { "type": "boolean", "readOnly": true },
    "id":               { "type": "string",  "format": "uuid", "readOnly": true },
    "modified_time":    { "type": "number",  "readOnly": true },
    "order":            { "type": "integer", "minimum": -1, "description": "-1 means LAST" },
    "org_id":           { "type": "string",  "format": "uuid", "readOnly": true },
    "site_id":          { "type": "string",  "format": "uuid", "readOnly": true },
    "src_wxtags":       { "type": "array",   "items": { "type": "string" } },
    "template_id":      { "type": "string",  "format": "uuid" }
  },
  "required": ["order", "src_wxtags"]
}
```

### Example 200 Body

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "site_id": "441a1214-6928-442a-8e92-e1d34b8ec6a6",
  "template_id": "6aa54cbd-e039-4878-846a-04f270de8a5c",
  "for_site": false,
  "enabled": true,
  "order": 1,
  "action": "allow",
  "apply_tags": [],
  "blocked_apps": ["mist", "all-videos"],
  "src_wxtags": [
    "8bfc2490-d726-3587-038d-cb2e71bd2330",
    "3aa8e73f-9f46-d827-8d6a-567bb7e67fc9"
  ],
  "dst_wxtags": [],
  "dst_allow_wxtags": [
    "fff34466-eec0-3756-6765-381c728a6037"
  ],
  "dst_deny_wxtags": [],
  "created_time": 1698000000.0,
  "modified_time": 1698000000.0
}
```

## Error Responses and MistHelper Handling

| Status | Meaning                                       | MistHelper Behavior                                                                                              |
|--------|-----------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax                                    | `logging.error("400 Bad Syntax from getOrgWxRule for rule %s", wxrule_id)`; write no rows; return 0.             |
| 401    | Unauthorized (missing/invalid token)          | `logging.error("401 Unauthorized -- check MIST_API_TOKEN in .env")`; return 0. Never log token contents.          |
| 403    | Permission Denied (token lacks org scope)     | `logging.warning("403 Permission denied for org %s / rule %s", org_id, wxrule_id)`; return 0.                    |
| 404    | Not Found (rule id or org id unknown)         | `logging.warning("WxRule %s not found in org %s", wxrule_id, org_id)`; write no rows; return 0.                  |
| 429    | Rate Limit (5000 calls/hour)                  | Adaptive delay system (`delay_metrics.json`, `tuning_data.json`) sleeps and retries per existing behavior.       |
| 5xx    | Upstream Mist Cloud error                     | `logging.exception("Unexpected error calling getOrgWxRule")`; retry per mistapi defaults; then return 0.         |

All error paths respect the constitution: no traceback leaves the method under
normal operation, and no token or full request URL is written to any log stream.

## Exact mistapi Python Call Signature

```python
import mistapi                                                                   # Root of the SDK.
import mistapi.api.v1.orgs.wxrules                                               # Explicit submodule import.

api_response: mistapi.APIResponse = mistapi.api.v1.orgs.wxrules.getOrgWxRule(   # Single positional call.
    apisession,                                                                  # Authenticated APISession object.
    org_id,                                                                      # Path param 1: owning org UUID.
    wxrule_id,                                                                   # Path param 2: rule UUID.
)

parsed_body: dict = api_response.data or {}                                     # dict, or {} on 404 / empty.
http_status: int = api_response.status_code                                     # 200 on success; 4xx/5xx otherwise.
```

Notes:
- `apisession` is a `mistapi.APISession` instance already constructed by MistHelper
  at startup and cached on `self.apisession` for `OrgExportUtils`.
- Both `org_id` and `wxrule_id` MUST be lowercase 36-character UUID strings; the
  menu method validates them with the shared UUID regex before this call.
- The SDK auto-injects the `Authorization` header from the session's stored token.
- The SDK exposes no dedicated 404 exception; callers inspect
  `api_response.status_code` and treat `>=400` as failure.
