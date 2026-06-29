# Endpoint Contract: getMspOrg

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/msps/GET_msps_msp_id_orgs_org_id.md`
**Date**: 2026-06-29

## HTTP Contract

| Attribute    | Value                                       |
|--------------|---------------------------------------------|
| **Method**   | `GET`                                       |
| **URL**      | `https://{mist_host}/api/v1/msps/{msp_id}/orgs/{org_id}` |
| **Auth**     | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**      | `MSPs Orgs`                                 |
| **operationId** | `getMspOrg`                              |

### Path Parameters

| Name     | Type          | Required | Description |
|----------|---------------|----------|-------------|
| `msp_id` | string (UUID) | Yes      | UUID of the Managed Service Provider that owns the org. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |
| `org_id` | string (UUID) | Yes      | UUID of the organization to read. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

None.

### Request Headers

| Header           | Value                | Notes |
|------------------|----------------------|-------|
| `Authorization`  | `Token <api_token>`  | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`         | `application/json`   | Default for mistapi SDK. |
| `User-Agent`     | `mistapi/<version>`  | Set by SDK. |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "msp_id": "b9d42c2e-88ee-41f8-b798-f009ce7fe909",
  "name": "Acme",
  "msp_name": "ACME-MSP",
  "msp_logo_url": "https://example.com/logo/b9d42c2e-88ee-41f8-b798-f009ce7fe909.jpeg",
  "alarmtemplate_id": "a1c2e3d4-5678-9abc-def0-123456789abc",
  "allow_mist": true,
  "orggroup_ids": [
    "11111111-2222-3333-4444-555555555555",
    "66666666-7777-8888-9999-aaaaaaaaaaaa"
  ],
  "session_expiry": 1440,
  "created_time": 1700000000,
  "modified_time": 1719600000
}
```

| Field              | Type                  | Description |
|--------------------|-----------------------|-------------|
| `id`               | string (UUID)         | Org UUID. Server-issued, read-only, globally unique. Used as MistHelper natural PK. |
| `msp_id`           | string (UUID)         | Owning MSP UUID. Read-only. |
| `name`             | string                | Org display name. Required by API. |
| `msp_name`         | string                | Owning MSP display name. Read-only. |
| `msp_logo_url`     | string                | URL of MSP-uploaded logo. Optional -- only present if uploaded. Read-only. |
| `alarmtemplate_id` | string (UUID) or null | Linked alarm template UUID, or null. |
| `allow_mist`       | boolean               | Whether Mist support can access this org. Default `true`. |
| `orggroup_ids`     | array of UUID strings | Org-group memberships. |
| `session_expiry`   | integer (minutes)     | Web UI session expiry. Range 10..20160. Default 1440. |
| `created_time`     | number (epoch s)      | Org creation time. Read-only. |
| `modified_time`    | number (epoch s)      | Last modification time. Read-only. |

The response carries exactly one JSON object (not a list, not paginated). The
`required` set per the OpenAPI schema is `["name"]`; all other fields may be
omitted by the server. MistHelper flattens the `orggroup_ids` array to a `;`-
joined TEXT column and converts `allow_mist` to a 0/1 INTEGER on write, per
the existing MistHelper conventions documented in
`specs/584-mist-get-msp-org/data-model.md`.

### Error Responses

| Status | Mist Description                                                   | MistHelper Handling |
|--------|--------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                         | Log `WARNING` ("Mist returned 400 -- check msp_id/org_id format"), no traceback, return early. |
| 401    | Unauthorized                                                       | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                  | Log `ERROR` ("Mist 403 -- token lacks read access to msp %s org %s", msp_id, org_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                     | Log `WARNING` ("No such MSP-managed org: msp %s org %s", msp_id, org_id). Treat as empty result and write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)       | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is
never included in any log message, even at `DEBUG`. The 404 case is the
documented gotcha: an `org_id` that exists but is not managed by the supplied
`msp_id` returns 404, not 403 -- MistHelper logs the WARNING and exits 0.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.msps import orgs as msps_orgs_module

apisession = mistapi.APISession(
    host=os.environ["MIST_HOST"],
    apitoken=os.environ["MIST_API_TOKEN"],
)
apisession.login()

response = msps_orgs_module.getMspOrg(
    apisession,
    msp_id="b9d42c2e-88ee-41f8-b798-f009ce7fe909",
    org_id="53f10664-3ce8-4c27-b382-0ef66432349f",
)

# Access the parsed body:
body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path (`/msps/{msp_id}/orgs/
  {org_id}` -> `mistapi.api.v1.msps.orgs`). The function name matches the
  OpenAPI operationId exactly (`getMspOrg`).
- Positional argument order in the mistapi SDK is consistently
  `(apisession, *path_params_in_url_order, **query_params)`. For this endpoint
  that means `(apisession, msp_id, org_id)` -- the same order in which the
  identifiers appear in the URL. Passing them as keyword arguments (shown
  above) is preferred for readability.
- `response.data` is `None` only when the HTTP response had no body (rare for a
  200). MistHelper normalizes this to `{}` before flattening, so downstream
  flattener helpers never see `None`.
- This endpoint takes **no** query parameters, so no `**kwargs` are accepted
  beyond `apisession`, `msp_id`, and `org_id`. Adding unrecognized keyword
  arguments raises `TypeError` from the SDK.
- Final SDK signature verification at implementation time:
  `python -c "from mistapi.api.v1.msps import orgs; help(orgs.getMspOrg)"`.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No `limit`
or `page` parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No endpoint-
specific tuning required for this contract because each invocation is a single
small GET.
