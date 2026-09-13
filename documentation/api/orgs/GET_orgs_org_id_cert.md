# listOrgCertificates

> listOrgCertificates

## HTTP

`GET /api/v1/orgs/{org_id}/cert`

## Description

Get Org Certificates

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

OK

```json
{
  "type": "object",
  "properties": {
    "cert": {
      "type": "string"
    },
    "pending_cert": {
      "type": "string"
    },
    "pending_cert_expiry": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "cert"
  ],
  "description": "If the current Org CA certificate is set to expire within 30 days, a pending certificate will be returned along with the expected auto-renewal timestamp."
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

`mistapi.api.v1.orgs.cert.listOrgCertificates()`

## Usage Context

Retrieves the organization's certificate for device authentication.

## Gotchas

- Used for RADIUS/NAC certificate-based authentication.

## Related Endpoints

- [GET_orgs_org_id_crl.md](GET_orgs_org_id_crl.md) — Certificate Revocation List
- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Org settings

## MistHelper Notes

Not currently used by MistHelper directly.
