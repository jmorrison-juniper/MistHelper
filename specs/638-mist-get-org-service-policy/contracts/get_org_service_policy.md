# Endpoint Contract: getOrgServicePolicy

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_servicepolicies_servicepolicy_id.md`
**Date**: 2026-06-30

## HTTP Contract

| Attribute       | Value                                                                   |
|-----------------|-------------------------------------------------------------------------|
| **Method**      | `GET`                                                                   |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id}` |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs Service Policies`                                                 |
| **operationId** | `getOrgServicePolicy`                                                   |

### Path Parameters

| Name               | Type          | Required | Description |
|--------------------|---------------|----------|-------------|
| `org_id`           | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |
| `servicepolicy_id` | string (UUID) | Yes      | Service Policy UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

None. This endpoint is not filtered or paginated.

### Request Headers

| Header          | Value                | Notes                                                            |
|-----------------|----------------------|------------------------------------------------------------------|
| `Authorization` | `Token <api_token>`  | Injected by `mistapi.APISession` from `.env`. Never logged.      |
| `Accept`        | `application/json`   | Default for mistapi SDK.                                         |
| `User-Agent`    | `mistapi/<version>`  | Set by SDK.                                                      |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "name": "default-allow",
  "action": "allow",
  "local_routing": true,
  "path_preference": "primary-wan",
  "services": ["ssh", "https"],
  "tenants": ["engineering", "operations"],
  "created_time": 1719600000,
  "modified_time": 1719603612.123,
  "aamw": {
    "enabled": false,
    "profile": "standard",
    "aamwprofile_id": "89b9d208-84a4-fa8f-af57-78f92c639cf2"
  },
  "antivirus": {
    "enabled": false,
    "profile": "Default",
    "avprofile_id": "89b9d208-84a4-fa8f-af57-78f92c639cf3"
  },
  "appqoe": {"enabled": false},
  "secintel": {
    "enabled": false,
    "profile": "standard",
    "secintelprofile_id": "secintel-default"
  },
  "ssl_proxy": {"enabled": false, "ciphers_category": "strong"},
  "idp": {
    "enabled": true,
    "alert_only": false,
    "profile": "strict",
    "idpprofile_id": "89b9d208-84a4-fa8f-af57-78f92c639cf2"
  },
  "ewf": [
    {"alert_only": false, "block_message": "Access to this URL Category has been blocked", "enabled": true,  "profile": "strict"},
    {"alert_only": true,  "block_message": "Monitored URL Category",                        "enabled": true,  "profile": "standard"},
    {"alert_only": false, "block_message": "Critical block",                                "enabled": false, "profile": "critical"}
  ]
}
```

| Field             | Type                | Description |
|-------------------|---------------------|-------------|
| `id`              | string UUID (readOnly) | Unique object instance ID in the Mist organization. MistHelper natural primary key for the parent row. |
| `org_id`          | string UUID (readOnly) | Owning org UUID. MistHelper injects the caller-supplied org_id if the API body omits it. |
| `name`            | string              | Human-friendly policy name. |
| `action`          | string enum         | `allow` or `deny`. |
| `local_routing`   | boolean             | Access within the same VRF. |
| `path_preference` | string              | Optional WAN path steering identifier; empty string means "derive all paths". |
| `services`        | string[] (unique)   | Service names bound to the policy. |
| `tenants`         | string[] (unique)   | Tenant scopes bound to the policy. |
| `created_time`    | number epoch (readOnly) | When the object was created. |
| `modified_time`   | number epoch (readOnly) | When the object was last modified. |
| `aamw`            | object              | SRX-only Advanced Anti-Malware config. Sub-fields: `enabled`, `profile` (`docsonly`/`executables`/`standard`), `aamwprofile_id`. |
| `antivirus`       | object              | SRX-only AV config. Sub-fields: `enabled`, `profile` (Default/noftp/httponly), `avprofile_id`. |
| `appqoe`          | object              | SRX-only AppQoE config. Sub-field: `enabled`. |
| `secintel`        | object              | SRX-only Security Intelligence config. Sub-fields: `enabled`, `profile` (`default`/`standard`/`strict`), `secintelprofile_id`. |
| `ssl_proxy`       | object              | SRX-only SSL proxy config. Sub-fields: `enabled`, `ciphers_category` (`medium`/`strong`/`weak`). |
| `idp`             | object              | IDP config. Sub-fields: `alert_only`, `enabled`, `profile` (`Custom`/`strict` default/`standard`), `idpprofile_id`. |
| `ewf`             | object[]            | Enhanced Web Filtering rule array. MistHelper flattens each element into a child row keyed by `(org_id, servicepolicy_id, rule_index)`. Each item: `{alert_only, block_message, enabled, profile}` where `profile` is enum `critical`/`standard`/`strict`. |

### Error Responses

| Status | Mist Description                                                     | MistHelper Handling |
|--------|----------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                           | Log `WARNING` ("Mist returned 400 -- check org_id / servicepolicy_id format"), no traceback, return early. |
| 401    | Unauthorized                                                         | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                    | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist.                      | Log `WARNING` ("Service policy %s not found in org %s", servicepolicy_id, org_id). Treat as empty result; write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)         | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is
never included in any log message, even at `DEBUG`.

## mistapi Python SDK Call Signature

```python
import mistapi
from mistapi.api.v1.orgs import servicepolicies as service_policies_module

apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

# Fetch a single service policy detail record:
response = service_policies_module.getOrgServicePolicy(
    apisession,
    org_id="a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
    servicepolicy_id="53f10664-3ce8-4c27-b382-0ef66432349f",
)

# Access the parsed body:
body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/orgs/{org_id}/servicepolicies/{servicepolicy_id}` ->
  `mistapi.api.v1.orgs.servicepolicies`). The enriched per-endpoint doc lists
  the SDK as `mistapi.api.v1.orgs.service_policies.getOrgServicePolicy()`
  (spelled with an underscore), but the URL-based `servicepolicies` module path
  matches the OpenAPI URL and matches how adjacent endpoints
  (`listOrgServicePolicies`, `updateOrgServicePolicy`) are organized. Final
  verification happens at implementation via
  `python -c "from mistapi.api.v1.orgs import servicepolicies; help(servicepolicies)"`;
  if the SDK exposes only the underscore variant, the import statement is
  updated to `from mistapi.api.v1.orgs import service_policies as
  service_policies_module` -- no other change needed.
- `response.data` is `None` only when the HTTP response had no body (rare).
  MistHelper normalizes this to `{}` before flattening.
- Neither path parameter is optional; both must be non-empty valid UUIDs.
  MistHelper validates both with `is_valid_uuid()` before calling the SDK to
  prevent avoidable 400s.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No
`limit`/`page` parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No
endpoint-specific tuning required for this contract.
