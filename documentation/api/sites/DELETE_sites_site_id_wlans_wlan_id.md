# deleteSiteWlan

> deleteSiteWlan

## HTTP

`DELETE /api/v1/sites/{site_id}/wlans/{wlan_id}`

## Description

Delete Site WLAN

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

`mistapi.api.v1.sites.wlans.deleteSiteWlan()`

## Usage Context

Deletes a WLAN (SSID) from a site. Removes the wireless network and disconnects all associated clients.

## Gotchas

- **DESTRUCTIVE**: All clients on this SSID are immediately disconnected.
- PSKs associated exclusively with this WLAN may become orphaned.

## Related Endpoints

- [GET_sites_site_id_wlans.md](GET_sites_site_id_wlans.md) — List WLANs
- [POST_sites_site_id_wlans.md](POST_sites_site_id_wlans.md) — Create WLAN
- [PUT_sites_site_id_wlans_wlan_id.md](PUT_sites_site_id_wlans_wlan_id.md) — Update WLAN

## MistHelper Notes

Used by Menu **49** (`listSiteWlans`), Menu **102**, and Menu **118** for WLAN management.
