# restartSiteMultipleDevices

> restartSiteMultipleDevices

## HTTP

`POST /api/v1/sites/{site_id}/devices/restart`

## Description

Note that only the devices that are connected will be restarted.

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
    },
    "node": {
      "type": "string",
      "description": "only for SSR: if node is not present, both nodes are restarted. For other devices: node should not be present"
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

`mistapi.api.v1.utilities.common.restartSiteMultipleDevices()`

## Usage Context

Restarts multiple devices at a site. Accepts a list of device MACs or device types to reboot. Use for bulk recovery after site-wide issues.

## Gotchas

- All targeted devices go offline simultaneously — plan for service outage.
- PoE-powered downstream devices also lose power during switch reboots.
- Prefer staggered individual restarts for non-emergency situations.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_restart.md](POST_sites_site_id_devices_device_id_restart.md) — Restart a single device

## MistHelper Notes

Used by Menu **91-93** for site-level AP reboot operations (`restartSiteMultipleDevices`).
