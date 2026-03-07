# countSiteSwOrGwPorts

> countSiteSwOrGwPorts

## HTTP

`GET /api/v1/sites/{site_id}/stats/ports/count`

## Description

Count by Distinct Attributes of Switch/Gateway Ports

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
| distinct | string | No |  |  |  |
| full_duplex | boolean | No |  |  | Indicates full or half duplex |
| mac | string | No |  |  | Device identifier |
| neighbor_mac | string | No |  |  | Chassis identifier of the chassis type listed |
| neighbor_port_desc | string | No |  |  | Description supplied by the system on the interface E.g. "GigabitEthernet2/0/39" |
| neighbor_system_name | string | No |  |  | Name supplied by the system on the interface E.g. neighbor system name E.g. "Kumar-Acc-SW.mist.local" |
| poe_disabled | boolean | No |  |  | Is the POE configured not be disabled. |
| poe_mode | string | No |  |  | POE mode depending on class E.g. "802.3at" |
| poe_on | boolean | No |  |  | Is the device attached to POE |
| port_id | string | No |  |  | Interface name |
| port_mac | string | No |  |  | Interface mac address |
| power_draw | number | No |  |  | Amount of power being used by the interface at the time the command is executed. Unit in watts. |
| tx_pkts | integer | No |  |  | Output packets |
| rx_pkts | integer | No |  |  | Input packets |
| rx_bytes | integer | No |  |  | Input bytes |
| tx_bps | integer | No |  |  | Output rate |
| rx_bps | integer | No |  |  | Input rate |
| tx_mcast_pkts | integer | No |  |  | Multicast output packets |
| tx_bcast_pkts | integer | No |  |  | Broadcast output packets |
| rx_mcast_pkts | integer | No |  |  | Multicast input packets |
| rx_bcast_pkts | integer | No |  |  | Broadcast input packets |
| speed | integer | No |  |  | Port speed |
| stp_state | string | No |  |  | If `up`==`true` |
| stp_role | string | No |  |  | If `up`==`true` |
| auth_state | string | No |  |  | If `up`==`true` && has Authenticator role |
| up | boolean | No |  |  | Indicates if interface is up |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| limit | integer | No | 100 |  |  |

## Request Body

None.

## Response

### 200

Result of Count

```json
{
  "type": "object",
  "properties": {
    "distinct": {
      "type": "string"
    },
    "end": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "count_result",
        "required": [
          "count"
        ],
        "type": "object",
        "properties": {
          "count": {
            "type": "integer",
            "contentEncoding": "int32"
          }
        },
        "additionalProperties": {
          "type": "string"
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "distinct",
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

`mistapi.api.v1.sites.stats_-_ports.countSiteSwOrGwPorts()`

## Usage Context

Returns the count of switch port statistics at a site.

## Gotchas

- Count only; use search endpoint for port details.

## Related Endpoints

- [GET_sites_site_id_stats_ports_search.md](GET_sites_site_id_stats_ports_search.md) — Search port stats
- [GET_sites_site_id_stats_switches_metrics.md](GET_sites_site_id_stats_switches_metrics.md) — Switch metrics

## MistHelper Notes

Used by Menus **14, 29, 31** via `searchSiteSwOrGwPorts` for port data export and SFP transceiver analysis.
