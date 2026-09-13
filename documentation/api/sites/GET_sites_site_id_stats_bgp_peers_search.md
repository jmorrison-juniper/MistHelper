# searchSiteBgpStats

> searchSiteBgpStats

## HTTP

`GET /api/v1/sites/{site_id}/stats/bgp_peers/search`

## Description

Search BGP Stats

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| mac | string | No |  |  |  |
| neighbor_mac | string | No |  |  |  |
| vrf_name | string | No |  |  |  |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "number"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "next": {
      "type": "string"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "bgp_stats",
        "type": "object",
        "properties": {
          "evpn_overlay": {
            "type": "boolean",
            "description": "If this is created for evpn overlay"
          },
          "for_overlay": {
            "type": "boolean",
            "description": "If this is created for overlay"
          },
          "local_as": {
            "type": "object",
            "description": "BGP AS, value in range 1-4294967294. Can be a Variable (e.g. `{{bgp_as}}` )"
          },
          "mac": {
            "type": "string",
            "description": "Router mac address",
            "examples": [
              "020001c04668"
            ]
          },
          "model": {
            "type": "string"
          },
          "neighbor": {
            "type": "string",
            "examples": [
              "15.8.3.5"
            ]
          },
          "neighbor_as": {
            "type": "object",
            "description": "BGP AS, value in range 1-4294967294. Can be a Variable (e.g. `{{bgp_as}}` )"
          },
          "neighbor_mac": {
            "type": "string",
            "description": "If it's another device in the same org",
            "examples": [
              "020001c04600"
            ]
          },
          "node": {
            "type": "string",
            "description": "Node0/node1",
            "examples": [
              "node0"
            ]
          },
          "org_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "rx_pkts": {
            "type": [
              "integer",
              "null"
            ],
            "description": "Amount of packets received since connection",
            "contentEncoding": "int64",
            "readOnly": true,
            "examples": [
              57770567
            ]
          },
          "rx_routes": {
            "type": "integer",
            "description": "Number of received routes",
            "contentEncoding": "int32",
            "examples": [
              60
            ]
          },
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "state": {
            "type": "string",
            "description": "enum: `active`, `connect`, `established`, `idle`, `open_config`, `open_sent`"
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "tx_pkts": {
            "type": [
              "integer",
              "null"
            ],
            "description": "Amount of packets sent since connection",
            "contentEncoding": "int64",
            "readOnly": true,
            "examples": [
              812204062
            ]
          },
          "tx_routes": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              60
            ]
          },
          "up": {
            "type": "boolean"
          },
          "uptime": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              31355
            ]
          },
          "vrf_name": {
            "type": "string",
            "examples": [
              "default"
            ]
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "number"
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.stats_-_bgp_peers.searchSiteBgpStats()`

## Usage Context

Searches BGP peer statistics at a site. Shows neighbor state, prefixes received/sent, and session uptime.

## Gotchas

- BGP state values follow standard BGP FSM states (Idle, Connect, Active, OpenSent, OpenConfirm, Established).

## Related Endpoints

- [GET_sites_site_id_stats_bgp_peers_count.md](GET_sites_site_id_stats_bgp_peers_count.md) — Count BGP peers
- [GET_sites_site_id_stats_ospf_peers_search.md](GET_sites_site_id_stats_ospf_peers_search.md) — OSPF peers

## MistHelper Notes

Not currently used by MistHelper directly.
