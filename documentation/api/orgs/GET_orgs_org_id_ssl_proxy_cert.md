# getOrgSslProxyCert

> getOrgSslProxyCert

## HTTP

`GET /api/v1/orgs/{org_id}/ssl_proxy_cert`

## Description

Get Org SSL proxy Certificates

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "cert": {
      "type": "string",
      "examples": [
        "-----BEGIN CERTIFICATE-----\\nMIIowDQYJKoZIhvcNAQELBQE\\n-----END CERTIFICATE-----"
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

`mistapi.api.v1.orgs.cert.getOrgSslProxyCert()`

## Usage Context

Retrieves details of the SSL proxy certificate for the organization.

## Gotchas

- SSL proxy certificates are used for SSL inspection on SRX gateways.

## Related Endpoints

- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Full org settings
- [GET_orgs_org_id_cert.md](GET_orgs_org_id_cert.md) — Org certificate

## MistHelper Notes

Not currently used by MistHelper directly.
