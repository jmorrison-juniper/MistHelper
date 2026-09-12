# Endpoint Contract: getOrgJseIntegration

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_setting_jse_setup.md`
**Date**: 2026-06-30

## HTTP Contract

| Attribute       | Value                                                       |
|-----------------|-------------------------------------------------------------|
| **Method**      | `GET`                                                       |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/setting/jse/setup`|
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs Integration JSE`                                      |
| **operationId** | `getOrgJseIntegration`                                      |

### Path Parameters

| Name     | Type          | Required | Description |
|----------|---------------|----------|-------------|
| `org_id` | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

None. The endpoint takes no query parameters.

### Request Headers

| Header           | Value                                  | Notes |
|------------------|----------------------------------------|-------|
| `Authorization`  | `Token <api_token>`                    | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`         | `application/json`                     | Default for mistapi SDK. |
| `User-Agent`     | `mistapi/<version>`                    | Set by SDK. |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

Schema title: `account_jse_info` (object).

```json
{
  "cloud_name": "devcentral.juniperclouds.net",
  "org_names": [
    "Acme Corp JSE Org",
    "Acme Corp Secondary"
  ],
  "username": "john@abc.com"
}
```

| Field        | Type        | Description |
|--------------|-------------|-------------|
| `cloud_name` | string      | JSE cloud the Mist org is bound to. Example: `devcentral.juniperclouds.net`. May be absent when no integration is configured. |
| `org_names`  | string[]    | Unique-items array of JSE org names visible to the bound JSE user. May be absent or empty when no integration is configured. MistHelper flattens this into a comma-joined `org_names_joined` column plus an `org_names_count` integer. |
| `username`   | string      | JSE account email of the user who configured the integration. Example: `john@abc.com`. May be absent when no integration is configured. |

All three fields are optional in the schema. MistHelper treats a 200 OK
body with all keys absent the same way it treats a 404: zero output rows
plus a `WARNING` log line.

### Error Responses

| Status | Mist Description                                                          | MistHelper Handling |
|--------|---------------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                                | Log `WARNING` ("Mist returned 400 -- check org_id format"), no traceback, return early. |
| 401    | Unauthorized                                                              | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                         | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id). Return early. |
| 404    | Not found. The API endpoint or resource does not exist.                   | Log `WARNING` ("No JSE integration configured for org %s -- writing zero rows", org_id). Treat as empty result and write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)              | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API
token is never included in any log message, even at `DEBUG`. No HTTP
status results in a Python traceback bubbling to the user.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.orgs.setting.jse import setup as jse_setup_module

apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

# Single call -- no query parameters, no request body:
response = jse_setup_module.getOrgJseIntegration(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

# Access the parsed body:
body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path follows the OpenAPI URL path
  (`/orgs/{org_id}/setting/jse/setup` ->
  `mistapi.api.v1.orgs.setting.jse.setup`). The enriched per-endpoint
  doc lists an alternate tag-derived path
  (`mistapi.api.v1.orgs.integration_jse`). If the installed mistapi
  release exposes the function only at the tag-derived path, the
  implementation switches the `from ... import setup` line accordingly
  -- everything else in the contract stays the same. Final verification:
  `python -c "from mistapi.api.v1.orgs.setting.jse import setup; help(setup)"`.
- `response.data` is `None` only when the HTTP response had no body.
  MistHelper normalizes this to `{}` before flattening.
- The function takes no optional query parameters beyond `apisession`
  and `org_id`.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No
`limit`/`page` parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour.
MistHelper's adaptive delay system (`delay_metrics.json` per-endpoint
state + `tuning_data.json` learning) governs back-off automatically. No
endpoint-specific tuning required for this contract -- the call is
inexpensive and returns a small fixed-shape JSON object.
