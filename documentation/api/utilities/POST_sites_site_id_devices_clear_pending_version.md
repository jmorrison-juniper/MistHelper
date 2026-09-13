# clearSiteMultipleDevicePendingVersion

> clearSiteMultipleDevicePendingVersion

## HTTP

`POST /api/v1/sites/{site_id}/devices/clear_pending_version`

## Description

Clear device pending fw version (Available on Junos OS EX2300-, EX3400-, EX4000-, EX4100-, EX4400- devices)

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

`mistapi.api.v1.utilities.lan.clearSiteMultipleDevicePendingVersion()`

## Usage Context

Clears the pending firmware version flag on multiple devices at a site. Removes scheduled upgrades from all targeted devices without affecting their current firmware.

## Gotchas

- Only clears the pending upgrade marker; currently installed firmware is unaffected.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_clear_pending_version.md](POST_sites_site_id_devices_device_id_clear_pending_version.md) — Clear pending version on single device
- [POST_sites_site_id_devices_upgrade.md](POST_sites_site_id_devices_upgrade.md) — Start a new upgrade

## MistHelper Notes

Not currently used by MistHelper via REST API.
