# deleteOrgNacPortalImage

> deleteOrgNacPortalImage

## HTTP

`DELETE /api/v1/orgs/{org_id}/nacportals/{nacportal_id}/portal_image`

## Description

Delete background image for NAC Portal


If image is not uploaded or is deleted, NAC Portal will use default image.

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

`mistapi.api.v1.orgs.nac_portals.deleteOrgNacPortalImage()`

## Usage Context

Deletes the portal image from a NAC portal.

## Gotchas

- Portal reverts to default branding after image removal.

## Related Endpoints

- [GET_orgs_org_id_nacportals_nacportal_id.md](GET_orgs_org_id_nacportals_nacportal_id.md) — Portal details
- [POST_orgs_org_id_nacportals_nacportal_id_portal_image.md](POST_orgs_org_id_nacportals_nacportal_id_portal_image.md) — Upload image

## MistHelper Notes

Not currently used by MistHelper directly.
