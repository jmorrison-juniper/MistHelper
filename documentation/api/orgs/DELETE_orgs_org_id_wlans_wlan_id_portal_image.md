# deleteOrgWlanPortalImage

> deleteOrgWlanPortalImage

## HTTP

`DELETE /api/v1/orgs/{org_id}/wlans/{wlan_id}/portal_image`

## Description

Delete Org WLAN Portal Image

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| wlan_id | string | Yes |  |

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

`mistapi.api.v1.orgs.wlans.deleteOrgWlanPortalImage()`

## Usage Context

Deletes the captive portal image for a specific org-level WLAN.

## Gotchas

- The portal reverts to the default image.

## Related Endpoints

- [POST_orgs_org_id_wlans_wlan_id_portal_image.md](POST_orgs_org_id_wlans_wlan_id_portal_image.md) — Upload portal image
- [GET_orgs_org_id_wlans.md](GET_orgs_org_id_wlans.md) — List org WLANs

## MistHelper Notes

Used by MistHelper via `listOrgWlans` in Menus 48, 102, 122.
