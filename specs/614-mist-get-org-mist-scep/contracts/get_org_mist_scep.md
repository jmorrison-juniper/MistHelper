# Endpoint Contract: getOrgMistScep

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_setting_mist_scep.md`
**Date**: 2026-06-30

## HTTP Contract

| Attribute       | Value                                                          |
|-----------------|----------------------------------------------------------------|
| **Method**      | `GET`                                                          |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/setting/mist_scep`   |
| **Auth**        | `Authorization: Token {api_token}` header (injected automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs SCEP`                                                    |
| **operationId** | `getOrgMistScep`                                               |

### Path Parameters

| Name     | Type          | Required | Description                                                              |
|----------|---------------|----------|--------------------------------------------------------------------------|
| `org_id` | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

_None._ This endpoint accepts no query parameters.

### Request Headers

| Header           | Value                  | Notes                                                            |
|------------------|------------------------|------------------------------------------------------------------|
| `Authorization`  | `Token <api_token>`    | Injected by `mistapi.APISession` from `.env`. Never logged.      |
| `Accept`         | `application/json`     | Default for mistapi SDK.                                         |
| `User-Agent`     | `mistapi/<version>`    | Set by SDK.                                                      |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

```json
{
  "cert_providers": ["intune", "jamf"],
  "enabled": true,
  "intune_scep_url": "https://scep.mistsys.com/api/v1/incoming/intune/0a1b2c3d-1234-5678-9abc-def012345678/scep",
  "jamf_access_token": "1Z4QqEnCt05Jjt3TV5LgPJ4V_WL_RWnJ7dqVMLYHj81=",
  "jamf_scep_url": "https://scep.mistsys.com/api/v1/incoming/intune/0a1b2c3d-1234-5678-9abc-def012345678/scep",
  "jamf_webhook_url": "https://scep.mistsys.com/api/v1/webhook/jamf/0a1b2c3d-1234-5678-9abc-def012345678/scep",
  "suspended": false
}
```

| Field               | Type            | Required | Sensitive | Description |
|---------------------|-----------------|----------|-----------|-------------|
| `cert_providers`    | string[] (enum) | No       | No        | List of configured SCEP cert providers. Enum values: `intune`, `jamf`, `byod`. May be absent or empty. |
| `enabled`           | boolean         | No       | No        | Read-only on upstream side. Whether SCEP is enabled for the org. |
| `intune_scep_url`   | string          | No       | Partial   | Intune SCEP enrollment URL. Read-only upstream. Logged only at the host-name level, never as the full URL. |
| `jamf_access_token` | string          | No       | YES       | Bearer token Jamf uses against the Mist SCEP webhook. Persisted to the configured backend; never logged above DEBUG; at DEBUG only presence is logged. |
| `jamf_scep_url`     | string          | No       | Partial   | Jamf SCEP enrollment URL. Read-only upstream. Logged host-name only. |
| `jamf_webhook_url`  | string          | No       | Partial   | Jamf webhook URL. Read-only upstream. Logged host-name only. |
| `suspended`         | boolean         | No       | No        | Whether SCEP is suspended for this org. Default `false`. |

All fields are optional in the schema (the response object has no `required` list). When
SCEP has never been configured for an org, the response may be a near-empty object
(for example `{"enabled": false, "suspended": false}`). MistHelper treats this as a
valid response, not an error.

### Error Responses

| Status | Mist Description                                                  | MistHelper Handling |
|--------|-------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                        | Log `WARNING` ("Mist returned 400 -- check org_id format"). No traceback. Return early. |
| 401    | Unauthorized                                                      | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                 | Log `ERROR` ("Mist 403 -- token lacks read access to org %s setting.mist_scep", org_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                    | Log `WARNING` ("No Mist SCEP setting for org %s (404)", org_id). Treat as empty result, write zero rows, return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)      | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is never
included in any log message, even at `DEBUG`. The `jamf_access_token` returned in the
200 body follows the same rule.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.orgs.setting import mist_scep as mist_scep_module

apisession = mistapi.APISession(
    host=os.environ["MIST_HOST"],
    apitoken=os.environ["MIST_API_TOKEN"],
)
apisession.login()

# Single required path parameter, no query parameters:
response = mist_scep_module.getOrgMistScep(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

# Access the parsed body:
body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/orgs/{org_id}/setting/mist_scep` -> `mistapi.api.v1.orgs.setting.mist_scep`).
  The enriched per-endpoint doc's "mistapi SDK" line lists a shorter
  `mistapi.api.v1.orgs.scep` path, but sibling endpoints under the same URL
  (`PUT /orgs/{org_id}/setting/mist_scep` -> `mistapi.api.v1.orgs.setting.mist_scep`)
  confirm the URL-based path is canonical. Final verification happens at implementation
  time via `python -c "from mistapi.api.v1.orgs.setting import mist_scep; help(mist_scep)"`.
- `response.data` is `None` only when the HTTP response has no body (rare for this
  endpoint). MistHelper normalizes this to `{}` before flattening.
- There are no query parameters to omit conditionally -- the SDK call signature is
  `(apisession, org_id)` with no optional kwargs.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No `limit` / `page`
parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's adaptive delay
system (`delay_metrics.json` per-endpoint state + `tuning_data.json` learning) governs
back-off automatically. No endpoint-specific tuning required for this contract -- the
response is a single small JSON object and the call cost is one unit.

## Related Endpoints (for awareness only -- out of scope for this spec)

| Method | URL                                                              | Purpose                              |
|--------|------------------------------------------------------------------|--------------------------------------|
| PUT    | `/api/v1/orgs/{org_id}/setting/mist_scep`                        | Update Mist SCEP setting             |
| DELETE | `/api/v1/orgs/{org_id}/setting/mist_scep`                        | Delete Mist SCEP setting             |
| GET    | `/api/v1/orgs/{org_id}/setting/mist_scep/client_certs`           | List Mist SCEP client certs          |
| POST   | `/api/v1/orgs/{org_id}/setting/mist_scep/client_certs/revoke`    | Revoke SCEP client certs             |

The PUT, DELETE, and POST endpoints are write operations and are out of scope for this
read-only spec (see `spec.md` -> "Out of Scope"). A separate spec will introduce a
destructive menu item for them if and when needed.
