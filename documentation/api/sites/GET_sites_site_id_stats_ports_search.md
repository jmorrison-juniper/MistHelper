# searchSiteSwOrGwPorts

> searchSiteSwOrGwPorts

## HTTP

`GET /api/v1/sites/{site_id}/stats/ports/search`

## Description

Search Switch / Gateway Ports Stats for a specific site.
Returns a list of switch/gateway ports stats that match the search criteria.

The response provide current/last port status and statistics within the hour.
Traffic information (Tx/Rx) are cumulative counters since the last device reboot.

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
| device_type | string | No |  |  | Type of device. enum: `switch`, `gateway`, `all` |
| auth_state | string | No |  |  | If `up`==`true` && has Authenticator role |
| full_duplex | boolean | No |  |  | Indicates full or half duplex |
| lte_imsi | string | No |  |  | LTE IMSI value, Check for null/empty |
| lte_iccid | string | No |  |  | LTE ICCID value, Check for null/empty |
| lte_imei | string | No |  |  | LTE IMEI value, Check for null/empty |
| mac | string | No |  |  | Device identifier |
| neighbor_mac | string | No |  |  | Chassis identifier of the chassis type listed |
| neighbor_port_desc | string | No |  |  | Description supplied by the system on the interface E.g. "GigabitEthernet2/0/39" |
| neighbor_system_name | string | No |  |  | Name supplied by the system on the interface E.g. neighbor system name E.g. "Kumar-Acc-SW.mist.local" |
| poe_disabled | boolean | No |  |  | Is the POE configured not be disabled. |
| poe_mode | string | No |  |  | POE mode depending on class E.g. "802.3at" |
| poe_on | boolean | No |  |  | Is the device attached to POE |
| poe_priority | string | No |  |  | PoE priority. |
| port_id | string | No |  |  | Interface name |
| port_mac | string | No |  |  | Interface mac address |
| speed | integer | No |  |  | Port speed |
| stp_state | string | No |  |  | If `up`==`true` |
| stp_role | string | No |  |  | If `up`==`true` |
| up | boolean | No |  |  | Indicates if interface is up |
| xcvr_part_number | string | No |  |  | Optic Slot Partnumber, Check for null/empty |
| limit | integer | No | 100 |  |  |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

## Request Body

None.

## Response

### 200

List of Switch Ports Stats

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1513177200
      ]
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        10
      ]
    },
    "next": {
      "type": "string"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "stats_switch_port",
        "required": [
          "mac",
          "org_id",
          "port_id",
          "site_id"
        ],
        "type": "object",
        "properties": {
          "active": {
            "type": "boolean",
            "description": "Indicates if interface is active/inactive",
            "readOnly": true
          },
          "auth_state": {
            "type": "string",
            "description": "enum: `authenticated`, `authenticating`, `held`, `init`"
          },
          "disabled": {
            "type": "boolean",
            "description": "Indicates if interface is disabled",
            "readOnly": true
          },
          "for_site": {
            "type": "boolean",
            "readOnly": true
          },
          "full_duplex": {
            "type": "boolean",
            "description": "Indicates full or half duplex",
            "examples": [
              true
            ]
          },
          "jitter": {
            "type": "number",
            "description": "Last sampled jitter of the interface",
            "readOnly": true
          },
          "last_flapped": {
            "type": "number",
            "description": "Indicates when the port was last flapped",
            "readOnly": true
          },
          "latency": {
            "type": "number",
            "description": "Last sampled latency of the interface",
            "readOnly": true
          },
          "loss": {
            "type": "number",
            "description": "Last sampled loss of the interface",
            "readOnly": true
          },
          "lte_iccid": {
            "type": [
              "string",
              "null"
            ],
            "description": "LTE ICCID value, Check for null/empty"
          },
          "lte_imei": {
            "type": [
              "string",
              "null"
            ],
            "description": "LTE IMEI value, Check for null/empty"
          },
          "lte_imsi": {
            "type": [
              "string",
              "null"
            ],
            "description": "LTE IMSI value, Check for null/empty"
          },
          "mac": {
            "type": "string",
            "readOnly": true,
            "examples": [
              "5c4527a96580"
            ]
          },
          "mac_count": {
            "type": "integer",
            "description": "Number of mac addresses in the forwarding table",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "mac_limit": {
            "minimum": 0.0,
            "type": "integer",
            "description": "Limit on number of dynamically learned macs",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "neighbor_mac": {
            "type": "string",
            "description": "chassis identifier of the chassis type listed",
            "readOnly": true,
            "examples": [
              "64d814353400"
            ]
          },
          "neighbor_port_desc": {
            "type": "string",
            "description": "Description supplied by the system on the interface E.g. \"GigabitEthernet2/0/39\"",
            "readOnly": true,
            "examples": [
              "GigabitEthernet1/0/21"
            ]
          },
          "neighbor_system_name": {
            "type": "string",
            "description": "Name supplied by the system on the interface E.g. neighbor system name E.g. \"Kumar-Acc-SW.mist.local\"",
            "readOnly": true,
            "examples": [
              "CORP-D-SW-2"
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
          "poe_disabled": {
            "type": "boolean",
            "description": "Is the POE disabled",
            "readOnly": true
          },
          "poe_mode": {
            "type": "string",
            "description": "enum: `802.3af`, `802.3at`, `802.3bt`"
          },
          "poe_on": {
            "type": "boolean",
            "description": "Is the device attached to POE",
            "readOnly": true
          },
          "poe_priority": {
            "type": "string",
            "description": "PoE priority. enum: `low`, `high`"
          },
          "port_id": {
            "type": "string",
            "readOnly": true,
            "examples": [
              "ge-0/0/0"
            ]
          },
          "port_mac": {
            "type": "string",
            "description": "Interface MAC address",
            "readOnly": true,
            "examples": [
              "5c4527a96580"
            ]
          },
          "port_usage": {
            "type": "string",
            "examples": [
              "lan"
            ]
          },
          "power_draw": {
            "type": "number",
            "description": "Amount of power being used by the interface at the time the command is executed. Unit in watts.",
            "readOnly": true
          },
          "rx_bcast_pkts": {
            "type": "integer",
            "description": "Broadcast input packets",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "rx_bps": {
            "type": [
              "integer",
              "null"
            ],
            "description": "Rate of receiving traffic, bits/seconds, last known",
            "contentEncoding": "int64",
            "readOnly": true,
            "examples": [
              60003
            ]
          },
          "rx_bytes": {
            "type": [
              "integer",
              "null"
            ],
            "description": "Amount of traffic received since connection",
            "contentEncoding": "int64",
            "readOnly": true,
            "examples": [
              8515104416
            ]
          },
          "rx_errors": {
            "type": "integer",
            "description": "Input errors",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "rx_mcast_pkts": {
            "type": "integer",
            "description": "Multicast input packets",
            "contentEncoding": "int32",
            "readOnly": true
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
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "speed": {
            "type": "integer",
            "description": "Port speed",
            "contentEncoding": "int32",
            "readOnly": true,
            "examples": [
              1000
            ]
          },
          "stp_role": {
            "type": "string",
            "description": "enum: `alternate`, `backup`, `designated`, `disabled`, `root`, `root-prevented`"
          },
          "stp_state": {
            "type": "string",
            "description": "enum: `blocking`, `disabled`, `forwarding`, `learning`, `listening`"
          },
          "tx_bcast_pkts": {
            "type": "integer",
            "description": "Broadcast output packets",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "tx_bps": {
            "type": [
              "integer",
              "null"
            ],
            "description": "Rate of transmitting traffic, bits/seconds, last known",
            "contentEncoding": "int64",
            "readOnly": true,
            "examples": [
              634301
            ]
          },
          "tx_bytes": {
            "type": [
              "integer",
              "null"
            ],
            "description": "Amount of traffic sent since connection",
            "contentEncoding": "int64",
            "readOnly": true,
            "examples": [
              211217389682
            ]
          },
          "tx_errors": {
            "type": "integer",
            "description": "Output errors",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "tx_mcast_pkts": {
            "type": "integer",
            "description": "Multicast output packets",
            "contentEncoding": "int32",
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
          "type": {
            "type": "string",
            "description": "device type. enum: `ap`, `ble`, `gateway`, `mxedge`, `nac`, `switch`"
          },
          "unconfigured": {
            "type": "boolean",
            "description": "Indicates if interface is unconfigured",
            "readOnly": true
          },
          "up": {
            "type": "boolean",
            "description": "Indicates if interface is up",
            "readOnly": true
          },
          "xcvr_model": {
            "type": "string",
            "description": "Optic Slot ModelName, Check for null/empty",
            "readOnly": true,
            "examples": [
              "SFP+-10G-SR"
            ]
          },
          "xcvr_part_number": {
            "type": "string",
            "description": "Optic Slot Partnumber, Check for null/empty",
            "readOnly": true,
            "examples": [
              "740-021487"
            ]
          },
          "xcvr_serial": {
            "type": "string",
            "description": "Optic Slot SerialNumber, Check for null/empty",
            "readOnly": true,
            "examples": [
              "N6AA9HT"
            ]
          }
        },
        "description": "Switch port statistics"
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1511967600
      ]
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        100
      ]
    }
  },
  "required": [
    "limit",
    "results",
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

`mistapi.api.v1.sites.stats_-_ports.searchSiteSwOrGwPorts()`

## Usage Context

Searches switch port statistics at a site. Returns port status, speed, duplex, PoE, and connected device info.

## Gotchas

- Large sites with many switches can return thousands of port records. Use filters to narrow results.
- SFP transceiver data (if present) is nested in the port stats response.

## Related Endpoints

- [GET_sites_site_id_stats_ports_count.md](GET_sites_site_id_stats_ports_count.md) — Count ports
- [GET_sites_site_id_stats_switches_metrics.md](GET_sites_site_id_stats_switches_metrics.md) — Switch metrics

## MistHelper Notes

Used by Menus **14, 29, 31** via `searchSiteSwOrGwPorts` for port data export and SFP transceiver data collection.
