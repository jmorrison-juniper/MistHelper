# Endpoint Contract: getMspSso

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/msps/GET_msps_msp_id_ssos_sso_id.md`
**Date**: 2026-06-29

## HTTP Contract

| Attribute       | Value                                                |
|-----------------|------------------------------------------------------|
| **Method**      | `GET`                                                |
| **URL**         | `https://{mist_host}/api/v1/msps/{msp_id}/ssos/{sso_id}` |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `MSPs SSO`                                           |
| **operationId** | `getMspSso`                                          |

### Path Parameters

| Name     | Type          | Required | Description |
|----------|---------------|----------|-------------|
| `msp_id` | string (UUID) | Yes      | MSP UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |
| `sso_id` | string (UUID) | Yes      | SSO/IdP record UUID within the MSP. Validated client-side via `is_valid_uuid()` before the call. |

### Query Parameters

None.

### Request Headers

| Header           | Value                  | Notes |
|------------------|------------------------|-------|
| `Authorization`  | `Token <api_token>`    | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`         | `application/json`     | Default for mistapi SDK. |
| `User-Agent`     | `mistapi/<version>`    | Set by SDK. |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

Single JSON object describing the SSO. The discriminator field `idp_type`
determines which conditional field groups are populated. The example below
shows a SAML configuration; LDAP / OAuth / mxedge_proxy / OpenRoaming
responses replace the conditional block with their respective fields.

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "msp_id": "b9d42c2e-88ee-41f8-b798-f009ce7fe909",
  "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "site_id": "441a1214-6928-442a-8e92-e1d34b8ec6a6",
  "name": "Corp-SAML",
  "idp_type": "saml",
  "domain": "s4t5vwv8",
  "created_time": 1719500000,
  "modified_time": 1719600000,
  "idp_sso_url": "https://idp.example.com/sso",
  "idp_sign_algo": "sha256",
  "idp_cert": "-----BEGIN CERTIFICATE-----\\nMII...-----END CERTIFICATE-----",
  "issuer": "https://idp.example.com/",
  "nameid_format": "email",
  "role_attr_from": "Role",
  "ignore_unmatched_roles": false,
  "default_role": "viewer",
  "custom_logout_url": "https://idp.example.com/logout"
}
```

### Response Fields (complete list)

| Field                       | Type              | Notes |
|-----------------------------|-------------------|-------|
| `id`                        | string (UUID)     | Read-only, server-issued. Primary key for MistHelper persistence. |
| `msp_id`                    | string (UUID)     | Read-only. |
| `org_id`                    | string (UUID)     | Read-only. May be omitted when SSO is MSP-scoped only. |
| `site_id`                   | string (UUID)     | Read-only. May be omitted. |
| `name`                      | string            | Required by schema. |
| `idp_type`                  | string enum       | `saml`/`ldap`/`mxedge_proxy`/`oauth`/`openroaming`. Discriminator. |
| `domain`                    | string            | Read-only. Used to build SAML ACS / SLO URLs. |
| `created_time`              | number (epoch s)  | Read-only. |
| `modified_time`             | number (epoch s)  | Read-only. |
| **SAML fields** (when `idp_type=saml`) | | |
| `idp_cert`                  | string (PEM)      | **Sensitive**. |
| `idp_sign_algo`             | string enum       | `sha1`/`sha256`/`sha384`/`sha512`. |
| `idp_sso_url`               | string (URL)      |  |
| `issuer`                    | string            |  |
| `nameid_format`             | string enum       | `email`/`unspecified`. |
| `custom_logout_url`         | string (URL)      |  |
| `default_role`              | string            |  |
| `role_attr_extraction`      | string            | Custom parsing scheme. |
| `role_attr_from`            | string            | Defaults to `Role`. |
| `ignore_unmatched_roles`    | boolean           |  |
| **LDAP fields** (when `idp_type=ldap`) | | |
| `ldap_type`                 | string enum       | `azure`/`custom`/`google`/`okta`/`ping_identity`. |
| `ldap_base_dn`              | string            |  |
| `ldap_bind_dn`              | string            |  |
| `ldap_bind_password`        | string            | **Sensitive**. |
| `ldap_cacerts`              | string[]          | PEM certs. **Sensitive** in aggregate. |
| `ldap_client_cert`          | string (PEM)      | **Sensitive**. |
| `ldap_client_key`           | string (PEM)      | **Sensitive**. |
| `ldap_server_hosts`         | string[]          | Hostnames or IPs. |
| `ldap_resolve_groups`       | boolean           |  |
| `ldap_group_attr`           | string            | Custom only. Defaults to `memberOf`. |
| `ldap_group_dn`             | string            | Custom only. Defaults to `base_dn`. |
| `ldap_user_filter`          | string            | Custom only. |
| `group_filter`              | string            | Custom only. |
| `member_filter`             | string            | Custom only. |
| **OAuth fields** (when `idp_type=oauth`) | | |
| `oauth_type`                | string enum       | `azure`/`azure-gov`/`okta`/`ping_identity`. |
| `oauth_cc_client_id`        | string            |  |
| `oauth_cc_client_secret`    | string (RSA key)  | **Sensitive**. |
| `oauth_ropc_client_id`      | string            |  |
| `oauth_ropc_client_secret`  | string            | **Sensitive**. |
| `oauth_discovery_url`       | string (URL)      |  |
| `oauth_tenant_id`           | string            |  |
| `oauth_provider_domain`     | string            | Okta region domain. |
| `oauth_ping_identity_region`| string enum       | `us`/`ca`/`eu`/`asia`/`au`. |
| `scim_enabled`              | boolean           |  |
| `scim_secret_token`         | string            | **Sensitive**. |
| **mxedge_proxy** (when `idp_type=mxedge_proxy`) | | |
| `mxedge_proxy.mxcluster_id` | string (UUID)     |  |
| `mxedge_proxy.operator_name`| string            |  |
| `mxedge_proxy.proxy_hosts`  | string[]          |  |
| `mxedge_proxy.ssids`        | string[]          |  |
| `mxedge_proxy.auth_servers` | object[]          | RADIUS auth servers with `secret`. **Sensitive**. |
| `mxedge_proxy.acct_servers` | object[]          | RADIUS acct servers with `secret`. **Sensitive**. |
| **OpenRoaming** (when `idp_type=openroaming`) | | |
| `openroaming.ssids`         | string[]          | Required. |
| `openroaming.wba_cert`      | string (PEM)      | Optional. |

### Error Responses

| Status | Mist Description                                              | MistHelper Handling |
|--------|---------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                    | Log `WARNING` ("Mist returned 400 -- check msp_id/sso_id format"). No traceback, return early. |
| 401    | Unauthorized                                                  | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                             | Log `ERROR` ("Mist 403 -- token lacks MSP read scope for msp %s", msp_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                | Log `WARNING` ("No SSO %s found in MSP %s", sso_id, msp_id). Treat as empty result and write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)  | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token,
certificates, passwords, and secret tokens are never included in any log
message, even at `DEBUG`. See `data-model.md` for the explicit sensitive-
field exclusion list.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.msps import ssos as msps_ssos_module

apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

response = msps_ssos_module.getMspSso(
    apisession,
    msp_id="b9d42c2e-88ee-41f8-b798-f009ce7fe909",
    sso_id="53f10664-3ce8-4c27-b382-0ef66432349f",
)

# Access the parsed body:
body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/msps/{msp_id}/ssos/{sso_id}` -> `mistapi.api.v1.msps.ssos`). The
  enriched per-endpoint doc lists the SDK module as
  `mistapi.api.v1.msps.sso.getMspSso()` (singular `sso`), but the URL token
  is plural (`ssos`) and the spec.md (authoritative feature contract) names
  the plural path. Final verification at implementation time via
  `python -c "from mistapi.api.v1.msps import ssos; help(ssos.getMspSso)"`.
- `response.data` is `None` only when the HTTP response had no body (rare).
  MistHelper normalizes this to `{}` before flattening.
- Both path parameters are positional in the SDK call; passing by keyword is
  equivalent. Neither has a default; both are required.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No
`limit`/`page` parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No endpoint-
specific tuning required for this contract.
