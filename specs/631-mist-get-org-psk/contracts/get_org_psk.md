# Contract: GET /api/v1/orgs/{org_id}/psks/{psk_id}

**Feature**: 631-mist-get-org-psk
**operationId**: `getOrgPsk`
**Source**: `documentation/api/orgs/GET_orgs_org_id_psks_psk_id.md`

## HTTP Contract

| Aspect          | Value                                                      |
|-----------------|------------------------------------------------------------|
| Method          | `GET`                                                      |
| URL template    | `https://{MIST_HOST}/api/v1/orgs/{org_id}/psks/{psk_id}`   |
| Auth header     | `Authorization: Token {MIST_API_TOKEN}` (or `X-CSRFToken` cookie) |
| Content-Type    | Not applicable to request (no body). Response is `application/json`. |
| Request body    | None.                                                      |
| Pagination      | Not paginated (single-object response).                    |
| Rate limiting   | Standard Mist rate limits (5000 calls/hour per token).     |

### Path Parameters

| Name     | Type   | Required | Format | Description                              |
|----------|--------|----------|--------|------------------------------------------|
| `org_id` | string | Yes      | UUID   | Organization scope.                      |
| `psk_id` | string | Yes      | UUID   | PSK unique identifier.                   |

### Query Parameters

None.

### Headers

| Header          | Required | Purpose                                       |
|-----------------|----------|-----------------------------------------------|
| `Authorization` | Yes      | `Token {MIST_API_TOKEN}` from `.env`.         |
| `Accept`        | No       | Defaults to `application/json`.               |

## Response: 200 OK

Content-Type: `application/json`. The body is a single JSON object describing
one PSK. The full schema (verbatim from the enriched doc) is:

```json
{
  "type": "object",
  "properties": {
    "admin_sso_id":              { "type": "string",  "readOnly": true },
    "created_time":              { "type": "number",  "readOnly": true },
    "email":                     { "type": "string" },
    "expire_time":               { "type": ["integer","null"], "contentEncoding": "int32" },
    "expiry_notification_time":  { "type": "integer", "contentEncoding": "int32" },
    "id":                        { "type": "string",  "contentEncoding": "uuid", "readOnly": true },
    "mac":                       { "type": "string" },
    "macs":                      { "type": "array",   "items": { "type": "string" } },
    "max_usage":                 { "type": "integer", "contentEncoding": "int32", "default": 0 },
    "modified_time":             { "type": "number",  "readOnly": true },
    "name":                      { "type": "string" },
    "note":                      { "type": "string" },
    "notify_expiry":             { "type": "boolean", "default": false },
    "notify_on_create_or_edit":  { "type": "boolean" },
    "old_passphrase":            { "type": "string" },
    "org_id":                    { "type": "string",  "contentEncoding": "uuid", "readOnly": true },
    "passphrase":                { "type": "string",  "minLength": 8,  "maxLength": 64 },
    "role":                      { "type": "string",  "minLength": 0,  "maxLength": 32 },
    "site_id":                   { "type": "string",  "contentEncoding": "uuid", "readOnly": true },
    "ssid":                      { "type": "string" },
    "usage":                     { "type": "string",  "description": "enum: macs, multi, single" },
    "vlan_id":                   { "type": "object" }
  },
  "required": ["name", "passphrase", "ssid"],
  "description": "PSK"
}
```

### Example Response

```json
{
  "id":            "53f10664-3ce8-4c27-b382-0ef66432349f",
  "org_id":        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "site_id":       "441a1214-6928-442a-8e92-e1d34b8ec6a6",
  "name":          "guest-day",
  "ssid":          "Guest",
  "passphrase":    "welcome-2026",
  "usage":         "multi",
  "max_usage":     0,
  "expire_time":   1735689600,
  "notify_expiry": true,
  "created_time":  1706832000.0,
  "modified_time": 1706918400.0
}
```

## Error Responses

| Status | Meaning                                                     | MistHelper Handling |
|--------|-------------------------------------------------------------|---------------------|
| 400    | Bad Syntax (malformed UUID)                                 | Should not occur -- MistHelper validates UUID shape client-side before the call. If encountered, log `WARNING` with the operation name and return early (exit 0). |
| 401    | Unauthorized (bad / missing token)                          | Log `ERROR` "Authentication failed for getOrgPsk"; surface to the user with a "check MIST_API_TOKEN in .env" hint; exit non-zero via the top-level exception handler. |
| 403    | Permission Denied (token lacks org access)                  | Log `WARNING` "Permission denied for org %s"; return early (exit 0) so batch runs continue. |
| 404    | Not found (unknown org_id or psk_id)                        | Log `WARNING` "getOrgPsk returned 404 for psk %s in org %s; no data written"; return early (exit 0). Do NOT write an empty row to any backend. |
| 429    | Too Many Requests (5000 calls/hour threshold)               | Yield to the adaptive delay system driven by `delay_metrics.json` + `tuning_data.json`; the mistapi SDK retries automatically. Log `INFO` "Rate limit hit; backing off". |

## mistapi SDK Call

**Import path**: `mistapi.api.v1.orgs.psks`
**Function**: `getOrgPsk`

### Python Call Signature

```python
import mistapi
from mistapi.api.v1.orgs import psks as psks_module

# apisession is an authenticated mistapi.APISession created at MistHelper startup
response = psks_module.getOrgPsk(
    apisession,   # positional -- authenticated session
    org_id,       # positional -- string UUID
    psk_id,       # positional -- string UUID
)

# Extract payload -- response is a mistapi response wrapper; .data is the dict
psk_record = response.data
```

### Return Value

- **Type**: `mistapi` response wrapper.
- **`.data` attribute**: `dict` matching the 200-response schema above, or
  `None` / empty dict on error paths.
- **`.status_code` attribute**: integer HTTP status; MistHelper inspects only
  in the retry / adaptive-delay wiring, not in the menu method.

### Constitutional Constraints on Log Statements Around This Call

Per Constitution Principle V (Observability) and V + III combined for secret
handling:

- `logging.info("Fetching PSK detail for org %s psk %s", org_id, psk_id)`
  BEFORE the call.
- `logging.debug("PSK detail: id=%s name=%s ssid=%s usage=%s", ...)` AFTER
  the call. The `passphrase` and `old_passphrase` fields are EXCLUDED from
  every log line.
- No f-string log formatting; use `%s` placeholders so the logger's lazy
  formatting suppresses arguments below the configured level.
