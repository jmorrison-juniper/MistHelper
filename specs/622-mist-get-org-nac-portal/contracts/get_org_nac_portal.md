# Endpoint Contract: getOrgNacPortal

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)
**Source**: `documentation/api/orgs/GET_orgs_org_id_nacportals_nacportal_id.md`

## HTTP Contract

| Aspect | Value |
|--------|-------|
| **Method** | `GET` |
| **URL template** | `https://{MIST_HOST}/api/v1/orgs/{org_id}/nacportals/{nacportal_id}` |
| **Authentication** | `Authorization: Token {MIST_API_TOKEN}` header (loaded from `.env` by `mistapi.APISession`) |
| **Required path params** | `org_id` (string, UUID), `nacportal_id` (string, UUID) |
| **Query params** | _None_ |
| **Request body** | _None_ |
| **Pagination** | Not paginated -- single object response |
| **Rate limit** | Standard Mist API rate limits (5000 req/hour per token); adaptive delay system governs back-off |

### Required Headers

| Header | Value | Source |
|--------|-------|--------|
| `Authorization` | `Token <api_token>` | `MIST_API_TOKEN` env var via `mistapi.APISession` |
| `Accept` | `application/json` | Set by `mistapi` SDK |
| `User-Agent` | `mistapi/<version>` | Set by `mistapi` SDK |

## Response 200 -- Success Schema

Single JSON object. The full schema is mirrored verbatim from the enriched
documentation at
`documentation/api/orgs/GET_orgs_org_id_nacportals_nacportal_id.md`.

| Field | Type | Notes |
|-------|------|-------|
| `id` | string (UUID) | Portal UUID; matches the `nacportal_id` path parameter. **Primary key with `org_id`.** |
| `name` | string | Display name, e.g. `"get-wifi"` |
| `type` | string | enum: `guest_admin`, `guest_portal`, `marvis_client` |
| `access_type` | string | Only when `type==marvis_client`. enum: `wireless`, `wireless+wired` |
| `ssid` | string | Associated SSID, e.g. `"Corp"` |
| `eap_type` | string | enum: `wpa2`, `wpa3` |
| `cert_expire_time` | integer | Days, e.g. `365` |
| `expiry_notification_time` | integer | Days |
| `notify_expiry` | boolean | Phase-2 notification flag |
| `enable_telemetry` | boolean | Telemetry on/off |
| `bg_image_url` | string | Background image URL |
| `template_url` | string | Portal HTML template URL |
| `thumbnail_url` | string (readOnly) | Server-generated thumbnail URL |
| `tos` | string | Terms-of-service text or URL |
| `ui_url` | string (readOnly) | When `auth==guest_admin`, the guest-admin login URL |
| `portal_authorize_url` | string (readOnly) | When `type==guest_portal` and `portal.auth==external`, the callback URL |
| `portal_authorize_jwt_secret` | string (readOnly) | **Sensitive.** When `type==guest_portal` and `portal.auth==external`, the JWT signing secret |
| `portal_sso_url` | string (readOnly) | ACS URL when SSO is enabled |
| `portal` | object | Guest-portal block; see sub-schema below |
| `portal.auth` | string | enum: `external`, `multi`, `none` |
| `portal.expire` | integer | Guest-session expiry minutes when `auth==none` or `multi` |
| `portal.external_portal_url` | string | When `auth==external`, external auth URL |
| `portal.force_reconnect` | boolean | Disconnect client to force reauth |
| `portal.forward` | boolean | Forward after auth |
| `portal.forward_url` | string | Forward target URL |
| `portal.max_num_devices` | integer (0-100) | Per-guest device cap; 0 = unlimited |
| `portal.privacy` | boolean | Show privacy policy |
| `sso` | object | SAML SSO block; see sub-schema below. May be absent |
| `sso.idp_cert` | string | **Sensitive.** IdP signing certificate (PEM) |
| `sso.idp_sign_algo` | string | enum: `sha1`, `sha256`, `sha384`, `sha512` |
| `sso.idp_sso_url` | string | IdP SSO endpoint |
| `sso.issuer` | string | SAML issuer URL |
| `sso.nameid_format` | string | e.g. `email` |
| `sso.use_sso_role_for_cert` | boolean | Inject role into cert subject |
| `sso.sso_role_matching` | array of object | Zero or more role-matching rules |
| `sso.sso_role_matching[].assigned` | string | Role assigned on match, e.g. `user` |
| `sso.sso_role_matching[].match` | string | SAML attribute value, e.g. `Student` |
| `additional_cacerts` | array of string | **Sensitive.** Extra trust-anchor CAs (PEM) |
| `additional_nac_server_name` | array of string | Extra NAC server hostnames |

### Example Response Fragment

```json
{
  "id": "51908ea7-dea7-4581-a578-f7320c4d5216",
  "name": "get-wifi",
  "type": "guest_portal",
  "ssid": "Corp",
  "eap_type": "wpa2",
  "cert_expire_time": 365,
  "portal": {
    "auth": "external",
    "external_portal_url": "https://yourorg.com/external-guest-portal",
    "forward": true,
    "forward_url": "https://yourorg.com/guest-portal-redirect",
    "max_num_devices": 10,
    "privacy": true
  },
  "portal_authorize_url": "https://guest-mistnac.mist.com/callback/be22bba7-8e22-e1cf-5185-b880816fe2cf/authorize",
  "portal_authorize_jwt_secret": "<REDACTED-IN-LOGS>",
  "portal_sso_url": "https://guest-mistnac.mist.com/callback/be22bba7-8e22-e1cf-5185-b880816fe2cf/acs",
  "sso": {
    "idp_sso_url": "https://yourorg.onelogin.com/trust/saml2/http-post/sso/138130",
    "issuer": "https://app.onelogin.com/saml/metadata/138130",
    "idp_sign_algo": "sha256",
    "nameid_format": "email",
    "idp_cert": "<REDACTED-IN-LOGS>",
    "use_sso_role_for_cert": true,
    "sso_role_matching": [
      { "assigned": "user", "match": "Student" }
    ]
  },
  "additional_nac_server_name": ["nac1.corp.com", "nac2.corp.com"]
}
```

## Error Responses and MistHelper Handling

| Status | Mist meaning | MistHelper handling |
|--------|--------------|---------------------|
| **400** | Bad Syntax | `mistapi` raises; MistHelper logs `ERROR Bad request for getOrgNacPortal: <reason>` (no traceback to user) and returns. Typical cause is a malformed UUID -- the UUID-shape regex gate in the new method prevents this case in practice. |
| **401** | Unauthorized | `mistapi` raises; MistHelper logs `ERROR Unauthorized: check MIST_API_TOKEN in .env` and returns. Token is never echoed. |
| **403** | Permission Denied | `mistapi` raises; MistHelper logs `WARNING Permission denied for org %s nacportal %s` and returns. |
| **404** | Not found | `mistapi` returns an empty / error payload; MistHelper logs `WARNING NAC portal %s not found in org %s` and returns without writing any row. |
| **429** | Too Many Requests | The adaptive delay system (`delay_metrics.json` + `tuning_data.json`) increases back-off automatically; the SDK's retry policy applies. No manual intervention required. |

In all error paths the method returns control to the menu loop without
raising. No stack trace is shown to the user. `logging.exception(...)` is
used only for unexpected exceptions outside the documented status codes.

## mistapi Python Call Signature

The exact SDK call used by the new menu method:

```python
import mistapi
from mistapi.api.v1.orgs import nac_portals

# `apisession` is the existing `mistapi.APISession` instance held by the
# MistHelper class. The two path parameters are passed positionally in the
# documented order (org_id first, nacportal_id second).
response = nac_portals.getOrgNacPortal(
    apisession,        # mistapi.APISession -- carries token, host, retry policy
    org_id,            # str -- Mist org UUID
    nacportal_id,      # str -- Mist NAC portal UUID
)

# `response` is mistapi.api_response.APIResponse.
# `response.status_code` -- HTTP status returned by the API.
# `response.data`        -- dict, the parsed JSON body (single object, not a list).
# `response.raw_data`    -- str, the raw body text (preserved for debugging).
# `response.next`        -- str | None, set when the endpoint paginates (None here).
```

The wrapper method `export_org_nac_portal()` then flattens `response.data`
into the three entities documented in [../data-model.md](../data-model.md)
and calls
`DataExporter.write_with_format_selection(rows, "org_nac_portal",
api_function_name="getOrgNacPortal")` to persist the result.
