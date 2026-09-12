# clearOrgCertificates

> clearOrgCertificates

## HTTP

`POST /api/v1/orgs/{org_id}/cert/regenerate`

## Description

Clear Org Certificates

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

`mistapi.api.v1.orgs.cert.clearOrgCertificates()`

## Usage Context

Regenerates the organization certificate.

## Gotchas

- Certificate regeneration requires applying pending changes afterward.
- May disrupt active device connections during rollout.

## Related Endpoints

- [POST_orgs_org_id_cert_apply_pending.md](POST_orgs_org_id_cert_apply_pending.md) — Apply pending cert
- [GET_orgs_org_id_cert.md](GET_orgs_org_id_cert.md) — Get cert details

## MistHelper Notes

Not currently used by MistHelper directly.
