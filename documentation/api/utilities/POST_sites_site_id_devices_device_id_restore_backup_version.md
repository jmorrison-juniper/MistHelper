# restoreSiteDeviceBackupVersion

> restoreSiteDeviceBackupVersion

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/restore_backup_version`

## Description

Restore device backup fw version (Available on Junos OS EX4000-, EX4100-, EX4400- devices)

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

`mistapi.api.v1.utilities.lan.restoreSiteDeviceBackupVersion()`

## Usage Context

Restores a device to a previous backup version of its configuration. Rolls back to a known-good state when current configuration causes issues.

## Gotchas

- The device reboots as part of the restoration process.
- Only works if the device has a previous backup stored.

## Related Endpoints

- [POST_sites_site_id_devices_restore_backup_version.md](POST_sites_site_id_devices_restore_backup_version.md) — Bulk restore for multiple devices
- [POST_sites_site_id_devices_device_id_snapshot.md](POST_sites_site_id_devices_device_id_snapshot.md) — Create a snapshot before restoring

## MistHelper Notes

Not currently used by MistHelper via REST API.
