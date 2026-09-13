# showSiteDeviceDot1xTable

> showSiteDeviceDot1xTable

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/show_dot1x`

## Description

Get Dot1X Table from the Device.

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
    "port_id": {
      "type": "string",
      "description": "Device Port ID",
      "examples": [
        "ge-0/0/0.0"
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

`mistapi.api.v1.utilities.common.showSiteDeviceDot1xTable()`

## Usage Context

Retrieves 802.1X authentication status from a switch. Shows per-port authentication state, client MACs, and VLAN assignments.

## Gotchas

- Only works on switches with 802.1X/NAC configured.
- Results show port-level details, not individual client sessions.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_clear_dot1x.md](POST_sites_site_id_devices_device_id_clear_dot1x.md) — Clear 802.1X sessions
- [POST_sites_site_id_wired_clients_client_mac_coa.md](POST_sites_site_id_wired_clients_client_mac_coa.md) — CoA for wired clients

## MistHelper Notes

Not currently used by MistHelper via REST API.
