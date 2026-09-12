# deleteOrgNacPortal

> deleteOrgNacPortal

## HTTP

`DELETE /api/v1/orgs/{org_id}/nacportals/{nacportal_id}`

## Description

Delete Org NAC Portal

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| nacportal_id | string | Yes |  |

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

`mistapi.api.v1.orgs.nac_portals.deleteOrgNacPortal()`

## Usage Context

Deletes a NAC portal from the organization.

## Gotchas

- Active NAC sessions using this portal are not affected until they expire.

## Related Endpoints

- [GET_orgs_org_id_nacportals.md](GET_orgs_org_id_nacportals.md) — List portals
- [POST_orgs_org_id_nacportals.md](POST_orgs_org_id_nacportals.md) — Create portal

## MistHelper Notes

Used by MistHelper via `listOrgNacPortals` for NAC exports.
