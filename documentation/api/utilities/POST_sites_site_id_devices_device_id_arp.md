# arpFromDevice

> arpFromDevice

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/arp`

## Description

ARP can be performed on the Device. The output will be available through websocket. As there can be multiple command issued against the same AP at the same time and the output all goes through the same websocket stream, session is introduced for demux.


#### Subscribe to Device Command outputs
`WS /api-ws/v1/stream`

```json
{
    "subscribe": "/sites/{site_id}/devices/{device_id}/cmd"
}
```
##### Example output from ws stream
```json
{ 
 "event": "data", 
 "channel": "/sites/4ac1dcf4-9d8b-7211-65c4-057819f0862b/devices/00000000-0000-0000-1000-5c5b350e0060/cmd", 
 "data": { 
   "session": "session_id", 
   "raw": 
   "Output": "\tMAC\t\tDEV\tVLAN\tRx Packets\t\t Rx Bytes\t\tTx Packets\t\t Tx Bytes\tFlows\tIdle sec\n-----------------------------------------------------------------------------------------------------------------------"
  } 
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
    "node": {
      "type": "string",
      "description": "only for HA. enum: `node0`, `node1`"
    }
  }
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

`mistapi.api.v1.utilities.common.arpFromDevice()`

## Usage Context

Sends an ARP request from a device to resolve or verify IP-to-MAC resolution. Useful for troubleshooting connectivity issues. Output returned via WebSocket.

## Gotchas

- Output is delivered asynchronously via WebSocket channel, not in the REST response body.
- Works on switches and gateways, not APs.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_show_arp.md](POST_sites_site_id_devices_device_id_show_arp.md) — View full ARP table
- [POST_sites_site_id_devices_device_id_ping.md](POST_sites_site_id_devices_device_id_ping.md) — Ping from device

## MistHelper Notes

Not currently used by MistHelper via REST API.
