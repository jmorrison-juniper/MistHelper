# getOrgSamlMetadata

> getOrgSamlMetadata

## HTTP

`GET /api/v1/orgs/{org_id}/ssos/{sso_id}/metadata`

## Description

Get Org SAML Metadata

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| sso_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "acs_url": {
      "type": "string",
      "description": "If `idp_type`==`saml`",
      "readOnly": true,
      "examples": [
        "https://api.mist.com/api/v1/saml/llDfa13f/login"
      ]
    },
    "entity_id": {
      "type": "string",
      "description": "If `idp_type`==`saml`",
      "readOnly": true,
      "examples": [
        "https://api.mist.com/api/v1/saml/llDfa13f/login"
      ]
    },
    "logout_url": {
      "type": "string",
      "description": "If `idp_type`==`saml`",
      "readOnly": true,
      "examples": [
        "https://api.mist.com/api/v1/saml/llDfa13f/logout"
      ]
    },
    "metadata": {
      "type": "string",
      "description": "If `idp_type`==`saml`",
      "readOnly": true,
      "examples": [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?><md:EntityDescriptor xmlns:md=\"urn:oasis:names:tc:SAML:2.0:metadata\" entityID=\"https://api.mist.com/api/v1/saml/llDfa13f/login\" validUntil=\"2027-10-12T21:59:01Z\" xmlns:ds=\"http://www.w3.org/2000/09/xmldsig#\"><md:SPSSODescriptor AuthnRequestsSigned=\"false\" WantAssertionsSigned=\"true\" protocolSupportEnumeration=\"urn:oasis:names:tc:SAML:2.0:protocol\"><md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified</md:NameIDFormat><md:AssertionConsumerService Binding=\"urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST\" Location=\"https://api.mist.com/api/v1/saml/llDfa13f/login\" index=\"0\" isDefault=\"true\"/></md:SPSSODescriptor></md:EntityDescriptor>"
      ]
    },
    "scim_base_url": {
      "type": "string",
      "description": "If `idp_type`==`oauth` and `scim_enabled`==`true`",
      "examples": [
        "https://scim.nac-staging.mistsys.com/S_41b2525a-e8b8-4809-8168-f1d8dcbe9735/azure/4d72b1dc-7503-4717-81ea-80d0125b886e"
      ]
    }
  }
}
```

## Errors

| Status | Description |
|--------|-------------|
| 400 | Bad Syntax |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.sso.getOrgSamlMetadata()`

## Usage Context

Retrieves SAML metadata (JSON format) for a specific SSO configuration.

## Gotchas

- Use the `.xml` variant for raw XML metadata needed by IdPs.

## Related Endpoints

- [GET_orgs_org_id_ssos_sso_id_metadata.xml.md](GET_orgs_org_id_ssos_sso_id_metadata.xml.md) — XML metadata
- [GET_orgs_org_id_ssos_sso_id.md](GET_orgs_org_id_ssos_sso_id.md) — SSO config

## MistHelper Notes

Not currently used by MistHelper directly.
