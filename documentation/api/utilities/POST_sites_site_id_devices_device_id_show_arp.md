# showSiteDeviceArpTable

> showSiteDeviceArpTable

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/show_arp`

## Description

Get ARP Table from the Device.

The output will be available through websocket. As there can be multiple command issued against the same device at the same time and the output all goes through the same websocket stream, `session` is introduced for demux.

#### Subscribe to Device Command outputs
`WS /api-ws/v1/stream`

```json
{
    "subscribe": "/sites/{site_id}/devices/{device_id}/cmd"
}
```


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
  "type": "object",
  "properties": {
    "duration": {
      "maximum": 300.0,
      "minimum": 0.0,
      "type": "integer",
      "description": "Duration in sec for which refresh is enabled. Should be set only if interval is configured to non-zero value.",
      "contentEncoding": "int32",
      "default": 0
    },
    "interval": {
      "maximum": 10.0,
      "minimum": 0.0,
      "type": "integer",
      "description": "Rate at which output will refresh",
      "contentEncoding": "int32",
      "default": 0
    },
    "ip": {
      "type": "string",
      "description": "IP Address",
      "examples": [
        "192.168.30.7"
      ]
    },
    "port_id": {
      "type": "string",
      "description": "Device Port ID",
      "examples": [
        "ge-0/0/0.0"
      ]
    },
    "vrf": {
      "type": "string",
      "description": "VRF Name",
      "examples": [
        "guest"
      ]
    }
  },
  "description": "All attributes are optional"
}
```

## Response

### 200

OK

```json
{
  "title": "websocket_session",
  "required": [
    "session"
  ],
  "type": "object",
  "properties": {
    "session": {
      "type": "string",
      "examples": [
        "19e73828-937f-05e6-f709-e29efdb0a82b"
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

`mistapi.api.v1.utilities.common.showSiteDeviceArpTable()`

## Usage Context

Executes a `show arp` command on a switch or gateway via the Mist cloud. Returns the ARP table showing IP-to-MAC bindings.

## Gotchas

- Only works on switches (EX) and gateways (SRX/SSR), not APs.
- Response is returned asynchronously; poll for results if not immediately available.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_clear_arp.md](POST_sites_site_id_devices_device_id_clear_arp.md) — Clear ARP table entries
- [POST_sites_site_id_devices_device_id_show_mac_table.md](POST_sites_site_id_devices_device_id_show_mac_table.md) — MAC table (layer 2 equivalent)

## MistHelper Notes

Not currently used by MistHelper via REST API. ARP-related show commands are available through WebSocket (Menus **5-8**).
