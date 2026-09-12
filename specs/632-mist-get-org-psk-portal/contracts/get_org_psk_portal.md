# Endpoint Contract: getOrgPskPortal

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_pskportals_pskportal_id.md`
**Date**: 2026-06-30

## HTTP Contract

| Attribute      | Value                                                              |
|----------------|--------------------------------------------------------------------|
| **Method**     | `GET`                                                              |
| **URL**        | `https://{mist_host}/api/v1/orgs/{org_id}/pskportals/{pskportal_id}` |
| **Auth**       | `Authorization: Token {api_token}` header (injected automatically by `mistapi.APISession`) |
| **Tag**        | `Orgs Psk Portals`                                                 |
| **operationId**| `getOrgPskPortal`                                                  |

### Path Parameters

| Name           | Type          | Required | Description                                                                     |
|----------------|---------------|----------|---------------------------------------------------------------------------------|
| `org_id`       | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()`.   |
| `pskportal_id` | string (UUID) | Yes      | PSK portal UUID. Validated client-side by MistHelper via `is_valid_uuid()`.     |

### Query Parameters

None.

### Request Headers

| Header          | Value                    | Notes                                                          |
|-----------------|--------------------------|----------------------------------------------------------------|
| `Authorization` | `Token <api_token>`      | Injected by `mistapi.APISession` from `.env`. Never logged.    |
| `Accept`        | `application/json`       | Default for the mistapi SDK.                                   |
| `User-Agent`    | `mistapi/<version>`      | Set by SDK.                                                    |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "name": "Guest Sponsor Portal",
  "ssid": "Guest",
  "auth": "sponsor",
  "type": "byod",
  "role": "guest",
  "bg_image_url": "https://cdn.example/bg.png",
  "thumbnail_url": "https://cdn.example/thumb.png",
  "template_url": "https://cdn.example/template.html",
  "ui_url": "https://portal.example/psk",
  "cleanup_psk": true,
  "expire_time": 1440,
  "expiry_notification_time": 3,
  "hide_psks_created_by_other_admins": false,
  "max_usage": 0,
  "notification_renew_url": "https://custom-sso/url",
  "notify_expiry": true,
  "notify_on_create_or_edit": false,
  "required_fields": ["email", "name"],
  "vlan_id": {"default": 10},
  "passphrase_rules": {
    "alphabets_enabled": true,
    "length": 12,
    "min_length": 10,
    "max_length": 16,
    "numerics_enabled": true,
    "symbols": "()[]{}_%@#&$",
    "symbols_enabled": true
  },
  "sso": {
    "allowed_roles": ["employee", "contractor"],
    "idp_cert": "-----BEGIN CERTIFICATE-----...",
    "idp_sign_algo": "sha256",
    "idp_sso_url": "https://idp.example/sso",
    "issuer": "https://idp.example",
    "nameid_format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
    "role_mapping": {"employee": "groups"},
    "use_sso_role_for_psk_role": false
  },
  "created_time": 1719600000,
  "modified_time": 1719603612.123
}
```

| Field                                | Type            | Description |
|--------------------------------------|-----------------|-------------|
| `id`                                 | string (UUID)   | Read-only. Unique portal ID assigned by Mist. Used as MistHelper natural PK. |
| `org_id`                             | string (UUID)   | Read-only. Echo of the parent org UUID. |
| `name`                               | string          | Portal name. Required by API. |
| `ssid`                               | string          | Intended SSID. Required by API. |
| `auth`                               | string enum     | `sponsor` or `sso`. |
| `type`                               | string enum     | `admin` or `byod`. Personal PSK portal kind. |
| `role`                               | string          | Role assigned to PSKs from this portal. |
| `bg_image_url` / `thumbnail_url` / `template_url` / `ui_url` | string | UI customization URLs. |
| `cleanup_psk`                        | boolean         | Cleanup exited PSK when portal deleted or SSID changed. Default `false`. |
| `expire_time`                        | int32           | PSK expiry, minutes. |
| `expiry_notification_time`           | int32           | Days before expiry to send reminder notification. |
| `hide_psks_created_by_other_admins`  | boolean         | Only meaningful when `type==admin`. Default `false`. |
| `max_usage`                          | int32           | `0` means unlimited. Default `0`. |
| `notification_renew_url`             | string          | Optional URL included in notification emails. |
| `notify_expiry`                      | boolean         | If true, send reminder before expiry. |
| `notify_on_create_or_edit`           | boolean         | Notify admins on create/edit. Default `false`. |
| `required_fields`                    | string[]        | Signup fields required from the guest (email is required by default). |
| `vlan_id`                            | object          | VLAN mapping. Can be a single VLAN or a per-role map. |
| `passphrase_rules`                   | object          | Nested config for passphrase generation. |
| `passphrase_rules.alphabets_enabled` | boolean         | Default `true`. |
| `passphrase_rules.length`            | int32 [8..63]   | Target length. |
| `passphrase_rules.min_length`        | int32 [8..63]   | Random min length when both min and max are valid. |
| `passphrase_rules.max_length`        | int32 [8..63]   | Random max length when both min and max are valid; must be > min_length. |
| `passphrase_rules.numerics_enabled`  | boolean         | Default `true`. |
| `passphrase_rules.symbols`           | string          | Allowed symbol set. Example: `()[]{}_%@#&$`. |
| `passphrase_rules.symbols_enabled`   | boolean         | Default `true`. |
| `sso`                                | object          | Only meaningful when `auth==sso`. |
| `sso.allowed_roles`                  | string[]        | Roles permitted to access the portal; empty/absent = any role. |
| `sso.idp_cert`                       | string          | SAML IdP certificate (PEM). |
| `sso.idp_sign_algo`                  | string enum     | `sha1`, `sha256`, `sha384`, `sha512`. |
| `sso.idp_sso_url`                    | string          | IdP SSO URL. |
| `sso.issuer`                         | string          | SAML issuer. |
| `sso.nameid_format`                  | string          | SAML NameID format URI. |
| `sso.role_mapping`                   | object          | Role name -> SSO attribute map. |
| `sso.use_sso_role_for_psk_role`      | boolean         | If true, top-level `role` is ignored. |
| `created_time`                       | number (epoch)  | Read-only. Creation time. |
| `modified_time`                      | number (epoch)  | Read-only. Last-modified time. |

### Error Responses

| Status | Mist Description                                                   | MistHelper Handling |
|--------|--------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                         | Log `WARNING` ("Mist returned 400 -- check org_id / pskportal_id format"), no traceback, return early. |
| 401    | Unauthorized                                                       | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                  | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id_short). Return early. |
| 404    | Not found. Endpoint or resource does not exist                     | Log `WARNING` ("No PSK portal %s in org %s", pskportal_id_short, org_id_short). Treat as empty result and write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)       | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token, the
full request URL, and the `Authorization` header value are never included in any
log message -- not even at `DEBUG`.

## mistapi Python SDK Call Signature

```python
import mistapi
from mistapi.api.v1.orgs import psk_portals

apisession = mistapi.APISession(
    host=os.environ["MIST_HOST"],
    apitoken=os.environ["MIST_API_TOKEN"],
)
apisession.login()

response = psk_portals.getOrgPskPortal(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
    pskportal_id="53f10664-3ce8-4c27-b382-0ef66432349f",
)

body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/orgs/{org_id}/pskportals/{pskportal_id}` -> `mistapi.api.v1.orgs.psk_portals`).
  Python module names use snake_case, so the URL segment `pskportals` maps to the
  module name `psk_portals`. Final verification happens at implementation time
  via
  `python -c "from mistapi.api.v1.orgs import psk_portals; help(psk_portals.getOrgPskPortal)"`.
- `response.data` is `None` only when the HTTP response had no body (rare, e.g. a
  transport-level 429 before Mist returns JSON). MistHelper normalizes this to
  `{}` before flattening so the writer never sees a `None`.
- Both path parameters are required. The SDK raises a `TypeError` if either is
  omitted; MistHelper catches this in the shared retry wrapper and surfaces it
  as a `WARNING`.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No `limit` /
`page` / cursor parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No
endpoint-specific tuning is required for this contract because the call is
lightweight (single object, small response body, no pagination).
