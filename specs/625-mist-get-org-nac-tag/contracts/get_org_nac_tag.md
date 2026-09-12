# Endpoint Contract: getOrgNacTag

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_nactags_nactag_id.md`
**Date**: 2026-06-30

## HTTP Contract

| Attribute       | Value                                                          |
|-----------------|----------------------------------------------------------------|
| **Method**      | `GET`                                                          |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/nactags/{nactag_id}` |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs NAC Tags`                                                |
| **operationId** | `getOrgNacTag`                                                 |

### Path Parameters

| Name        | Type          | Required | Description                                                                             |
|-------------|---------------|----------|-----------------------------------------------------------------------------------------|
| `org_id`    | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` first.     |
| `nactag_id` | string (UUID) | Yes      | NAC tag UUID (Mist-generated `id` field). Validated client-side by MistHelper first.    |

### Query Parameters

_None._ This endpoint takes no query parameters.

### Request Headers

| Header          | Value                    | Notes |
|-----------------|--------------------------|-------|
| `Authorization` | `Token <api_token>`      | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`        | `application/json`       | Default for mistapi SDK. |
| `User-Agent`    | `mistapi/<version>`      | Set by SDK. |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

Single JSON object representing one NAC tag. Example (illustrative -- the
concrete field set depends on the tag's `type`):

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "name": "corp-radius-superuser",
  "type": "radius_group",
  "created_time": 1700000000,
  "modified_time": 1719000000,
  "allow_usermac_override": false,
  "radius_group": "superuser"
}
```

Example for a `match`-type tag:

```json
{
  "id": "f0e1d2c3-b4a5-4968-8877-665544332211",
  "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "name": "engineering-ssid-match",
  "type": "match",
  "match": "ssid",
  "match_all": false,
  "values": ["Engineering", "Engineering-Guest"],
  "created_time": 1700000000,
  "modified_time": 1719000000,
  "allow_usermac_override": true
}
```

| Field                    | Type            | Description |
|--------------------------|-----------------|-------------|
| `id`                     | string (UUID)   | Mist-assigned unique ID. Read-only. Stable for the lifetime of the tag. |
| `org_id`                 | string (UUID)   | Parent org UUID. Read-only. |
| `name`                   | string          | Human-readable tag name. Required. Min length 1. |
| `type`                   | string enum     | One of: `egress_vlan_names`, `gbp_tag`, `match`, `radius_attrs`, `radius_group`, `radius_vendor_attrs`, `redirect_nacportal_id`, `session_timeout`, `username_attr`, `vlan`. Required. Determines which of the type-specific fields below are populated. |
| `created_time`           | number (epoch)  | Read-only. Seconds since epoch. |
| `modified_time`          | number (epoch)  | Read-only. Seconds since epoch. |
| `allow_usermac_override` | boolean         | Default `false`. When `true`, a usermac result can override this tag. |
| `match`                  | string enum     | When `type==match`. One of: `cert_cn`, `cert_eku`, `cert_issuer`, `cert_san`, `cert_serial`, `cert_sub`, `cert_template`, `client_mac`, `edr_status`, `gbp_tag`, `hostname`, `idp_role`, `ingress_vlan`, `mdm_status`, `nas_ip`, `radius_group`, `realm`, `ssid`, `user_name`, `usermac_label`. |
| `match_all`              | boolean         | When `type==match`. Default `false`. `true` = require all `values` to match; `false` = any value matches. Currently meaningful only when `match` is `idp_role`, `usermac_label`, or `edr_status`. |
| `values`                 | string[]        | When `type==match`. List of values to match against. |
| `egress_vlan_names`      | string[]        | When `type==egress_vlan_names`. List of egress VLAN names to return. |
| `gbp_tag`                | object          | When `type==gbp_tag`. Group-Based Policy tag payload. |
| `radius_attrs`           | string[]        | When `type==radius_attrs`. Standard RADIUS attributes, e.g. `"Idle-Timeout=600"`. |
| `radius_group`           | string          | When `type==radius_group`. RADIUS group name. |
| `radius_vendor_attrs`    | string[]        | When `type==radius_vendor_attrs`. Vendor-specific attributes, e.g. `"PaloAlto-Admin-Role=superuser"`. |
| `nacportal_id`           | string (UUID)   | When `type==redirect_nacportal_id`. ID of NAC portal to redirect to. |
| `session_timeout`        | integer (secs)  | When `type==session_timeout`. |
| `username_attr`          | string enum     | When `type==username_attr`. One of: `automatic`, `cn`, `dns`, `email`, `upn`. |
| `vlan`                   | string          | When `type==vlan`. VLAN identifier (name or ID) to assign. |

Only the fields relevant to the tag's `type` are populated by the API.
MistHelper stores array/object fields as JSON-encoded TEXT in
`_json`-suffixed SQLite columns per `data-model.md`.

### Error Responses

| Status | Mist Description                                                    | MistHelper Handling |
|--------|---------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                          | Log `WARNING` ("Mist returned 400 -- check org_id / nactag_id format"), no traceback, return early. |
| 401    | Unauthorized                                                        | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                   | Log `ERROR` ("Mist 403 -- token lacks read access to NAC tags in org %s", org_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                      | Log `WARNING` ("No NAC tag %s in org %s", nactag_id, org_id). Treat as empty result and write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)        | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is
never included in any log message, even at `DEBUG`. The full request URL is
also never logged (only the truncated `org_id[:8]` / `nactag_id[:8]` are
included in `INFO` chatter).

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.orgs import nac_tags

apisession = mistapi.APISession(
    host=os.environ["MIST_HOST"],
    apitoken=os.environ["MIST_API_TOKEN"],
)
apisession.login()

response = nac_tags.getOrgNacTag(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
    nactag_id="53f10664-3ce8-4c27-b382-0ef66432349f",
)

body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path is `mistapi.api.v1.orgs.nac_tags` (snake_case in
  Python) even though the URL path segment is `nactags` (no underscore) --
  this is a documented mistapi convention. Confirmed by the enriched
  per-endpoint doc.
- `response.data` is `None` only when the HTTP response had no body (rare).
  MistHelper normalizes this to `{}` before flattening.
- Both `org_id` and `nactag_id` are passed positionally per mistapi
  convention. Neither has a Python-side default; both are required.
- The function returns a `mistapi.APIResponse` object; do not attempt to
  iterate it -- `response.data` is a single dict, not a paginated list.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No
`limit` / `page` parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No
endpoint-specific tuning required for this contract; a single GET returning
one small JSON object rarely triggers 429.

## Related Endpoints (context)

- `GET /orgs/{org_id}/nactags` -- `listOrgNacTags`, MistHelper menu 44.
  Bulk list companion; shares SQLite table `org_nac_tags` per
  `data-model.md`.
- `PUT /orgs/{org_id}/nactags/{nactag_id}` -- update tag. Out of scope for
  this read-only spec.
