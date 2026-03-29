# clearSiteDevicePendingVersion

> clearSiteDevicePendingVersion

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/clear_pending_version`

## Description

Clear device pending fw version (Available on Junos OS EX2300-, EX3400-, EX4000-, EX4100-, EX4400- devices)

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| device_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

## Errors

| Status | Description |
|--------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.utilities.lan.clearSiteDevicePendingVersion()`

## Usage Context

Clears the pending firmware version flag on a specific device. Removes the scheduled upgrade without reverting the current firmware.

## Gotchas

- Only clears the pending upgrade marker; the currently installed firmware is unaffected.
- The device will no longer attempt to upgrade to the pending version on next reboot.

## Related Endpoints

- [POST_sites_site_id_devices_clear_pending_version.md](POST_sites_site_id_devices_clear_pending_version.md) — Clear pending version for multiple devices
- [POST_sites_site_id_devices_device_id_upgrade.md](POST_sites_site_id_devices_device_id_upgrade.md) — Set a new upgrade target

## MistHelper Notes

Not currently used by MistHelper via REST API.
