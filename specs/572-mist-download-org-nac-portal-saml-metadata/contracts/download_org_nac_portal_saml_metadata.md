# Contract: downloadOrgNacPortalSamlMetadata

**Branch**: `572-mist-download-org-nac-portal-saml-metadata`
**Date**: 2026-06-29
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_nacportals_nacportal_id_saml_metadata.xml.md`

This file is the authoritative HTTP + SDK contract for the new menu item.
It is derived from the enriched per-endpoint OpenAPI documentation and
must remain consistent with that file.

## 1. HTTP Contract

| Element                | Value                                                                       |
|------------------------|-----------------------------------------------------------------------------|
| Method                 | `GET`                                                                       |
| URL template           | `https://{MIST_HOST}/api/v1/orgs/{org_id}/nacportals/{nacportal_id}/saml_metadata.xml` |
| Host (example)         | `api.mist.com` (US), `api.eu.mist.com` (EU), `api.gc1.mist.com` (Canada)    |
| Authentication header  | `Authorization: Token {MIST_API_TOKEN}` -- mistapi sets this automatically  |
| Accept header          | `application/xml` (set by mistapi)                                          |
| Request body           | None                                                                        |
| Pagination             | Not paginated                                                               |
| Rate limit             | Standard Mist API limit: 5000 calls / hour / token; 429 on overage          |

### Path parameters (both required)

| Name           | Type   | Format     | Notes                                                |
|----------------|--------|------------|------------------------------------------------------|
| `org_id`       | string | Mist UUID  | The organization that owns the NAC portal.           |
| `nacportal_id` | string | Mist UUID  | The NAC portal whose SAML SP metadata is requested.  |

### Query parameters

_None._

### Request headers (controlled by mistapi)

| Header          | Value                              | Notes                                  |
|-----------------|------------------------------------|----------------------------------------|
| `Authorization` | `Token <MIST_API_TOKEN>`           | Loaded from `.env` by `APISession`.    |
| `Accept`        | `application/xml`                  | mistapi default for `.xml` endpoints.  |
| `User-Agent`    | `mistapi/<version>`                | mistapi default.                       |

## 2. Response (200 OK)

The 200 response body is the SAML 2.0 Service Provider metadata XML
document for the NAC portal. The enriched doc declares the schema as
`{"type": "string", "description": "File", "contentEncoding": "base64"}`
-- in practice the server returns the body as `application/xml` and
mistapi exposes it through `APIResponse.data` as a UTF-8 string (or
bytes on some mistapi versions; the implementation handles both).

### Example response body

```xml
<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                     entityID="https://api.mist.com/api/v1/saml/5hdF5g/login"
                     validUntil="2027-10-12T21:59:01Z"
                     xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
    <md:SPSSODescriptor AuthnRequestsSigned="false" WantAssertionsSigned="true"
                        protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:SingleLogoutService
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            Location="https://api.mist.com/api/v1/saml/5hdF5g/logout" />
        <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified</md:NameIDFormat>
        <md:AssertionConsumerService
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            Location="https://api.mist.com/api/v1/saml/5hdF5g/login"
            index="0" isDefault="true"/>
        <md:AttributeConsumingService index="0">
            <md:ServiceName xml:lang="en-US">Mist</md:ServiceName>
            <md:RequestedAttribute Name="Role"
                NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:basic"
                isRequired="true"/>
            <md:RequestedAttribute Name="FirstName"
                NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:basic"
                isRequired="false"/>
            <md:RequestedAttribute Name="LastName"
                NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:basic"
                isRequired="false"/>
        </md:AttributeConsumingService>
    </md:SPSSODescriptor>
</md:EntityDescriptor>
```

### Fields extracted by MistHelper

MistHelper does not flatten the entire document. It extracts only the
attributes useful for cross-portal queries:

| XML location                          | Stored as       | Type | Notes                                  |
|---------------------------------------|-----------------|------|----------------------------------------|
| `/EntityDescriptor/@entityID`         | `entity_id`     | TEXT | Stable SP identifier (typically URL).  |
| `/EntityDescriptor/@validUntil`       | `valid_until`   | TEXT | ISO-8601 UTC expiry timestamp.         |
| _whole document_                      | `metadata_xml`  | TEXT | Verbatim body for IdP re-import.       |
| _byte length of whole document_       | `metadata_bytes`| INT  | Observability only.                    |

See [data-model.md](../data-model.md) for the full row schema and DDL.

## 3. Error Responses & MistHelper Handling

| Status | Meaning per Mist                                                                 | MistHelper handling                                                                                 |
|--------|----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax                                                                       | Log WARNING with the upstream message; return early; no traceback.                                  |
| 401    | Unauthorized                                                                     | Log WARNING ("API token invalid or expired -- check `.env`"); return early; no traceback.           |
| 403    | Permission Denied                                                                | Log WARNING ("Token lacks Org Read on this portal"); return early; no traceback.                    |
| 404    | NAC portal or org not found                                                      | Log WARNING ("Org/portal not found -- check UUIDs"); return early. **No file is written on 404.**   |
| 429    | Rate limit exceeded (5000 calls / hour / token)                                  | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off; mistapi auto-retries.  |
| 5xx    | Upstream server error                                                            | Log ERROR with traceback via `logging.exception`; the existing retry layer re-tries per config.     |

The API token is **never** logged in any branch above.

## 4. mistapi Python Call Signature

The mistapi SDK exposes the endpoint as a free function in the
`mistapi.api.v1.orgs.nac_portals` module. MistHelper invokes it as:

```python
import mistapi
from mistapi.api.v1.orgs import nac_portals  # SDK module per enriched doc

response = nac_portals.downloadOrgNacPortalSamlMetadata(
    self.apisession,   # mistapi.APISession bootstrapped from .env
    org_id,            # str  -- Mist UUID
    nacportal_id,      # str  -- Mist UUID
)

# response is mistapi.APIResponse
# response.status_code -> int (200 on success)
# response.data        -> str | bytes (the XML body)
# response.headers     -> dict
```

### Notes

- The SDK function name is camelCase (`downloadOrgNacPortalSamlMetadata`),
  matching the operationId. The module path is snake_case
  (`nac_portals`) per mistapi convention.
- `response.data` may be `str` or `bytes` depending on mistapi version.
  The implementation normalizes to `str` via
  `data.decode('utf-8')` when `isinstance(data, bytes)`.
- No keyword arguments are accepted (the endpoint has no query
  parameters). Passing extras would raise `TypeError` at call time.

## 5. Conformance Checklist

- [x] HTTP method, path, and params match the OpenAPI doc.
- [x] Authentication header is supplied by mistapi (`Token <token>`).
- [x] No request body.
- [x] 200 body is treated as opaque XML (parsed only for two attrs).
- [x] Errors 400 / 401 / 403 / 404 / 429 / 5xx are handled per the table
      above; the API token never appears in log output.
- [x] mistapi SDK call signature matches section 4.
- [x] PK strategy registration matches [data-model.md](../data-model.md).
