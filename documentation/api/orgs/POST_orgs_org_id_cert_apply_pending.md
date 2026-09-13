# rotateOrgCertificate

> rotateOrgCertificate

## HTTP

`POST /api/v1/orgs/{org_id}/cert/apply_pending`

## Description

Replace the current org cert with the pending cert generated previously

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

`mistapi.api.v1.orgs.cert.rotateOrgCertificate()`

## Usage Context

Applies pending certificate changes to the organization.

## Gotchas

- This triggers a certificate rollout which may affect active connections.

## Related Endpoints

- [POST_orgs_org_id_cert_regenerate.md](POST_orgs_org_id_cert_regenerate.md) — Regenerate cert
- [GET_orgs_org_id_cert.md](GET_orgs_org_id_cert.md) — Get cert details

## MistHelper Notes

Not currently used by MistHelper directly.
