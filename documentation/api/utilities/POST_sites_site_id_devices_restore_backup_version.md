# restoreSiteMultipleDeviceBackupVersion

> restoreSiteMultipleDeviceBackupVersion

## HTTP

`POST /api/v1/sites/{site_id}/devices/restore_backup_version`

## Description

Restore device backup fw version (Available on Junos OS EX4000-, EX4100-, EX4400- devices)

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "device_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": ""
    }
  },
  "required": [
    "device_ids"
  ],
  "description": "Request Body"
}
```

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

`mistapi.api.v1.utilities.lan.restoreSiteMultipleDeviceBackupVersion()`

## Usage Context

Restores multiple devices at a site to their previous backup configuration. Bulk rollback operation for recovering from a bad configuration push.

## Gotchas

- All targeted devices reboot as part of the restoration.
- Only works if devices have stored backup versions.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_restore_backup_version.md](POST_sites_site_id_devices_device_id_restore_backup_version.md) — Restore a single device
- [POST_sites_site_id_devices_device_id_snapshot.md](POST_sites_site_id_devices_device_id_snapshot.md) — Create snapshots before bulk operations

## MistHelper Notes

Not currently used by MistHelper via REST API.
