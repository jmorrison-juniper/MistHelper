# clearSiteDeviceMacTable

> clearSiteDeviceMacTable

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/clear_mac_table`

## Description

Clear MAC Table from the Device.

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

`mistapi.api.v1.utilities.common.clearSiteDeviceMacTable()`

## Usage Context

Clears the MAC address table on a switch. Forces the switch to re-learn all MAC addresses. Useful when troubleshooting layer 2 forwarding issues or MAC flapping.

## Gotchas

- Causes brief traffic flooding as the switch re-learns MAC entries.
- This clears the entire MAC table. Use `clear_macs` for targeted MAC removal.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_show_mac_table.md](POST_sites_site_id_devices_device_id_show_mac_table.md) — View current MAC table first
- [POST_sites_site_id_devices_device_id_clear_macs.md](POST_sites_site_id_devices_device_id_clear_macs.md) — Clear specific MACs

## MistHelper Notes

Not currently used by MistHelper via REST API.
