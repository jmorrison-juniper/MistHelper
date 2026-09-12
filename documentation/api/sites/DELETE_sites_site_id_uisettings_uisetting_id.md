# deleteSiteUiSetting

> deleteSiteUiSetting

## HTTP

`DELETE /api/v1/sites/{site_id}/uisettings/{uisetting_id}`

## Description

Site UI settings

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| uisetting_id | string | Yes |  |

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

`mistapi.api.v1.sites.ui_settings.deleteSiteUiSetting()`

## Usage Context

Deletes a UI settings entry from a site. Removes custom dashboard or UI preferences.

## Gotchas

- Dashboard customizations are lost; UI reverts to defaults.

## Related Endpoints

- [GET_sites_site_id_uisettings.md](GET_sites_site_id_uisettings.md) — List UI settings
- [POST_sites_site_id_uisettings.md](POST_sites_site_id_uisettings.md) — Create UI setting

## MistHelper Notes

Not currently used by MistHelper directly.
