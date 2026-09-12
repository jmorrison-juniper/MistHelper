# showSiteDeviceForwardingTable

> showSiteDeviceForwardingTable

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/show_forwarding_table`

## Description

Get forwarding table from the Device. The output will be available through websocket. As there can be multiple command issued against the same device at the same time and the output all goes through the same websocket stream, `session` is introduced for demux.

#### Subscribe to Device Command outputs
`WS /api-ws/v1/stream`

```json
{
    "subscribe": "/sites/{site_id}/devices/{device_id}/cmd"
}
```

##### Example output from ws stream
```
Mon 2024-05-20 16:47:30 UTC Retrieving fib entries… Entry Count: 3268 Capacity:    22668 ==================== ====== ======= ================== ===== ====================== =========== =========== ====== IP Prefix            Port   Proto   Tenant             VRF   Service                Next Hops   Vector      Cost ==================== ====== ======= ================== ===== ====================== =========== =========== ====== 0.0.0.0/0               0   None    Old_Mgmt           -     internet-wan_and_lte   1-2.0       broadband      1 1-4.0       lte           10 branch1-Kiosk      -     internet-wan_and_lte   1-2.0       broadband      1 1-4.0       lte           10 branch1-MGT        -     internet-wan_and_lte   1-2.0       broadband      1 1-4.0       lte           10 3.1.1.0/24              0   None    Old_Mgmt           -     internet-wan_and_lte   1-2.0       broadband      1 1-4.0       lte           10 branch1-Kiosk      -     internet-wan_and_lte   1-2.0       broadband      1 1-4.0       lte           10 branch1-MGT        -     internet-wan_and_lte   1-2.0       broadband      1 1-4.0       lte           10

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
    },
    "prefix": {
      "type": "string",
      "description": "IP Prefix",
      "examples": [
        "3.1.1.0/24"
      ]
    },
    "service_ip": {
      "type": "string",
      "description": "Only supported with SSR",
      "examples": [
        "3.1.1.10"
      ]
    },
    "service_name": {
      "type": "string",
      "description": "Only supported with SSR",
      "examples": [
        "internet-wan_and_lte"
      ]
    },
    "service_port": {
      "type": "integer",
      "description": "Only supported with SSR",
      "contentEncoding": "int32",
      "examples": [
        32768
      ]
    },
    "service_protocol": {
      "type": "string",
      "description": "Only supported with SSR",
      "examples": [
        "udp"
      ]
    },
    "service_tenant": {
      "type": "string",
      "description": "Only supported with SSR",
      "examples": [
        "branch1-wifi-mgt"
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

`mistapi.api.v1.utilities.common.showSiteDeviceForwardingTable()`

## Usage Context

Retrieves the forwarding table (FIB) from a gateway. Shows active forwarding entries with next-hop and interface information.

## Gotchas

- The forwarding table reflects actual forwarding state, not routing policy — use `show route` for RIB.
- Results can be very large on gateways with many routes.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_show_route.md](POST_sites_site_id_devices_device_id_show_route.md) — Routing table (RIB)
- [POST_sites_site_id_devices_device_id_show_mac_table.md](POST_sites_site_id_devices_device_id_show_mac_table.md) — Layer 2 forwarding

## MistHelper Notes

WebSocket show commands (Menu **6**) use a similar endpoint for real-time forwarding table retrieval.
