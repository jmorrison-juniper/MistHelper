# Endpoint Contract: GetOrgNacPortalSamlMetadata

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_nacportals_nacportal_id_saml_metadata.md`
**Date**: 2026-06-30

## HTTP Contract

| Attribute       | Value                                                                       |
|-----------------|-----------------------------------------------------------------------------|
| **Method**      | `GET`                                                                       |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/nacportals/{nacportal_id}/saml_metadata` |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs NAC Portals`                                                          |
| **operationId** | `getOrgNacPortalSamlMetadata`                                               |

### Path Parameters

| Name           | Type          | Required | Description |
|----------------|---------------|----------|-------------|
| `org_id`       | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |
| `nacportal_id` | string (UUID) | Yes      | NAC Portal UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. Obtain via the bulk `listOrgNacPortals` menu item. |

### Query Parameters

None. This endpoint has no query parameters.

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

Content-Type: `application/json`

```json
{
  "acs_url": "https://api.mist.com/api/v1/saml/llDfa13f/login",
  "entity_id": "https://api.mist.com/api/v1/saml/llDfa13f/login",
  "logout_url": "https://api.mist.com/api/v1/saml/llDfa13f/logout",
  "metadata": "<?xml version=\"1.0\" encoding=\"UTF-8\"?><md:EntityDescriptor xmlns:md=\"urn:oasis:names:tc:SAML:2.0:metadata\" entityID=\"https://api.mist.com/api/v1/saml/llDfa13f/login\" validUntil=\"2027-10-12T21:59:01Z\" xmlns:ds=\"http://www.w3.org/2000/09/xmldsig#\"><md:SPSSODescriptor AuthnRequestsSigned=\"false\" WantAssertionsSigned=\"true\" protocolSupportEnumeration=\"urn:oasis:names:tc:SAML:2.0:protocol\"><md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified</md:NameIDFormat><md:AssertionConsumerService Binding=\"urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST\" Location=\"https://api.mist.com/api/v1/saml/llDfa13f/login\" index=\"0\" isDefault=\"true\"/></md:SPSSODescriptor></md:EntityDescriptor>",
  "scim_base_url": "https://scim.nac-staging.mistsys.com/S_41b2525a-e8b8-4809-8168-f1d8dcbe9735/azure/4d72b1dc-7503-4717-81ea-80d0125b886e"
}
```

| Field           | Type   | Required in 200 | Description |
|-----------------|--------|-----------------|-------------|
| `acs_url`       | string | conditional     | Assertion Consumer Service URL. Present when parent NAC portal `idp_type == saml`. Read-only. |
| `entity_id`     | string | conditional     | SAML Service-Provider entity ID URL. Present when `idp_type == saml`. Read-only. |
| `logout_url`    | string | conditional     | Single Logout URL. Present when `idp_type == saml`. Read-only. |
| `metadata`      | string | conditional     | Embedded SP XML metadata document (raw XML string). Present when `idp_type == saml`. Read-only. Typically a few KB. |
| `scim_base_url` | string | conditional     | SCIM 2.0 base URL for the portal. Present when `idp_type == oauth` and `scim_enabled == true`. Mutually exclusive with the SAML fields above. |

All top-level fields are optional in the schema. In practice the parent NAC
portal's `idp_type` determines which subset is present. MistHelper stores every
field as-is (nulls preserved) plus a derived `idp_flavor` column
(`saml` / `oauth` / `unknown`) for cheap SQL filtering.

### Error Responses

| Status | Mist Description                                                       | MistHelper Handling |
|--------|------------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                             | Log `WARNING` ("Mist returned 400 -- check org_id / nacportal_id format"), no traceback, return early. |
| 401    | Unauthorized                                                           | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                      | Log `ERROR` ("Mist 403 -- token lacks read access to org %s NAC portal %s", org_id, nacportal_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                         | Log `WARNING` ("No SAML metadata for NAC portal %s in org %s -- portal missing or not SAML-configured", nacportal_id, org_id). Treat as empty result and write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)           | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is
never included in any log message, even at `DEBUG`. The `metadata` XML string
is never echoed at any log level; only its length is logged.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.orgs.nacportals import saml_metadata as saml_metadata_module

apisession = mistapi.APISession(
    host=os.environ["MIST_HOST"],
    apitoken=os.environ["MIST_API_TOKEN"],
)
apisession.login()

# Retrieve SAML metadata for a specific NAC portal in a specific org.
response = saml_metadata_module.getOrgNacPortalSamlMetadata(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
    nacportal_id="4d72b1dc-7503-4717-81ea-80d0125b886e",
)

# Access the parsed body:
body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/orgs/{org_id}/nacportals/{nacportal_id}/saml_metadata` ->
  `mistapi.api.v1.orgs.nacportals.saml_metadata`). The enriched per-endpoint
  doc lists the SDK as
  `mistapi.api.v1.orgs.nac_portals.getOrgNacPortalSamlMetadata()` (with an
  underscore), but MistHelper's existing usage at `MistHelper.py:12614`
  already imports the URL-matching `nacportals` variant (no underscore) for
  `listOrgNacPortals`. Following the spec.md and the existing precedent, the
  URL-based path is canonical. Final verification happens at implementation
  via `python -c "from mistapi.api.v1.orgs.nacportals import saml_metadata; help(saml_metadata)"`.
- `response.data` is `None` only when the HTTP response had no body (rare).
  MistHelper normalizes this to `{}` before flattening.
- Both path parameters are positional in the SDK signature; there are no
  query parameters and no request body to pass.
- The XML `metadata` field arrives as a plain Python string. MistHelper stores
  it verbatim in the `metadata` TEXT column; downstream consumers that want
  the raw XML can `SELECT metadata FROM org_nac_portal_saml_metadata WHERE
  org_id = ? AND nacportal_id = ?` and dump it to a file. The response does
  *not* need XML parsing inside MistHelper.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No
`limit`/`page` parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No
endpoint-specific tuning required for this contract.
