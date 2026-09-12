# deleteSiteWirelessClientsBlocklist

> deleteSiteWirelessClientsBlocklist

## HTTP

`DELETE /api/v1/sites/{site_id}/setting/blacklist`

## Description

Delete Site Blacklist Station Clients

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

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

`mistapi.api.v1.sites.setting.deleteSiteWirelessClientsBlocklist()`

## Usage Context

Removes a MAC address from the site’s blacklist. Allows the device to reconnect.

## Gotchas

- The device can immediately reassociate after removal.

## Related Endpoints

- [POST_sites_site_id_setting_blacklist.md](POST_sites_site_id_setting_blacklist.md) — Add to blacklist
- [GET_sites_site_id_setting.md](GET_sites_site_id_setting.md) — View site settings

## MistHelper Notes

Not currently used by MistHelper directly. `getSiteSetting` is used in Menus **4, 18, 103, 118, 119, 120**.
