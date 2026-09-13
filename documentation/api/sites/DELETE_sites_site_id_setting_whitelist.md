# deleteSiteWirelessClientsAllowlist

> deleteSiteWirelessClientsAllowlist

## HTTP

`DELETE /api/v1/sites/{site_id}/setting/whitelist`

## Description

Delete Site Whitelist Station Clients

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

`mistapi.api.v1.sites.setting.deleteSiteWirelessClientsAllowlist()`

## Usage Context

Removes a MAC address from the site’s whitelist. Revokes explicit allow for that device.

## Gotchas

- The device may be denied access if it matches a blacklist or NAC rule.

## Related Endpoints

- [POST_sites_site_id_setting_whitelist.md](POST_sites_site_id_setting_whitelist.md) — Add to whitelist
- [GET_sites_site_id_setting.md](GET_sites_site_id_setting.md) — View site settings

## MistHelper Notes

Not currently used by MistHelper directly.
