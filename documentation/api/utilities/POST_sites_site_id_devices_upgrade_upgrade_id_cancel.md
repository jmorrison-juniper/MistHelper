# cancelSiteDeviceUpgrade

> cancelSiteDeviceUpgrade

## HTTP

`POST /api/v1/sites/{site_id}/devices/upgrade/{upgrade_id}/cancel`

## Description

Best effort to cancel an upgrade. Devices which are already upgraded wont be touched

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| upgrade_id | string | Yes |  |

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

`mistapi.api.v1.utilities.upgrade.cancelSiteDeviceUpgrade()`

## Usage Context

Cancels an in-progress site-level device firmware upgrade. Devices already upgraded remain on the new version.

## Gotchas

- Cancellation is best-effort; devices mid-flash may still complete.

## Related Endpoints

- [GET_sites_site_id_devices_upgrade_upgrade_id.md](GET_sites_site_id_devices_upgrade_upgrade_id.md) — Check upgrade status before cancelling
- [POST_sites_site_id_devices_upgrade.md](POST_sites_site_id_devices_upgrade.md) — Start a new site upgrade

## MistHelper Notes

Used by Menu **90** (`FirmwareManager`) to cancel site-level upgrades.
