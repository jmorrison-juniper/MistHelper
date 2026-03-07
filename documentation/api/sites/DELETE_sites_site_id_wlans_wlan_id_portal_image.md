# deleteSiteWlanPortalImage

> deleteSiteWlanPortalImage

## HTTP

`DELETE /api/v1/sites/{site_id}/wlans/{wlan_id}/portal_image`

## Description

Delete Site WLAN Portal Image

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
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

`mistapi.api.v1.sites.wlans.deleteSiteWlanPortalImage()`

## Usage Context

Deletes the captive portal image (splash page background) for a WLAN. Removes the custom branding graphic.

## Gotchas

- The portal reverts to a default appearance until a new image is uploaded.

## Related Endpoints

- [POST_sites_site_id_wlans_wlan_id_portal_image.md](POST_sites_site_id_wlans_wlan_id_portal_image.md) — Upload portal image
- [GET_sites_site_id_wlans_wlan_id.md](GET_sites_site_id_wlans_wlan_id.md) — Get WLAN details

## MistHelper Notes

Not currently used by MistHelper directly. Menu **49** uses `listSiteWlans`.
