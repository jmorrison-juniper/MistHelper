# monitorSiteDeviceTraffic

> monitorSiteDeviceTraffic

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/monitor_traffic`

## Description

Monitor traffic on switches and SRX.
  * JUNOS uses cmd "monitor interface <port>" to monitor traffic on particular <port>
  * JUNOS uses cmd "monitor interface traffic" to monitor traffic on all ports

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
  "title": "utils_monitor_traffic",
  "type": "object",
  "properties": {
    "port": {
      "type": "string",
      "description": "Port name, if no port input is provided then all ports will be monitored",
      "examples": [
        "ge-0/0/1"
      ]
    }
  }
}
```

## Response

### 200

OK

```json
{
  "title": "websocket_session_with_url",
  "required": [
    "session",
    "url"
  ],
  "type": "object",
  "properties": {
    "session": {
      "type": "string",
      "examples": [
        "19e73828-937f-05e6-f709-e29efdb0a82b"
      ]
    },
    "url": {
      "type": "string",
      "examples": [
        "wss://api-ws.mist.com/ssh?jwt=xxxx"
      ]
    }
  }
}
```

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

`mistapi.api.v1.utilities.common.monitorSiteDeviceTraffic()`

## Usage Context

Starts a traffic monitor (packet capture) on a specific device interface. Captures live network traffic for troubleshooting. Output delivered via WebSocket.

## Gotchas

- Only works on switches and gateways.
- Capture runs until manually stopped or a timeout is reached.
- High-traffic interfaces may generate large capture output.

## Related Endpoints

- [POST_sites_site_id_pcaps_capture.md](POST_sites_site_id_pcaps_capture.md) — Site-level packet capture (wireless + wired)
- [POST_sites_site_id_devices_device_id_show_mac_table.md](POST_sites_site_id_devices_device_id_show_mac_table.md) — Identify traffic sources

## MistHelper Notes

Not currently used by MistHelper via REST API. For structured packet captures, use Menu **9** (site) or Menu **10** (org).
