# tracerouteFromDevice

> tracerouteFromDevice

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/traceroute`

## Description

Traceroute can be performed from the Device.

The output will be available through websocket. As there can be multiple command issued against the same Device at the same time and the output all goes through the same websocket stream, session is introduced for demux.


#### Subscribe to Device Command outputs

`WS /api-ws/v1/stream`

```json
{
    "subscribe": "/sites/{site_id}/devices/{device_id}/cmd"
}
```


#### Example output from ws stream
```json
{
  "channel": "/sites/d6fb4f96-xxxx-xxxx-xxxx-xxxxxxxxxxxx/devices/00000000-0000-0000-1000-xxxxxxxxxxxx/cmd",
  "event": "data",
  "data": {
    "session": "9106e908-74dc-4a4f-9050-9c2adcaf44a5",
    "raw": "Running traceroute...\ntraceroute to 8.8.8.8, 64 hops max\n 0  192.168.1.1 1 ms  192.168.1.1 1 ms  192.168.1.1 1 ms\n 1  80.10.236.81 2 ms  80.10.236.81 4 ms  80.10.236.81 2 ms\n 2  193.253.80.250 3 ms  193.253.80.250 2 ms  193.253.80.250 2 ms\n 3  193.252.159.41 2 ms  193.252.159.41 1 ms  193.252.159.41 3 ms\n"
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
    "host": {
      "type": "string",
      "description": "Host name"
    },
    "network": {
      "type": "string",
      "description": "For SSR, optional, the source to initiate traceroute from",
      "default": "internal"
    },
    "node": {
      "type": "string",
      "description": "only for HA. enum: `node0`, `node1`"
    },
    "port": {
      "type": "integer",
      "description": "When `protocol`==`udp`, not supported in SSR. The udp port to use",
      "contentEncoding": "int32",
      "default": 33434
    },
    "protocol": {
      "type": "string",
      "description": "enum: `icmp` (Only supported by AP/MxEdge), `udp`"
    },
    "timeout": {
      "type": "integer",
      "description": "Not supported in SSR. Maximum time in seconds to wait for the response",
      "contentEncoding": "int32",
      "default": 60
    },
    "use_ipv6": {
      "type": "boolean",
      "default": false
    },
    "vrf": {
      "type": "string",
      "description": "For SRX, optional, the source to initiate traceroute from. by default, master VRF/RI is assumed"
    }
  },
  "description": "Request Body"
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

`mistapi.api.v1.utilities.common.tracerouteFromDevice()`

## Usage Context

Executes a traceroute from a device to a target host. Shows the hop-by-hop path for diagnosing routing issues. Output returned via WebSocket.

## Gotchas

- Output is delivered asynchronously via WebSocket channel.
- Intermediate hops may not respond if ICMP is filtered, showing `*` entries.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_ping.md](POST_sites_site_id_devices_device_id_ping.md) — Quick reachability test
- [POST_sites_site_id_devices_device_id_show_route.md](POST_sites_site_id_devices_device_id_show_route.md) — Local routing table

## MistHelper Notes

Not currently used by MistHelper via REST API.
