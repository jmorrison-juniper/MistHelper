# showSiteSsrAndSrxRoutes

> showSiteSsrAndSrxRoutes

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/show_route`

## Description

Get routes from SSR, SRX and Switch. 

The output will be available through websocket. As there can be multiple command issued against the same device at the same time and the output all goes through the same websocket stream, `session` is introduced for demux.

#### Subscribe to Device Command outputs
`WS /api-ws/v1/stream`

```json
{
    "subscribe": "/sites/{site_id}/devices/{device_id}/cmd"
}
```
##### Example output from ws stream
```
admin@labsystem1.fiedler# show bgp neighbors
BGP neighbor is 192.168.4.1, remote AS 4200000001, local AS 4200000128, external
link
  BGP version 4, remote router ID 1.1.1.1
  BGP state = Established, up for 00:27:25
  Last read 00:00:25, hold time is 90, keepalive interval is 30 seconds
  Configured hold time is 90, keepalive interval is 30 seconds
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Route refresh: advertised and received(old &amp; new)
    Address family IPv4 Unicast: advertised and received
    Graceful Restart Capability: advertised and received
      Remote Restart timer is 120 seconds
      Address families by peer:
        none
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
    "neighbor": {
      "type": "string",
      "description": "IP of the neighbor",
      "examples": [
        "192.168.4.1"
      ]
    },
    "node": {
      "title": "ha_cluster_node",
      "type": "object",
      "properties": {
        "node": {
          "type": "string",
          "description": "only for HA. enum: `node0`, `node1`"
        }
      }
    },
    "prefix": {
      "type": "string",
      "description": "Route prefix",
      "examples": [
        "192.168.0.5/30"
      ]
    },
    "protocol": {
      "type": "string",
      "description": "enum: `any`, `bgp`, `direct`, `evpn`, `ospf`, `static`"
    },
    "route": {
      "type": "string",
      "description": "If specified, dump bot received and advertised, if not specified, both will be shown\n  * for SSR, show bgp neighbors 10.250.18.202 received-routes/advertised-routes\n  * for SRX and Switches, show route receive_protocol/advertise_protocol bgp 192.168.255.12'",
      "examples": [
        "advertised"
      ]
    },
    "vrf": {
      "type": "string",
      "description": "VRF name",
      "examples": [
        "default"
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

`mistapi.api.v1.utilities.wan.showSiteSsrAndSrxRoutes()`

## Usage Context

Retrieves the routing table (RIB) from a gateway. Shows routes, next-hops, protocols (OSPF/BGP/static/connected), and metrics.

## Gotchas

- Routing tables on large SSR deployments can be extensive — consider filtering by prefix if supported.
- Shows RIB (routing decisions), not FIB (actual forwarding state).

## Related Endpoints

- [POST_sites_site_id_devices_device_id_show_forwarding_table.md](POST_sites_site_id_devices_device_id_show_forwarding_table.md) — FIB (forwarding table)
- [POST_sites_site_id_devices_device_id_show_bgp_summary.md](POST_sites_site_id_devices_device_id_show_bgp_summary.md) — BGP sessions
- [POST_sites_site_id_devices_device_id_show_ospf_database.md](POST_sites_site_id_devices_device_id_show_ospf_database.md) — OSPF LSDB

## MistHelper Notes

WebSocket show commands (Menu **7**) use a similar endpoint for real-time routing table retrieval.
