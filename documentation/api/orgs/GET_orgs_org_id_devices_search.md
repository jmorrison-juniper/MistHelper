# searchOrgDevices

> searchOrgDevices

## HTTP

`GET /api/v1/orgs/{org_id}/devices/search`

## Description

Search Org Devices

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
| band_24_bandwidth | integer | No |  |  | If `type`==`ap`, Bandwidth of band_24 |
| band_24_channel | integer | No |  |  | If `type`==`ap`, Channel of band_24 |
| band_24_power | integer | No |  |  | If `type`==`ap`, Power of band_24 |
| band_5_bandwidth | integer | No |  |  | If `type`==`ap`, Bandwidth of band_5 |
| band_5_channel | integer | No |  |  | If `type`==`ap`, Channel of band_5 |
| band_5_power | integer | No |  |  | If `type`==`ap`, Power of band_5 |
| band_6_bandwidth | integer | No |  |  | If `type`==`ap`, Bandwidth of band_6 |
| band_6_channel | integer | No |  |  | If `type`==`ap`, Channel of band_6 |
| band_6_power | integer | No |  |  | If `type`==`ap`, Power of band_6 |
| cpu | string | No |  |  | If `type`==`switch` or `type`==`gateway`, max cpu usage |
| clustered | string | No |  |  | If `type`==`gateway`, true / false |
| eth0_port_speed | integer | No |  |  | If `type`==`ap`, Port speed of eth0 |
| evpntopo_id | string | No |  |  | If `type`==`switch`, EVPN topology id |
| ext_ip | string | No |  |  | External IP Address |
| hostname | string | No |  |  | Partial / full hostname |
| ip | string | No |  |  |  |
| last_config_status | string | No |  |  | If `type`==`switch` or `type`==`gateway`, last configuration status |
| last_hostname | string | No |  |  | If `type`==`switch` or `type`==`gateway`, last hostname |
| lldp_mgmt_addr | string | No |  |  | If `type`==`ap`, LLDP management ip address |
| lldp_port_id | string | No |  |  | If `type`==`ap`, LLDP port id |
| lldp_power_allocated | integer | No |  |  | If `type`==`ap`, LLDP Allocated Power |
| lldp_power_draw | integer | No |  |  | If `type`==`ap`, LLDP Negotiated Power |
| lldp_system_desc | string | No |  |  | If `type`==`ap`, LLDP system description |
| lldp_system_name | string | No |  |  | If `type`==`ap`, LLDP system name |
| mac | string | No |  |  | Device mac |
| model | string | No |  |  | Device model |
| mxedge_id | string | No |  |  | If `type`==`ap`, Mist Edge id, if AP is connecting to a Mist Edge |
| mxedge_ids | string | No |  |  | If `type`==`ap`, Comma separated list of Mist Edge ids, if AP is connecting to a Mist Edge |
| mxtunnel_status | string | No |  |  | If `type`==`ap`, MxTunnel status, up / down |
| node | string | No |  |  | If `type`==`gateway`, `node0` / `node1` |
| node0_mac | string | No |  |  | If `type`==`gateway`, mac for node0 |
| node1_mac | string | No |  |  | If `type`==`gateway`, mac for node1 |
| power_constrained | boolean | No |  |  | If `type`==`ap`, Power_constrained |
| site_id | string | No |  |  | Site id |
| t128agent_version | string | No |  |  | If `type`==`gateway`,version of 128T agent |
| version | string | No |  |  | Version |
| type | string | No |  |  | Type of device. enum: `ap`, `gateway`, `switch` |
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
      "type": "integer",
      "contentEncoding": "int32"
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
        "oneOf": [
          {
            "title": "ap_search",
            "required": [
              "mxtunnel_status",
              "power_constrained",
              "power_opmode",
              "wlans"
            ],
            "type": "object",
            "properties": {
              "band_24_bandwidth": {
                "type": "string",
                "description": "Bandwidth of band_24"
              },
              "band_24_channel": {
                "type": "integer",
                "description": "Channel of band_24",
                "contentEncoding": "int32"
              },
              "band_24_power": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "band_5_bandwidth": {
                "type": "string",
                "description": "Bandwidth of band_5"
              },
              "band_5_channel": {
                "type": "integer",
                "description": "Channel of band_5",
                "contentEncoding": "int32"
              },
              "band_5_power": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "band_6_bandwidth": {
                "type": "string"
              },
              "band_6_channel": {
                "type": "integer",
                "description": "Channel of band_6",
                "contentEncoding": "int32"
              },
              "band_6_power": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "eth0_port_speed": {
                "type": "integer",
                "description": "Port speed of eth0",
                "contentEncoding": "int32"
              },
              "ext_ip": {
                "type": "string"
              },
              "hostname": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "Partial / full hostname"
              },
              "inactive_wired_vlans": {
                "type": "array",
                "items": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "description": ""
              },
              "ip": {
                "type": "string",
                "description": "IP Address"
              },
              "last_hostname": {
                "type": "string"
              },
              "lldp_mgmt_addr": {
                "type": "string",
                "description": "LLDP management ip address"
              },
              "lldp_port_desc": {
                "type": "string"
              },
              "lldp_port_id": {
                "type": "string",
                "description": "LLDP port id"
              },
              "lldp_power_allocated": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "lldp_power_draw": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "lldp_system_desc": {
                "type": "string",
                "description": "LLDP system description"
              },
              "lldp_system_name": {
                "type": "string",
                "description": "LLDP system name"
              },
              "mac": {
                "type": "string",
                "description": "Device model"
              },
              "model": {
                "type": "string"
              },
              "mxedge_id": {
                "type": "string",
                "description": "Mist Edge id, if AP is connecting to a Mist Edge"
              },
              "mxedge_ids": {
                "type": "string",
                "description": "Comma separated list of Mist Edge ids, if AP is connecting to a Mist Edge"
              },
              "mxtunnel_status": {
                "type": "string",
                "description": "MxTunnel status"
              },
              "org_id": {
                "type": "string",
                "contentEncoding": "uuid",
                "readOnly": true,
                "examples": [
                  "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
                ]
              },
              "power_constrained": {
                "type": "boolean"
              },
              "power_opmode": {
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
              "sku": {
                "type": "string"
              },
              "timestamp": {
                "type": "number",
                "description": "Epoch (seconds)",
                "readOnly": true
              },
              "uptime": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "version": {
                "type": "string",
                "description": "Version"
              },
              "wlans": {
                "type": "array",
                "items": {
                  "title": "ap_search_wlan",
                  "type": "object",
                  "properties": {
                    "id": {
                      "type": "string",
                      "contentEncoding": "uuid"
                    },
                    "ssid": {
                      "type": "string"
                    }
                  }
                },
                "description": ""
              }
            }
          },
          {
            "title": "switch_search",
            "required": [
              "type"
            ],
            "type": "object",
            "properties": {
              "clustered": {
                "type": "boolean"
              },
              "evpn_missing_links": {
                "type": "boolean"
              },
              "evpntopo_id": {
                "type": "string"
              },
              "ext_ip": {
                "type": "string"
              },
              "hostname": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "ip": {
                "type": "string"
              },
              "last_config_status": {
                "type": "string"
              },
              "last_hostname": {
                "type": "string"
              },
              "last_trouble_code": {
                "type": "string"
              },
              "last_trouble_timestamp": {
                "type": "number",
                "description": "Epoch (seconds)",
                "readOnly": true
              },
              "mac": {
                "type": "string"
              },
              "managed": {
                "type": "boolean",
                "deprecated": true
              },
              "mist_configured": {
                "type": "boolean",
                "description": "whether the device can be configured by Mist or not. This deprecates `managed` (for adopted device) and `disable_auto_config` for claimed device)"
              },
              "model": {
                "type": "string"
              },
              "num_members": {
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
              "radius_stats": {
                "type": "object",
                "additionalProperties": {
                  "title": "device_search_radius_stat",
                  "type": "object",
                  "properties": {
                    "auth_accepts": {
                      "type": "integer",
                      "description": "Number of accepted authentication requests",
                      "contentEncoding": "int32"
                    },
                    "auth_rejects": {
                      "type": "integer",
                      "description": "Number of rejected authentication requests",
                      "contentEncoding": "int32"
                    },
                    "auth_server_status": {
                      "type": "string",
                      "description": "Status of the device search radius filter. enum: `up`, `down`, `unreachable`"
                    },
                    "auth_timeouts": {
                      "type": "integer",
                      "description": "Number of authentication timeouts",
                      "contentEncoding": "int32"
                    }
                  }
                },
                "description": "Property key is the RADIUS server IP Address"
              },
              "role": {
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
              "time_drifted": {
                "type": "boolean"
              },
              "timestamp": {
                "type": "number",
                "description": "Epoch (seconds)",
                "readOnly": true
              },
              "type": {
                "const": "switch",
                "type": "string",
                "description": "Device Type. enum: `switch`"
              },
              "uptime": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "version": {
                "type": "string"
              }
            }
          },
          {
            "title": "gateway_search",
            "required": [
              "type"
            ],
            "type": "object",
            "properties": {
              "clustered": {
                "type": "boolean"
              },
              "evpn_missing_links": {
                "type": "boolean"
              },
              "evpntopo_id": {
                "type": "string"
              },
              "ext_ip": {
                "type": "string"
              },
              "hostname": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "ip": {
                "type": "string"
              },
              "last_config_status": {
                "type": "string"
              },
              "last_hostname": {
                "type": "string"
              },
              "last_trouble_code": {
                "type": "string"
              },
              "last_trouble_timestamp": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "mac": {
                "type": "string"
              },
              "managed": {
                "type": "boolean",
                "deprecated": true
              },
              "mist_configured": {
                "type": "boolean",
                "description": "whether the device can be configured by Mist or not. This deprecates `managed` (for adopted device) and `disable_auto_config` for claimed device)"
              },
              "model": {
                "type": "string"
              },
              "node": {
                "type": "string"
              },
              "node0_mac": {
                "type": "string"
              },
              "node1_mac": {
                "type": "string"
              },
              "num_members": {
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
              "role": {
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
              "t128agent_version": {
                "type": "string"
              },
              "time_drifted": {
                "type": "boolean"
              },
              "timestamp": {
                "type": "number",
                "description": "Epoch (seconds)",
                "readOnly": true
              },
              "type": {
                "const": "gateway",
                "type": "string",
                "description": "Device Type. enum: `gateway`"
              },
              "uptime": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "version": {
                "type": "string"
              }
            }
          }
        ]
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

`mistapi.api.v1.orgs.devices.searchOrgDevices()`

## Usage Context

Searches devices across the organization with filtering by model, type, name, MAC, and more.

## Gotchas

- Returns all device types (AP, switch, gateway) unless filtered.
- Use `limit` for pagination on large inventories.

## Related Endpoints

- [GET_orgs_org_id_devices_count.md](GET_orgs_org_id_devices_count.md) — Count devices
- [GET_orgs_org_id_devices_summary.md](GET_orgs_org_id_devices_summary.md) — Device summary

## MistHelper Notes

Used by MistHelper via `searchOrgDevices` in Menu 16 and related menus.
