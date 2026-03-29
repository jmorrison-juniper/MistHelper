# revokeOrgIssuedClientCertificates

> revokeOrgIssuedClientCertificates

## HTTP

`POST /api/v1/orgs/{org_id}/setting/mist_scep/client_certs/revoke`

## Description

Revoke Issued Client Certificates

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "serial_numbers": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    }
  }
}
```

## Response

### 200

OK

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

`mistapi.api.v1.orgs.scep.revokeOrgIssuedClientCertificates()`

## Usage Context

Revokes SCEP client certificates for Mist NAC.

## Gotchas

- Revocation is immediate and permanent.

## Related Endpoints

- [GET_orgs_org_id_setting_mist_scep_client_certs.md](GET_orgs_org_id_setting_mist_scep_client_certs.md) — Get SCEP certs
- [GET_orgs_org_id_setting_mist_scep.md](GET_orgs_org_id_setting_mist_scep.md) — Get SCEP config

## MistHelper Notes

Not currently used by MistHelper directly.
