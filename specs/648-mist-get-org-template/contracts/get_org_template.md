# Endpoint Contract: getOrgTemplate

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_templates_template_id.md`
**Date**: 2026-07-01

## HTTP Contract

| Attribute       | Value                                                           |
|-----------------|-----------------------------------------------------------------|
| **Method**      | `GET`                                                           |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/templates/{template_id}` |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs WLAN Templates`                                           |
| **operationId** | `getOrgTemplate`                                                |

### Path Parameters

| Name          | Type          | Required | Description |
|---------------|---------------|----------|-------------|
| `org_id`      | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |
| `template_id` | string (UUID) | Yes      | WLAN Template UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

_None._

### Request Headers

| Header          | Value                        | Notes |
|-----------------|------------------------------|-------|
| `Authorization` | `Token <api_token>`          | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`        | `application/json`           | Default for mistapi SDK. |
| `User-Agent`    | `mistapi/<version>`          | Set by SDK. |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "name": "Guest-Corp",
  "created_time": 1719600000,
  "modified_time": 1719601234,
  "filter_by_deviceprofile": false,
  "deviceprofile_ids": [
    "b1c2d3e4-1111-2222-3333-444455556666",
    "c2d3e4f5-2222-3333-4444-555566667777"
  ],
  "applies": {
    "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
    "site_ids": [
      "d3e4f5a6-3333-4444-5555-666677778888",
      "e4f5a6b7-4444-5555-6666-777788889999"
    ],
    "sitegroup_ids": [
      "f5a6b7c8-5555-6666-7777-8888999900aa"
    ]
  },
  "exceptions": {
    "site_ids": [
      "a6b7c8d9-6666-7777-8888-99990000aabb"
    ],
    "sitegroup_ids": [
      "b7c8d9e0-7777-8888-9999-0000aabbccdd",
      "c8d9e0f1-8888-9999-0000-aabbccddeeff"
    ]
  }
}
```

| Field                     | Type                    | Description |
|---------------------------|-------------------------|-------------|
| `id`                      | string (UUID)           | Template UUID. Read-only. Stable natural PK for MistHelper. |
| `org_id`                  | string (UUID)           | Owning organization UUID. Read-only. |
| `name`                    | string                  | Template display name. Required per schema. |
| `created_time`            | number (epoch seconds)  | Read-only. Set on creation. |
| `modified_time`           | number (epoch seconds)  | Read-only. Bumped on every update. |
| `filter_by_deviceprofile` | boolean                 | Whether apply/exception rules further filter by device profile. |
| `deviceprofile_ids`       | string[] (UUID)         | Device profiles bound to this template. |
| `applies`                 | object                  | Scope of application. Contains `org_id`, `site_ids[]`, `sitegroup_ids[]`. |
| `applies.org_id`          | string (UUID)           | Optional. When present, the template is applied org-wide. Read-only. |
| `applies.site_ids`        | string[] (UUID)         | Sites the template applies to. |
| `applies.sitegroup_ids`   | string[] (UUID)         | Sitegroups the template applies to. |
| `exceptions`              | object                  | Scopes excluded from application. Takes precedence over `applies`. |
| `exceptions.site_ids`     | string[] (UUID)         | Sites explicitly excluded. |
| `exceptions.sitegroup_ids`| string[] (UUID)         | Sitegroups explicitly excluded. |

Required field per schema: `name`. All other fields may be absent when
default-valued or when the template has not yet been fully configured;
MistHelper tolerates missing keys via `dict.get()` with sensible defaults.

### Error Responses

| Status | Mist Description                                                             | MistHelper Handling |
|--------|------------------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                                   | Log `WARNING` ("Mist returned 400 -- check org_id/template_id format"), no traceback, return early. |
| 401    | Unauthorized                                                                 | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                            | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                               | Log `WARNING` ("No template %s in org %s", template_id, org_id). Treat as empty result; write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)                 | Adaptive delay system (delay_metrics.json + tuning_data.json) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is
never included in any log message, even at DEBUG.

## mistapi Python SDK Call Signature

```python
import mistapi
from mistapi.api.v1.orgs import wlan_templates

apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

response = wlan_templates.getOrgTemplate(
    apisession,
    org_id="a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
    template_id="53f10664-3ce8-4c27-b382-0ef66432349f",
)

body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The enriched per-endpoint doc lists the SDK module as
  `mistapi.api.v1.orgs.wlan_templates.getOrgTemplate()`. The `wlan_templates`
  submodule is the SDK's disambiguator between WLAN templates (this endpoint),
  site templates, network templates, and gateway templates -- all of which
  share the `/templates` URL fragment shape at different scopes. Final
  verification at implementation time:
  `python -c "from mistapi.api.v1.orgs import wlan_templates; help(wlan_templates.getOrgTemplate)"`.
- `response.data` is `None` only when the HTTP response had no body (rare).
  MistHelper normalizes this to `{}` before flattening.
- The path parameters are positional in the SDK signature (`apisession`,
  `org_id`, `template_id`); MistHelper passes them positionally to match SDK
  convention across the rest of the codebase.
- No query parameters. No request body. No pagination.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No
`limit`/`page`/`start`/`end` parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No endpoint-
specific tuning is required for this contract.
