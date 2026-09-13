# listOrgIssuedClientCertificates

> listOrgIssuedClientCertificates

## HTTP

`GET /api/v1/orgs/{org_id}/setting/mist_scep/client_certs`

## Description

Get Issued Client Certificates

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| sso_name_id | string | No |  |  | sso_name_id obtained from NAC Portal |
| serial_number | string | No |  |  | Serial Number of the certificate |
| device_id | string | No |  |  | Device ID |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "title": "issued_client_certificate",
        "type": "object",
        "properties": {
          "cert_provider": {
            "type": "string",
            "examples": [
              "byod"
            ]
          },
          "common_name": {
            "type": "string",
            "examples": [
              "john@corp.com"
            ]
          },
          "created_time": {
            "type": "string",
            "description": "When the certificate has been created",
            "examples": [
              "2025-08-18 10:10:30.949165+00:00"
            ]
          },
          "device_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "00000000-0000-0000-1000-d8695a0f9e61"
            ]
          },
          "expire_time": {
            "type": "string",
            "description": "When the certificate will expire",
            "examples": [
              "2026-08-18 10:06:00+00:00"
            ]
          },
          "serial_number": {
            "type": "string",
            "examples": [
              "91984382552102771A2B3C4E5F224719956718003374658"
            ]
          }
        }
      },
      "description": ""
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

`mistapi.api.v1.orgs.scep.listOrgIssuedClientCertificates()`

## Usage Context

Retrieves SCEP client certificates for the organization.

## Gotchas

- SCEP is used for automatic certificate enrollment for NAC.

## Related Endpoints

- [GET_orgs_org_id_setting_mist_scep.md](GET_orgs_org_id_setting_mist_scep.md) — SCEP settings
- [GET_orgs_org_id_setting_mist_nac_crls.md](GET_orgs_org_id_setting_mist_nac_crls.md) — CRLs

## MistHelper Notes

Not currently used by MistHelper directly.
