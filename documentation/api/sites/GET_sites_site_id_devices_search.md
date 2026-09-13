# searchSiteDevices

> searchSiteDevices

## HTTP

`GET /api/v1/sites/{site_id}/devices/search`

## Description

Search Device

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
| hostname | string | No |  |  | Partial / full hostname |
| type | string | No |  |  |  |
| model | string | No |  |  | Device model |
| mac | string | No |  |  | Device MAC |
| ext_ip | string | No |  |  | Device external ip |
| version | string | No |  |  | Version |
| power_constrained | boolean | No |  |  | power_constrained |
| ip | string | No |  |  |  |
| mxtunnel_status | string | No |  |  | For APs only, MxTunnel status, up / down. |
| mxedge_id | string | No |  |  | For APs only, Mist Edge id, if AP is connecting to a Mist Edge |
| mxedge_ids | array | No |  |  | For APs only, list of Mist Edge id, if AP is connecting to a Mist Edge |
| last_hostname | string | No |  |  | For Switches and Gateways only, last hostname |
| last_config_status | string | No |  |  | For Switches and Gateways only, last configuration status of the switch/gateway |
| radius_stats | string | No |  |  | For Switches and Gateways only, Key-value pairs where the key is the RADIUS server address and the value contains authentication statistics:   *  <server_address> (string): IP address of the RADIUS server as the key   * `auth_accepts` (long): Number of accepted authentication requests   * `auth_rejects` (long): Number of rejected authentication requests   * `auth_timeouts` (long): Number of authentication timeouts   * `auth_server_status` (string): Status of the server. Possible values: `up`, `down`, `unreachable` |
| cpu | string | No |  |  | For Switches and Gateways only, max cpu usage |
| node0_mac | string | No |  |  | For Gateways only, node0 MAC Address |
| clustered | boolean | No |  |  | For Gateways only |
| t128agent_version | string | No |  |  | For Gateways (SSR) only, version of 128T agent |
| node1_mac | string | No |  |  | For Gateways only, node1 MAC Address |
| node | string | No |  |  | For Gateways only. enum: `node0`, `node1` |
| evpntopo_id | string | No |  |  | For Switches only, EVPN topology id |
| lldp_system_name | string | No |  |  | For APs only, LLDP system name |
| lldp_system_desc | string | No |  |  | For APs only, LLDP system description |
| lldp_port_id | string | No |  |  | For APs only, LLDP port id |
| lldp_mgmt_addr | string | No |  |  | For APs only, LLDP management ip address |
| band_24_channel | integer | No |  |  | Channel of band_24 |
| band_5_channel | integer | No |  |  | Channel of band_5 |
| band_6_channel | integer | No |  |  | Channel of band_6 |
| band_24_bandwidth | integer | No |  |  | Bandwidth of band_24 |
| band_5_bandwidth | integer | No |  |  | Bandwidth of band_5 |
| band_6_bandwidth | integer | No |  |  | Bandwidth of band_6 |
| eth0_port_speed | integer | No |  |  | Port speed of eth0 |
| stats | boolean | No | False |  | Whether to return device stats |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| sort | string | No |  |  | Sort options |
| desc_sort | string | No |  |  | Sort options in reverse order |
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

`mistapi.api.v1.sites.devices.searchSiteDevices()`

## Usage Context

Searches devices at a site with filtering by model, MAC, hostname, version, type, and status. Supports cursor-based pagination.

## Gotchas

- Uses cursor-based pagination. Check `next` for additional pages.

## Related Endpoints

- [GET_sites_site_id_devices.md](GET_sites_site_id_devices.md) — List all devices
- [GET_sites_site_id_devices_count.md](GET_sites_site_id_devices_count.md) — Count devices

## MistHelper Notes

Not currently used by MistHelper directly. `listSiteDevices` is preferred for site-level operations.
