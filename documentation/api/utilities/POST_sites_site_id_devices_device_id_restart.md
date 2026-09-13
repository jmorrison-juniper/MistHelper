# restartSiteDevice

> restartSiteDevice

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/restart`

## Description

Restart / Reboot a device

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| device_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "title": "utils_devices_restart",
  "type": "object",
  "properties": {
    "member": {
      "maximum": 9.0,
      "minimum": 0.0,
      "type": "integer",
      "description": "Optional for VC member",
      "contentEncoding": "int32"
    },
    "node": {
      "type": "string",
      "description": "only for SRX/SSR: if node is not present, both nodes are restarted. For other devices: node should not be present"
    }
  }
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

`mistapi.api.v1.utilities.common.restartSiteDevice()`

## Usage Context

Restarts a specific device at a site. The device reboots and reconnects to the Mist cloud. Use for troubleshooting persistent issues that survive config changes.

## Gotchas

- Device is offline during reboot (1-5 minutes depending on device type).
- PoE-powered downstream devices also lose power during switch reboots.
- APs in HA/mesh may have clients that need to roam.

## Related Endpoints

- [POST_sites_site_id_devices_restart.md](POST_sites_site_id_devices_restart.md) — Restart multiple devices at a site
- [POST_sites_site_id_devices_device_id_reprovision.md](POST_sites_site_id_devices_device_id_reprovision.md) — Try reprovision first (less disruptive)

## MistHelper Notes

Used by Menu **91-93** for AP reboot operations (`restartSiteDevice`).
