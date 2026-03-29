# truncateOrgCrlFile

> truncateOrgCrlFile

## HTTP

`POST /api/v1/orgs/{org_id}/crl/truncate`

## Description

By default, all certs used by recently unclaimed devices within 9 month will be included in CRL. If the list grows too big, you can truncate it

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
  "title": "days_number",
  "type": "object",
  "properties": {
    "days": {
      "type": "integer",
      "contentEncoding": "int32",
      "default": 30
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

`mistapi.api.v1.orgs.cert.truncateOrgCrlFile()`

## Usage Context

Truncates (clears) the Certificate Revocation List for the organization.

## Gotchas

- This removes all revoked certificate entries. Use with extreme caution.
- Previously revoked certificates will become valid again.

## Related Endpoints

- [GET_orgs_org_id_crl.md](GET_orgs_org_id_crl.md) — Get CRL
- [GET_orgs_org_id_cert.md](GET_orgs_org_id_cert.md) — Get cert

## MistHelper Notes

Not currently used by MistHelper directly.
