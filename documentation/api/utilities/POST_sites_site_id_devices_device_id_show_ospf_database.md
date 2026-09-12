# showSiteGatewayOspfDatabase

> showSiteGatewayOspfDatabase

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/show_ospf_database`

## Description

Get OSPF Database from SSR and SRX. The output will be available through websocket. 

As there can be multiple command issued against the same device at the same time and the output all goes through the same websocket stream, `session` is introduced for demux.

#### Subscribe to Device Command outputs
`WS /api-ws/v1/stream`

```json
{
  "subscribe": "/sites/{site_id}/devices/{device_id}/cmd"
}
```

#### Example output from ws stream
```
===== ==================== ========== ======= ======== ================ =================== =================
Vrf   Neighbor Router ID   Priority   State   Uptime   Dead Timer Due   Interface Address   Interface State
===== ==================== ========== ======= ======== ================ =================== =================
      1.0.0.3                     1   Full       852               38   172.16.3.2          Backup
      1.0.0.4                     1   Full       811               33   172.16.3.2          DROther
      1.0.0.3                     1   Full       852               38   172.16.4.2          Backup
      1.0.0.4                     1   Full       811               34   172.16.4.2          DROther
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
    "self_originate": {
      "type": "boolean",
      "description": "Show originating info, default is false",
      "default": false
    },
    "vrf": {
      "type": "string",
      "description": "VRF name",
      "examples": [
        "lan"
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

`mistapi.api.v1.utilities.wan.showSiteGatewayOspfDatabase()`

## Usage Context

Retrieves the OSPF link-state database (LSDB) from a gateway. Shows all OSPF LSAs known to the device.

## Gotchas

- Only available on gateways running OSPF.
- LSDB can be large in multi-area deployments.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_show_ospf_neighbors.md](POST_sites_site_id_devices_device_id_show_ospf_neighbors.md) — OSPF neighbor adjacencies
- [POST_sites_site_id_devices_device_id_show_ospf_interfaces.md](POST_sites_site_id_devices_device_id_show_ospf_interfaces.md) — OSPF-enabled interfaces
- [POST_sites_site_id_devices_device_id_show_ospf_summary.md](POST_sites_site_id_devices_device_id_show_ospf_summary.md) — OSPF overview

## MistHelper Notes

Not currently used by MistHelper via REST API.
