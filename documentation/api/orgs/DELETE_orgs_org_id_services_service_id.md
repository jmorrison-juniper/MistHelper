# deleteOrgService

> deleteOrgService

## HTTP

`DELETE /api/v1/orgs/{org_id}/services/{service_id}`

## Description

Delete Org Service

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| service_id | string | Yes |  |

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

`mistapi.api.v1.orgs.services.deleteOrgService()`

## Usage Context

Deletes a service (application definition) from the organization.

## Gotchas

- Ensure no service policies reference this service.

## Related Endpoints

- [GET_orgs_org_id_services.md](GET_orgs_org_id_services.md) — List services
- [POST_orgs_org_id_services.md](POST_orgs_org_id_services.md) — Create service

## MistHelper Notes

Used by MistHelper via `listOrgServices` in Menu 4.
