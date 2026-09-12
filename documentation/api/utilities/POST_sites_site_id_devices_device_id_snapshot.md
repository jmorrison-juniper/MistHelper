# createSiteDeviceSnapshot

> createSiteDeviceSnapshot

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/snapshot`

## Description

Create recovery device snapshot (Available on Junos OS EX2300-, EX3400-, EX4400- devices)

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

`mistapi.api.v1.utilities.lan.createSiteDeviceSnapshot()`

## Usage Context

Creates a configuration snapshot of a device. Captures the current running state as a backup point that can be restored later.

## Gotchas

- No known gotchas; non-disruptive operation.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_restore_backup_version.md](POST_sites_site_id_devices_device_id_restore_backup_version.md) — Restore from a snapshot

## MistHelper Notes

Not currently used by MistHelper via REST API.
