# downloadMspSamlMetadata

> downloadMspSamlMetadata

## HTTP

`GET /api/v1/msps/{msp_id}/ssos/{sso_id}/metadata.xml`

## Description

Download MSP SAML Metadata

Example of metadata.xml:
```xml
<?xml version="1.0" encoding="UTF-8"?><md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" entityID="https://api.mist.com/api/v1/saml/5hdF5g/login" validUntil="2027-10-12T21:59:01Z" xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
  <md:SPSSODescriptor AuthnRequestsSigned="false" WantAssertionsSigned="true" protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
      <md:SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" Location="https://api.mist.com/api/v1/saml/5hdF5g/logout" />
      <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified</md:NameIDFormat>
      <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" Location="https://api.mist.com/api/v1/saml/5hdF5g/login" index="0" isDefault="true"/>
      <md:AttributeConsumingService index="0">
          <md:ServiceName xml:lang="en-US">Mist</md:ServiceName>
          <md:RequestedAttribute Name="Role" NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:basic" isRequired="true"/>
          <md:RequestedAttribute Name="FirstName" NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:basic" isRequired="false"/>
          <md:RequestedAttribute Name="LastName" NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:basic" isRequired="false"/>
      </md:AttributeConsumingService>
  </md:SPSSODescriptor>
</md:EntityDescriptor>
```

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |
| sso_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "string",
  "description": "File",
  "contentEncoding": "base64"
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

`mistapi.api.v1.msps.sso.downloadMspSamlMetadata()`

## Usage Context

Downloads the SAML SP metadata for an MSP SSO configuration in standard XML format. Most identity providers accept XML metadata import directly, making this the preferred format for IdP setup.

## Gotchas

- The response is XML, not JSON — handle content type appropriately.
- The metadata URL itself can sometimes be used as the metadata import URL in the IdP configuration.

## Related Endpoints

- [GET_msps_msp_id_ssos_sso_id_metadata.md](GET_msps_msp_id_ssos_sso_id_metadata.md) — Same metadata in JSON format
- [GET_msps_msp_id_ssos_sso_id.md](GET_msps_msp_id_ssos_sso_id.md) — Full SSO configuration details

## MistHelper Notes

Not currently used by MistHelper directly.
