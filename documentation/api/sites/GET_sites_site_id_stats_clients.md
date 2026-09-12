# listSiteWirelessClientsStats

> listSiteWirelessClientsStats

## HTTP

`GET /api/v1/sites/{site_id}/stats/clients`

## Description

Get List of Site All Clients Stats Details

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
| wired | boolean | No | False |  |  |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "array",
  "items": {
    "oneOf": [
      {
        "title": "stats_wireless_client",
        "required": [
          "ap_id",
          "ap_mac",
          "band",
          "channel",
          "is_guest",
          "key_mgmt",
          "mac",
          "proto",
          "rssi",
          "snr",
          "ssid",
          "wlan_id"
        ],
        "type": "object",
        "properties": {
          "accuracy": {
            "type": "integer",
            "description": "Estimated client location accuracy, in meter",
            "contentEncoding": "int32"
          },
          "airespace_ifname": {
            "type": "string"
          },
          "airwatch": {
            "type": "object",
            "properties": {
              "authorized": {
                "type": "boolean"
              }
            },
            "required": [
              "authorized"
            ],
            "description": "Information if airwatch enabled"
          },
          "annotation": {
            "type": "string"
          },
          "ap_id": {
            "type": "string",
            "description": "AP ID the client is connected to",
            "contentEncoding": "uuid"
          },
          "ap_mac": {
            "type": "string",
            "description": "AP the client is connected to"
          },
          "assoc_time": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "band": {
            "type": "string",
            "description": "enum: `24`, `5`, `6`"
          },
          "bssid": {
            "type": "string"
          },
          "channel": {
            "type": "integer",
            "description": "Current channel",
            "contentEncoding": "int32"
          },
          "dual_band": {
            "type": "boolean",
            "description": "Whether the client is dual_band capable (determined by whether we\u2019ve seen probe requests from both bands)"
          },
          "family": {
            "type": "string",
            "description": "Device family, through fingerprinting. iPod / Nexus Galaxy / Windows Mobile or CE \u2026"
          },
          "group": {
            "type": "string"
          },
          "guest": {
            "type": "object",
            "properties": {
              "access_code_email": {
                "type": "string",
                "description": "If `auth_method`==`email`, the email address where the authorization code has been sent to",
                "readOnly": true
              },
              "ap_mac": {
                "type": "string",
                "description": "MAC Address of the AP the guest was connected to during the registration process",
                "readOnly": true
              },
              "auth_method": {
                "type": "string",
                "description": "Type of guest authorization",
                "readOnly": true
              },
              "authorized": {
                "type": "boolean",
                "description": "Whether the guest is current authorized",
                "default": true
              },
              "authorized_expiring_time": {
                "type": "number",
                "description": "When the authorization would expire",
                "readOnly": true,
                "examples": [
                  1480704955
                ]
              },
              "authorized_time": {
                "type": "number",
                "description": "When the guest was authorized",
                "readOnly": true,
                "examples": [
                  1480704355
                ]
              },
              "company": {
                "type": "string",
                "description": "Optional, the info provided by user",
                "examples": [
                  "abc"
                ]
              },
              "email": {
                "type": "string",
                "description": "Optional, the info provided by user",
                "examples": [
                  "john@abc.com"
                ]
              },
              "field1": {
                "type": "string",
                "description": "Optional, the info provided by user"
              },
              "field2": {
                "type": "string"
              },
              "field3": {
                "type": "string"
              },
              "field4": {
                "type": "string"
              },
              "mac": {
                "type": "string",
                "description": "MAC Address",
                "readOnly": true
              },
              "minutes": {
                "maximum": 259200.0,
                "minimum": 0.0,
                "type": "integer",
                "description": "Authorization duration, in minutes. Default is 1440 minutes (1 day), maximum is 259200 (180 days)",
                "contentEncoding": "int32",
                "default": 1440
              },
              "name": {
                "type": "string",
                "description": "Optional, the info provided by user",
                "readOnly": true,
                "examples": [
                  "John Smith"
                ]
              },
              "random_mac": {
                "type": "boolean",
                "description": "If the client is using a randomized MAC Address to connect the SSID",
                "readOnly": true
              },
              "ssid": {
                "type": "string",
                "description": "Name of the SSID",
                "readOnly": true,
                "examples": [
                  "Guest-SSID"
                ]
              },
              "wlan_id": {
                "type": "string",
                "description": "ID of the SSID",
                "contentEncoding": "uuid",
                "readOnly": true,
                "examples": [
                  "6748cfa6-4e12-11e6-9188-0242ac110007"
                ]
              }
            },
            "description": "Guest"
          },
          "hostname": {
            "type": "string",
            "description": "Hostname that we learned from sniffing DHCP"
          },
          "idle_time": {
            "type": "number",
            "description": "How long, in seconds, has the client been idle (since the last RX packet)"
          },
          "ip": {
            "type": "string"
          },
          "is_guest": {
            "type": "boolean",
            "description": "Whether this is a guest"
          },
          "key_mgmt": {
            "type": "string",
            "description": "E.g. WPA2-PSK/CCMP"
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
          "mac": {
            "type": "string",
            "description": "Client mac"
          },
          "manufacture": {
            "type": "string",
            "description": "Device manufacture, through fingerprinting or OUI"
          },
          "map_id": {
            "type": "string",
            "description": "Estimated client location - map_id",
            "contentEncoding": "uuid"
          },
          "model": {
            "type": "string",
            "description": "Device model, may be available if we can identify them"
          },
          "num_locating_aps": {
            "type": "integer",
            "description": "Number of APs used to locate this client",
            "contentEncoding": "int32"
          },
          "os": {
            "type": "string",
            "description": "Device os, through fingerprinting"
          },
          "power_saving": {
            "type": "boolean",
            "description": "If it\u2019s currently in power-save mode"
          },
          "proto": {
            "type": "string",
            "description": "enum: `a`, `ac`, `ax`, `b`, `be`, `g`, `n`"
          },
          "psk_id": {
            "type": "string",
            "description": "PSK id (if multi-psk is used)",
            "contentEncoding": "uuid"
          },
          "rssi": {
            "type": "number",
            "description": "Signal strength"
          },
          "rssizones": {
            "type": "array",
            "items": {
              "title": "stats_wireless_client_rssi_zone",
              "type": "object",
              "properties": {
                "id": {
                  "type": "string",
                  "description": "Unique ID of the object instance in the Mist Organization",
                  "contentEncoding": "uuid",
                  "readOnly": true,
                  "examples": [
                    "53f10664-3ce8-4c27-b382-0ef66432349f"
                  ]
                },
                "since": {
                  "type": "number"
                }
              }
            },
            "description": "List of rssizone_id\u2019s where client is in and since when (if known)"
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
          "rx_rate": {
            "type": [
              "number",
              "null"
            ],
            "description": "RX Rate, Mbps",
            "readOnly": true
          },
          "rx_retries": {
            "type": [
              "integer",
              "null"
            ],
            "description": "Amount of rx retries",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "snr": {
            "type": "number",
            "description": "Signal over noise"
          },
          "ssid": {
            "type": "string",
            "description": "SSID the client is connected to"
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
          "tx_rate": {
            "type": [
              "number",
              "null"
            ],
            "description": "TX Rate, Mbps",
            "readOnly": true
          },
          "tx_retries": {
            "type": [
              "integer",
              "null"
            ],
            "description": "Amount of tx retries",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "type": {
            "type": "string",
            "description": "Client\u2019s type, regular / vip / resource / blocked (if client object is created)"
          },
          "uptime": {
            "type": "number",
            "description": "How long, in seconds, has the client been connected"
          },
          "username": {
            "type": "string",
            "description": "Username that we learned from 802.1X exchange or Per_user PSK or User Portal"
          },
          "vbeacons": {
            "type": "array",
            "items": {
              "title": "stats_wireless_client_vbeacon",
              "type": "object",
              "properties": {
                "id": {
                  "type": "string",
                  "description": "Unique ID of the object instance in the Mist Organization",
                  "contentEncoding": "uuid",
                  "readOnly": true,
                  "examples": [
                    "53f10664-3ce8-4c27-b382-0ef66432349f"
                  ]
                },
                "since": {
                  "type": "number"
                }
              }
            },
            "description": "List of beacon_id\u2019s where the client is in and since when (if known)"
          },
          "vlan_id": {
            "type": "string",
            "description": "VLAN id, could be empty (from older AP)"
          },
          "wlan_id": {
            "type": "string",
            "description": "WLAN ID the client is connected to",
            "contentEncoding": "uuid"
          },
          "wxrule_id": {
            "type": "string",
            "description": "Current WxlanRule using for a Client or an authorized Guest (portal user). null if default rule is matched.",
            "contentEncoding": "uuid"
          },
          "wxrule_usage": {
            "type": "array",
            "items": {
              "title": "stats_wireless_client_wxrule_usage",
              "type": "object",
              "properties": {
                "tag_id": {
                  "type": "string",
                  "contentEncoding": "uuid"
                },
                "usage": {
                  "type": "integer",
                  "contentEncoding": "int32"
                }
              }
            },
            "description": "Current WxlanRule usage per tag_id"
          },
          "x": {
            "type": "number",
            "description": "Estimated client location in pixels"
          },
          "x_m": {
            "type": "number",
            "description": "Estimated client location in meter"
          },
          "y": {
            "type": "number",
            "description": "Estimated client location in pixels"
          },
          "y_m": {
            "type": "number",
            "description": "Estimated client location in meter"
          },
          "zones": {
            "type": "array",
            "items": {
              "title": "stats_wireless_client_zone",
              "type": "object",
              "properties": {
                "id": {
                  "type": "string",
                  "description": "Unique ID of the object instance in the Mist Organization",
                  "contentEncoding": "uuid",
                  "readOnly": true,
                  "examples": [
                    "53f10664-3ce8-4c27-b382-0ef66432349f"
                  ]
                },
                "since": {
                  "type": "number"
                }
              }
            },
            "description": "List of zone_id\u2019s where client is in and since when (if known)"
          }
        }
      },
      {
        "title": "stats_wired_client",
        "required": [
          "mac"
        ],
        "type": "object",
        "properties": {
          "auth_state": {
            "minLength": 1,
            "type": "string",
            "description": "Client authorization status"
          },
          "device_id": {
            "minLength": 1,
            "type": "string",
            "description": "Device ID the client is connected to"
          },
          "eth_port": {
            "minLength": 1,
            "type": "string",
            "description": "Port on AP where the wired client is connected"
          },
          "last_seen": {
            "type": "number",
            "description": "Time when last Tx/Rx observed"
          },
          "mac": {
            "minLength": 1,
            "type": "string",
            "description": "Client mac"
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
          "uptime": {
            "type": "number",
            "description": "How long, in seconds, has the client been connected"
          },
          "vlan_id": {
            "type": "number",
            "description": "VLAN id, could be empty"
          }
        }
      }
    ]
  },
  "description": "",
  "examples": [
    [
      {
        "annotation": "unknown",
        "ap_id": "00000000-0000-0000-1000-5c5b35963d70",
        "ap_mac": "5c5b358e6fea",
        "assoc_time": 1741152905,
        "band": "5",
        "bssid": "5c5b358298f2",
        "channel": 157,
        "dual_band": true,
        "family": "",
        "group": "",
        "hostname": "android-9b228dc33690",
        "idle_time": 5,
        "ip": "10.100.0.47",
        "is_guest": false,
        "key_mgmt": "WPA3-SAE-FT/CCMP",
        "last_seen": 1741257505,
        "mac": "dadbfc123456",
        "manufacture": "Unknown",
        "map_id": "ed7a0a4e-8835-4c94-ba78-6c1169c9f135",
        "model": "",
        "num_locating_aps": 2,
        "os": "Android 10",
        "proto": "ac",
        "rssi": -39,
        "rx_bps": 0,
        "rx_bytes": 14451780,
        "rx_pkts": 44175,
        "rx_rate": 6,
        "rx_retries": 2010,
        "site_id": "96c348a9-d6d7-4732-b4f5-23350a2843cd",
        "snr": 47,
        "ssid": "Live_demo_only",
        "tx_bps": 0,
        "tx_bytes": 56364072,
        "tx_pkts": 43685,
        "tx_rate": 173.3,
        "tx_retries": 5413,
        "uptime": 104600,
        "vlan_id": "1",
        "wlan_id": "497fc18a-79b5-405a-bf5a-192eed31ea60",
        "x": 695.3357339330526,
        "x_m": 24.086588,
        "y": 760.6746524247893,
        "y_m": 26.349943
      }
    ]
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

`mistapi.api.v1.sites.stats_-_clients_wireless.listSiteWirelessClientsStats()`

## Usage Context

Retrieves wireless client statistics at a site, including connection details, signal quality, and data usage.

## Gotchas

- Returns currently connected clients only. For historical data, use the search/insights endpoints.

## Related Endpoints

- [GET_sites_site_id_stats_clients_client_mac.md](GET_sites_site_id_stats_clients_client_mac.md) — Specific client stats
- [GET_sites_site_id_clients_search.md](GET_sites_site_id_clients_search.md) — Search clients

## MistHelper Notes

Used by Menus **29, 68** via `listSiteClientsStats` for wireless client data export.
