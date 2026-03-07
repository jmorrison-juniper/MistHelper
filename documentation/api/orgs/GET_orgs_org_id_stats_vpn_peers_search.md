# searchOrgPeerPathStats

> searchOrgPeerPathStats

## HTTP

`GET /api/v1/orgs/{org_id}/stats/vpn_peers/search`

## Description

Search Org Peer Path Stats

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| mac | string | No |  |  |  |
| site_id | string | No |  |  |  |
| type | string | No |  |  |  |
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

OK

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
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "vpn_peer_stat",
        "type": "object",
        "properties": {
          "is_active": {
            "type": "boolean",
            "description": "Redundancy status of the associated interface"
          },
          "jitter": {
            "minimum": 0.0,
            "type": "number",
            "description": "Jitter in milliseconds"
          },
          "last_seen": {
            "type": [
              "number",
              "null"
            ],
            "description": "Last seen timestamp",
            "readOnly": true,
            "examples": [
              1470417522
            ]
          },
          "latency": {
            "minimum": 0.0,
            "type": "number",
            "description": "Latency in milliseconds"
          },
          "loss": {
            "maximum": 100.0,
            "minimum": 0.0,
            "type": "number",
            "description": "Packet loss in percentage"
          },
          "mac": {
            "minLength": 1,
            "type": "string",
            "description": "Router mac address"
          },
          "mos": {
            "maximum": 5.0,
            "minimum": 0.0,
            "type": "number",
            "description": "Mean Opinion Score, a measure of the quality of the VPN link"
          },
          "mtu": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "org_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "peer_mac": {
            "minLength": 1,
            "type": "string",
            "description": "Peer router mac address"
          },
          "peer_port_id": {
            "minLength": 1,
            "type": "string",
            "description": "Peer router device interface"
          },
          "peer_router_name": {
            "minLength": 1,
            "type": "string"
          },
          "peer_site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "port_id": {
            "minLength": 1,
            "type": "string",
            "description": "Router device interface"
          },
          "router_name": {
            "minLength": 1,
            "type": "string"
          },
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "type": {
            "minLength": 1,
            "type": "string",
            "description": "`ipsec`for SRX, `svr` for 128T"
          },
          "up": {
            "type": "boolean"
          },
          "uptime": {
            "type": "integer",
            "contentEncoding": "int32"
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
  },
  "required": [
    "end",
    "limit",
    "results",
    "start",
    "total"
  ]
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

`mistapi.api.v1.orgs.stats_-_vpn_peers.searchOrgPeerPathStats()`

## Usage Context

Searches for VPN peer statistics across the organization.

## Gotchas

- Includes peer status, latency, and jitter metrics.

## Related Endpoints

- [GET_orgs_org_id_stats_vpn_peers_count.md](GET_orgs_org_id_stats_vpn_peers_count.md) — Count VPN peers
- [GET_orgs_org_id_vpns.md](GET_orgs_org_id_vpns.md) — VPN config

## MistHelper Notes

Not currently used by MistHelper directly.
