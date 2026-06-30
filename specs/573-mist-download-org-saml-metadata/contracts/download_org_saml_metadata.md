# Endpoint Contract: downloadOrgSamlMetadata

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_ssos_sso_id_metadata.xml.md`
**Date**: 2026-06-29

## HTTP Contract

| Attribute       | Value                                       |
|-----------------|---------------------------------------------|
| **Method**      | `GET`                                       |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/ssos/{sso_id}/metadata.xml` |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs SSO`                                  |
| **operationId** | `downloadOrgSamlMetadata`                   |

### Path Parameters

| Name     | Type          | Required | Description                                                                                  |
|----------|---------------|----------|----------------------------------------------------------------------------------------------|
| `org_id` | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |
| `sso_id` | string (UUID) | Yes      | SSO configuration UUID under the org. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

None.

### Request Headers

| Header          | Value                                  | Notes |
|-----------------|----------------------------------------|-------|
| `Authorization` | `Token <api_token>`                    | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`        | `application/xml, text/xml, */*`       | Set by SDK; the endpoint returns XML, not JSON. |
| `User-Agent`    | `mistapi/<version>`                    | Set by SDK. |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

The response body is a SAML 2.0 `<md:EntityDescriptor>` XML document describing the
Mist-side Service Provider for the given SSO configuration. Content-Type is
`application/xml` (or equivalent). MistHelper stores the body verbatim.

Example body (truncated for readability; the full example lives in `spec.md`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor
    xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    entityID="https://api.mist.com/api/v1/saml/5hdF5g/login"
    validUntil="2027-10-12T21:59:01Z"
    xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
  <md:SPSSODescriptor AuthnRequestsSigned="false"
                      WantAssertionsSigned="true"
                      protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                            Location="https://api.mist.com/api/v1/saml/5hdF5g/logout" />
    <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified</md:NameIDFormat>
    <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                                 Location="https://api.mist.com/api/v1/saml/5hdF5g/login"
                                 index="0" isDefault="true" />
    <md:AttributeConsumingService index="0">
      <md:ServiceName xml:lang="en-US">Mist</md:ServiceName>
      <md:RequestedAttribute Name="Role"
                             NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:basic"
                             isRequired="true" />
      <md:RequestedAttribute Name="FirstName"
                             NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:basic"
                             isRequired="false" />
      <md:RequestedAttribute Name="LastName"
                             NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:basic"
                             isRequired="false" />
    </md:AttributeConsumingService>
  </md:SPSSODescriptor>
</md:EntityDescriptor>
```

| Element / Attribute                            | XPath                                                                | Notes |
|------------------------------------------------|----------------------------------------------------------------------|-------|
| `EntityDescriptor/@entityID`                   | `/md:EntityDescriptor/@entityID`                                     | Unique SAML SP entity ID (URL). MistHelper extracts to `entity_id` column (best-effort). |
| `EntityDescriptor/@validUntil`                 | `/md:EntityDescriptor/@validUntil`                                   | ISO 8601 expiration. MistHelper extracts to `valid_until` column (best-effort). |
| `SPSSODescriptor`                              | `/md:EntityDescriptor/md:SPSSODescriptor`                            | One element; not extracted into columns. |
| `SingleLogoutService/@Location`                | `.../md:SingleLogoutService/@Location`                               | IdP-callable logout endpoint. Not extracted. |
| `AssertionConsumerService/@Location`           | `.../md:AssertionConsumerService/@Location`                          | IdP-callable ACS endpoint. Not extracted. |
| `AttributeConsumingService/md:RequestedAttribute` | `.../md:AttributeConsumingService/md:RequestedAttribute`          | Required + optional SAML attributes. Not extracted. |

The full XML always lives in the `metadata_xml` TEXT column; downstream consumers can
parse it on demand. Only `entity_id` and `valid_until` are surfaced as their own
columns, and both are best-effort -- any parse error leaves them `NULL` and never
fails the row write.

### Error Responses

| Status | Mist Description                                                   | MistHelper Handling |
|--------|--------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                         | Log `WARNING` ("Mist returned 400 -- check org_id/sso_id format"). No traceback. Return early. |
| 401    | Unauthorized                                                       | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                  | Log `ERROR` ("Mist 403 -- token lacks read access to org %s SSO %s", org_id, sso_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist.                    | Log `WARNING` ("No SAML metadata for org %s sso %s", org_id, sso_id). Treat as empty result and write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)       | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is never
included in any log message, even at `DEBUG`. The raw XML body is never logged at
`INFO` or above -- only its byte size and a truncated SHA-256 digest are logged.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.orgs.ssos import metadata_xml as saml_metadata_module

apisession = mistapi.APISession(
    host=os.environ["MIST_HOST"],
    apitoken=os.environ["MIST_API_TOKEN"],
)
apisession.login()

# Single call -- two required path params, no query, no body:
response = saml_metadata_module.downloadOrgSamlMetadata(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
    sso_id="5hdF5g0a-1111-2222-3333-444455556666",
)

# Access the parsed body (XML, not JSON):
body = response.data           # str (or bytes -- MistHelper normalizes to str)
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/orgs/{org_id}/ssos/{sso_id}/metadata.xml` ->
  `mistapi.api.v1.orgs.ssos.metadata_xml`). The `.xml` URL suffix becomes `_xml` in the
  Python module name because dots are illegal in module names. Adjacent endpoints
  under the same URL prefix (e.g. `GET /orgs/{org_id}/ssos/{sso_id}` ->
  `mistapi.api.v1.orgs.ssos.sso`) confirm the URL-based naming convention. Final
  verification happens at implementation via
  `python -c "from mistapi.api.v1.orgs.ssos import metadata_xml; help(metadata_xml)"`.
- `response.data` is `None` only when the HTTP response had no body (404 most often).
  MistHelper's `_normalize_xml_body()` helper coerces `None` to `""`, `bytes` to
  UTF-8-decoded `str`, and passes `str` through unchanged.
- There are no optional query parameters and no request body, so the SDK signature is
  `downloadOrgSamlMetadata(apisession, org_id, sso_id)` -- positional or keyword.

## Pagination

Not paginated. The endpoint returns a single XML document per call. No `limit`/`page`
parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's adaptive
delay system (`delay_metrics.json` per-endpoint state + `tuning_data.json` learning)
governs back-off automatically. No endpoint-specific tuning is required for this
contract -- the call is light (a few KB of XML, one round trip).
