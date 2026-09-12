# Endpoint Contract: GetOrgSkyAtpIntegration

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_setting_skyatp_setup.md`
**Date**: 2026-06-30

## HTTP Contract

| Attribute       | Value                                                                        |
|-----------------|------------------------------------------------------------------------------|
| **Method**      | `GET`                                                                        |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/setting/skyatp/setup`              |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs Integration SkyATP`                                                    |
| **operationId** | `getOrgSkyAtpIntegration`                                                    |

### Path Parameters

| Name     | Type          | Required | Description                                                                            |
|----------|---------------|----------|----------------------------------------------------------------------------------------|
| `org_id` | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

None. This endpoint has no query parameters.

### Request Headers

| Header          | Value                | Notes |
|-----------------|----------------------|-------|
| `Authorization` | `Token <api_token>`  | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`        | `application/json`   | Default for mistapi SDK. |
| `User-Agent`    | `mistapi/<version>`  | Set by SDK. |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

Example body (redacted signed URLs):

```json
{
  "secintel": {
    "third_party_threat_feeds": [
      "block_list",
      "threatfox_ip",
      "tor",
      "threatfox_url",
      "threatfox_domains"
    ]
  },
  "secintel_allowlist_url": "https://papi.s3.amazonaws.com/secintel_allowlist/xxx...",
  "secintel_blocklist_url": "https://papi.s3.amazonaws.com/secintel_blocklist/xxx..."
}
```

| Field                                    | Type            | Description |
|------------------------------------------|-----------------|-------------|
| `secintel`                               | object          | Container for Sky ATP / secintel feed configuration. May be absent for orgs that have never configured Sky ATP -- MistHelper tolerates this via `body.get("secintel", {})`. |
| `secintel.third_party_threat_feeds`      | string[] (unique items) | Third-party threat-intel feed identifiers enabled on the org. Documented values by category -- ip-based: `block_list`, `threatfox_ip`, `feodo_tracker`, `dshield`, `tor`; url-based: `threatfox_url`, `urlhaus`, `open_phish`; domain-based: `threatfox_domains`. Juniper native secintel feeds (`infected_host`, `geo_ip`, `attacker_ip`, `command_and_control`) are enabled by license tier and are NOT listed in this array. |
| `secintel_allowlist_url`                 | string, read-only | Signed S3 URL exposing the org allowlist. Sensitive -- treated as a credential by MistHelper (stored in CSV/SQLite as data, but never echoed to INFO log). |
| `secintel_blocklist_url`                 | string, read-only | Signed S3 URL exposing the org blocklist. Sensitive -- same handling as the allowlist URL. |

### Error Responses

| Status | Mist Description                                                          | MistHelper Handling |
|--------|---------------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                                | Log `WARNING` ("Mist returned 400 -- check org_id format"), no traceback, return early. |
| 401    | Unauthorized                                                              | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                         | Log `ERROR` ("Mist 403 -- token lacks read access to org %s Sky ATP settings", org_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                            | Log `WARNING` ("No Sky ATP integration configured for org %s", org_id). Treat as empty result and write zero rows. Return cleanly (exit code 0). |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)              | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API
token is never included in any log message, even at `DEBUG`. Signed
allowlist / blocklist URLs are echoed only as boolean presence flags at
INFO / DEBUG level (`has_allowlist_url=true`), never as the raw URL.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.orgs.setting.skyatp import setup as sky_atp_setup_module

apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

response = sky_atp_setup_module.getOrgSkyAtpIntegration(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/orgs/{org_id}/setting/skyatp/setup` ->
  `mistapi.api.v1.orgs.setting.skyatp.setup`). This is the path named in
  spec.md and matches how the mistapi SDK organizes modules by URL.
- The enriched per-endpoint doc lists an alternate SDK path
  `mistapi.api.v1.orgs.integration_skyatp.getOrgSkyAtpIntegration()`.
  MistHelper's implementation wraps the import in a try/except to
  tolerate either layout across mistapi versions. Final verification at
  implementation time via
  `python -c "from mistapi.api.v1.orgs.setting.skyatp import setup;
  help(setup)"`.
- `response.data` is `None` only when the HTTP response had no body
  (rare). MistHelper normalizes this to `{}` before flattening.
- There are no query parameters and no request body to serialize.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No
`limit`/`page` parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No
endpoint-specific tuning required for this contract -- the response is a
small singleton object with no follow-on paged calls.
