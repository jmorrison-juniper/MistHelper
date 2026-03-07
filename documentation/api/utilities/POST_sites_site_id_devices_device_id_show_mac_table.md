# showSiteDeviceMacTable

> showSiteDeviceMacTable

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/show_mac_table`

## Description

Get MAC Table from the Device.

The output will be available through websocket. As there can be multiple command issued against the same device at the same time and the output all goes through the same websocket stream, `session` is introduced for demux.



#### Subscribe to Device Command outputs

`WS /api-ws/v1/stream`

```json
{
    "subscribe": "/sites/{site_id}/devices/{device_id}/cmd"
```


#### Example output from ws stream

```json 
{
    "event": "data",
    "channel": "/sites/d6fb4f96-xxxx-xxxx-xxxx-a8d7b85087ac/devices/00000000-0000-0000-1000-209339xxxxxx/cmd",
    "data": "{\"event\": \"data\", \"channel\": \"/sites/d6fb4f96-xxxx-xxxx-xxxx-a8d7b85087ac/devices/209339xxxxxx/cmd\", \"data\": {\"session\": \"eec2b6e4-1e63-4f9f-9cf8-ef7f9632861e\", \"raw\": \"\\nMAC flags (S - static MAC, D - dynamic MAC, L - locally learned, P - Persistent static, C - Control MAC\\n           SE - statistics enabled, NM - non configured MAC, R - remote PE MAC, O - ovsdb MAC\\n           GBP - group based policy, B - Blocked MAC)\\n\\n\\nE\"}}"
}
{
    "event": "data",
    "channel": "/sites/d6fb4f96-xxxx-xxxx-xxxx-a8d7b85087ac/devices/00000000-0000-0000-1000-209339xxxxxx/cmd",
    "data": "{\"event\": \"data\", \"channel\": \"/sites/d6fb4f96-xxxx-xxxx-xxxx-a8d7b85087ac/devices/209339xxxxxx/cmd\", \"data\": {\"session\": \"eec2b6e4-1e63-4f9f-9cf8-ef7f9632861e\", \"raw\": \"thernet switching table : 59 entries, 59 learned\\nRouting instance : default-switch\\n    Vlan                MAC                 MAC         Age   GBP     Logical                NH        MAC        RTR\\n    name                address             flags      \"}}"
}
{
    "event": "data",
    "channel": "/sites/d6fb4f96-xxxx-xxxx-xxxx-a8d7b85087ac/devices/00000000-0000-0000-1000-209339xxxxxx/cmd",
    "data": "{\"event\": \"data\", \"channel\": \"/sites/d6fb4f96-xxxx-xxxx-xxxx-a8d7b85087ac/devices/209339xxxxxx/cmd\", \"data\": {\"session\": \"eec2b6e4-1e63-4f9f-9cf8-ef7f9632861e\", \"raw\": \"       Tag     interface              Index     property   ID\\n    corp                00:50:56:87:4f:69   D             -           xe-0/1/3.0             0                    0       \\n    corp                00:50:56:87:ce:f5   D             -           x\"}}"
}
{
    "event": "data",
    "channel": "/sites/d6fb4f96-xxxx-xxxx-xxxx-a8d7b85087ac/devices/00000000-0000-0000-1000-209339xxxxxx/cmd",
    "data": "{\"event\": \"data\", \"channel\": \"/sites/d6fb4f96-xxxx-xxxx-xxxx-a8d7b85087ac/devices/209339xxxxxx/cmd\", \"data\": {\"session\": \"eec2b6e4-1e63-4f9f-9cf8-ef7f9632861e\", \"raw\": \"e-0/1/3.0             0                    0       \\n    corp                20:93:39:0f:62:00   D             -           xe-0/1/3.0             0                    0       \\n    ifo                 00:50:56:87:2d:42   D             -           xe-0/1/3.0 \"}}"
}
...
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
    "mac_address": {
      "type": "string",
      "examples": [
        "f8c1165c6400"
      ]
    },
    "port_id": {
      "type": "string",
      "examples": [
        "ge-0/0/0.0"
      ]
    },
    "vlan_id": {
      "type": "string",
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

`mistapi.api.v1.utilities.common.showSiteDeviceMacTable()`

## Usage Context

Retrieves the MAC address table from a switch. Shows learned MAC addresses, VLAN assignments, and port mappings.

## Gotchas

- Large MAC tables on aggregation switches may return paginated results.
- MAC entries have aging timers — stale entries may not appear.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_clear_mac_table.md](POST_sites_site_id_devices_device_id_clear_mac_table.md) — Clear MAC table entries
- [POST_sites_site_id_devices_device_id_clear_macs.md](POST_sites_site_id_devices_device_id_clear_macs.md) — Clear specific MACs
- [POST_sites_site_id_devices_device_id_show_arp.md](POST_sites_site_id_devices_device_id_show_arp.md) — ARP table (layer 3 equivalent)

## MistHelper Notes

WebSocket show commands (Menu **5**) use a similar endpoint for real-time MAC table retrieval.
