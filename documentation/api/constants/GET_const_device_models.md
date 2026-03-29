# listDeviceModels

> listDeviceModels

## HTTP

`GET /api/v1/const/device_models`

## Description

Get list of AP device models for the Mist Site

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of supported device models

```json
{
  "type": "array",
  "items": {
    "oneOf": [
      {
        "title": "const_device_ap",
        "required": [
          "ap_type",
          "type"
        ],
        "type": "object",
        "properties": {
          "ap_type": {
            "type": "string",
            "examples": [
              "jewel"
            ]
          },
          "band24": {
            "title": "const_device_ap_band24",
            "type": "object",
            "properties": {
              "band5_channels_op": {
                "type": "string",
                "examples": [
                  "low"
                ]
              },
              "max_clients": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  128
                ]
              },
              "max_power": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  19
                ]
              },
              "min_power": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  8
                ]
              }
            }
          },
          "band5": {
            "title": "const_device_ap_band5",
            "type": "object",
            "properties": {
              "max_clients": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  128
                ]
              },
              "max_power": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  17
                ]
              },
              "min_power": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  8
                ]
              }
            }
          },
          "band6": {
            "title": "const_device_ap_band5",
            "type": "object",
            "properties": {
              "max_clients": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  128
                ]
              },
              "max_power": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  17
                ]
              },
              "min_power": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  8
                ]
              }
            }
          },
          "band_24_usages": {
            "type": "array",
            "items": {
              "title": "const_device_ap_band_24_usage",
              "enum": [
                "24",
                "5",
                "6"
              ],
              "type": "string",
              "description": "enum: `24`, `5`, `6`"
            },
            "description": ""
          },
          "ce_dfs_ok": {
            "type": "boolean",
            "examples": [
              true
            ]
          },
          "cisco_pace": {
            "type": "boolean"
          },
          "description": {
            "type": "string",
            "examples": [
              "AP-45"
            ]
          },
          "disallowed_channels": {
            "type": "object",
            "additionalProperties": {
              "type": "array",
              "items": {
                "type": "integer",
                "format": "int32"
              },
              "description": "Property key is a list of country codes (e.g. \"GB, DE\")"
            },
            "description": "Property key is a list of country codes (e.g. \"GB, DE\")"
          },
          "display": {
            "type": "string",
            "examples": [
              "AP45"
            ]
          },
          "extio": {
            "type": "object",
            "additionalProperties": {
              "title": "const_device_ap_extios",
              "type": "object",
              "properties": {
                "default_dir": {
                  "type": "string",
                  "description": "enum: `IN`, `OUT`"
                },
                "input": {
                  "type": "boolean"
                },
                "output": {
                  "type": "boolean"
                }
              }
            },
            "description": "Property key is the GPIO port name (e.g. \"D0\", \"A1\")"
          },
          "fcc_dfs_ok": {
            "type": "boolean",
            "examples": [
              true
            ]
          },
          "has_11ax": {
            "type": "boolean"
          },
          "has_compass": {
            "type": "boolean",
            "examples": [
              false
            ]
          },
          "has_ext_ant": {
            "type": "boolean"
          },
          "has_extio": {
            "type": "boolean",
            "examples": [
              false
            ]
          },
          "has_height": {
            "type": "boolean",
            "examples": [
              false
            ]
          },
          "has_module_port": {
            "type": "boolean"
          },
          "has_poe_out": {
            "type": "boolean",
            "examples": [
              true
            ]
          },
          "has_scanning_radio": {
            "type": "boolean",
            "examples": [
              true
            ]
          },
          "has_selectable_radio": {
            "type": "boolean",
            "examples": [
              true
            ]
          },
          "has_usb": {
            "type": "boolean"
          },
          "has_vble": {
            "type": "boolean",
            "examples": [
              true
            ]
          },
          "has_wifi_band24": {
            "type": "boolean",
            "examples": [
              true
            ]
          },
          "has_wifi_band5": {
            "type": "boolean",
            "examples": [
              true
            ]
          },
          "has_wifi_band6": {
            "type": "boolean",
            "examples": [
              true
            ]
          },
          "max_poe_out": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              15400
            ]
          },
          "max_wlans": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "model": {
            "type": "string",
            "examples": [
              "AP45"
            ]
          },
          "other_dfs_ok": {
            "type": "boolean",
            "examples": [
              true
            ]
          },
          "outdoor": {
            "type": "boolean"
          },
          "radios": {
            "type": "object",
            "additionalProperties": {
              "type": "string"
            },
            "description": "Property key is the radio number (e.g. r0, r1, ...). Property value is the RF band (e.g. \"24\", \"5\", ...)",
            "examples": [
              {
                "r0": "6",
                "r1": "5",
                "r2": "24"
              }
            ]
          },
          "shared_scanning_radio": {
            "type": "boolean"
          },
          "type": {
            "const": "ap",
            "type": "string",
            "description": "Device Type. enum: `ap`",
            "readOnly": true
          },
          "unmanaged": {
            "type": "boolean"
          },
          "vble": {
            "title": "const_device_ap_vble",
            "type": "object",
            "properties": {
              "beacon_rate": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  4
                ]
              },
              "beams": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  9
                ]
              },
              "power": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  8
                ]
              }
            }
          }
        }
      },
      {
        "title": "const_device_switch",
        "required": [
          "type"
        ],
        "type": "object",
        "properties": {
          "alias": {
            "type": "string",
            "examples": [
              "EX4100-48P-CHAS"
            ]
          },
          "defaults": {
            "title": "const_device_switch_default",
            "type": "object",
            "properties": {
              "_ports": {
                "type": "string",
                "examples": [
                  "ge-0/0/0-47, et-0/1/0-3, xe-0/2/0-3, ge-0/2/0-3"
                ]
              }
            }
          },
          "description": {
            "type": "string",
            "examples": [
              "Juniper EX4100 Series"
            ]
          },
          "display": {
            "type": "string",
            "examples": [
              "EX4100-48P"
            ]
          },
          "evolved_os": {
            "type": "boolean",
            "default": false
          },
          "evpn_ri_type": {
            "type": "string",
            "examples": [
              "mac-vrf"
            ]
          },
          "experimental": {
            "type": "boolean",
            "default": false
          },
          "fans_pluggable": {
            "type": "boolean",
            "default": false,
            "examples": [
              true
            ]
          },
          "has_bgp": {
            "type": "boolean",
            "default": false,
            "examples": [
              true
            ]
          },
          "has_ets": {
            "type": "boolean",
            "default": false
          },
          "has_evpn": {
            "type": "boolean",
            "default": false,
            "examples": [
              true
            ]
          },
          "has_irb": {
            "type": "boolean",
            "default": false,
            "examples": [
              true
            ]
          },
          "has_poe_out": {
            "type": "boolean",
            "default": false,
            "examples": [
              true
            ]
          },
          "has_snapshot": {
            "type": "boolean",
            "default": true
          },
          "has_vc": {
            "type": "boolean",
            "default": true,
            "examples": [
              true
            ]
          },
          "model": {
            "type": "string",
            "examples": [
              "EX4100-48P"
            ]
          },
          "modular": {
            "type": "boolean",
            "default": false
          },
          "no_shaping_rate": {
            "type": "boolean",
            "default": false
          },
          "number_fans": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              2
            ]
          },
          "oc_device": {
            "type": "boolean",
            "default": false,
            "examples": [
              true
            ]
          },
          "oob_interface": {
            "type": "string",
            "examples": [
              "re0:mgmt-0, re1:mgmt-0"
            ]
          },
          "packet_action_drop_only": {
            "type": "boolean",
            "default": false
          },
          "pic": {
            "type": "object",
            "additionalProperties": {
              "type": "string"
            },
            "description": "Object Key is the PIC number",
            "examples": [
              {
                "0": "ge*48",
                "1": "qsfp+*4",
                "2": "sfp+*4 (uplink)"
              }
            ]
          },
          "sub_required": {
            "type": "string"
          },
          "type": {
            "const": "switch",
            "type": "string",
            "description": "Device Type. enum: `switch`",
            "readOnly": true
          }
        }
      },
      {
        "title": "const_device_gateway",
        "required": [
          "type"
        ],
        "type": "object",
        "properties": {
          "defaults": {
            "type": "object",
            "additionalProperties": {
              "type": "string"
            },
            "description": "Object Key is the interface type name (e.g. \"lan_ports\", \"wan_ports\", ...)"
          },
          "description": {
            "type": "string"
          },
          "experimental": {
            "type": "boolean",
            "default": false
          },
          "fans_pluggable": {
            "type": "boolean",
            "default": true
          },
          "ha_node0_fpc": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "ha_node1_fpc": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "has_bgp": {
            "type": "boolean",
            "default": false
          },
          "has_fxp0": {
            "type": "boolean",
            "default": true
          },
          "has_ha_control": {
            "type": "boolean",
            "default": false
          },
          "has_ha_data": {
            "type": "boolean",
            "default": false
          },
          "has_irb": {
            "type": "boolean",
            "default": false
          },
          "has_poe_out": {
            "type": "boolean",
            "default": true
          },
          "has_snapshot": {
            "type": "boolean",
            "default": true
          },
          "irb_disabled_by_default": {
            "type": "boolean",
            "default": false
          },
          "model": {
            "type": "string"
          },
          "number_fans": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "oc_device": {
            "type": "boolean",
            "default": false
          },
          "pic": {
            "type": "object",
            "additionalProperties": {
              "type": "string"
            },
            "description": "Object Key is the PIC number"
          },
          "ports": {
            "type": "object",
            "properties": {
              "display": {
                "type": "string"
              },
              "pci_address": {
                "type": "string"
              },
              "speed": {
                "type": "integer",
                "contentEncoding": "int32"
              }
            },
            "description": "Object Key is the interface name (e.g. \"ge-0/0/1\", ...)"
          },
          "sub_required": {
            "type": "string"
          },
          "t128_device": {
            "type": "boolean",
            "default": false
          },
          "type": {
            "const": "gateway",
            "type": "string",
            "description": "Device Type. enum: `gateway`",
            "readOnly": true
          }
        }
      }
    ],
    "discriminator": {
      "propertyName": "type",
      "mapping": {
        "ap": "const_device_ap",
        "gateway": "const_device_switch",
        "switch": "const_device_gateway"
      }
    }
  },
  "description": "",
  "examples": [
    "[{\"defaults\":{\"ha_control_port\":\"ge-0/0/1\",\"ha_data_ports\":\"ge-0/0/2,ge-3/0/2\",\"ha_fxp0_port\":\"ge-0/0/0\",\"ha_lan_ports\":\"ge-0/0/4,ge-3/0/4\",\"ha_wan_ports\":\"ge-0/0/3,ge-3/0/3\",\"lan_ports\":\"ge-0/0/1-6\",\"lte_wan_ports\":\"cl-1/0/0\",\"wan_ports\":\"ge-0/0/0,ge-0/0/7\"},\"description\":\"Juniper SRX320 Series\",\"fans_pluggable\":false,\"ha_node0_fpc\":3,\"ha_node1_fpc\":3,\"has_bgp\":true,\"has_fxp0\":false,\"has_ha_control\":false,\"has_ha_data\":false,\"has_irb\":true,\"has_poe_out\":true,\"has_snapshot\":true,\"irb_disabled_by_default\":false,\"model\":\"SRX320\",\"number_fans\":1,\"oc_device\":true,\"pic\":{\"0\":\"ge*6, sfp*2\"},\"sub_required\":\"wan1\",\"type\":\"gateway\"}]",
    "[{\"alias\":\"EX4100-48P-CHAS\",\"defaults\":{\"_ports\":\"ge-0/0/0-47, et-0/1/0-3, xe-0/2/0-3, ge-0/2/0-3\"},\"description\":\"Juniper EX4100 Series\",\"display\":\"EX4100-48P\",\"evolved_os\":false,\"evpn_ri_type\":\"mac-vrf\",\"fans_pluggable\":true,\"has_bgp\":true,\"has_ets\":true,\"has_evpn\":true,\"has_irb\":true,\"has_poe_out\":true,\"model\":\"EX4100-48P\",\"modular\":true,\"number_fans\":2,\"oc_device\":true,\"oob_interface\":\"re0:mgmt-0, re1:mgmt-0\",\"pic\":{\"0\":\"ge*48\",\"1\":\"qsfp+*4\",\"2\":\"sfp+*4 (uplink)\"},\"sub_required\":\"string\",\"type\":\"switch\"}]"
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.constants.models.listDeviceModels()`

## Usage Context

Returns the complete list of supported Juniper/Mist device hardware models with specifications including radio capabilities, port counts, antenna types, PoE support, and form factors. Use this to validate device model strings, look up hardware capabilities, or build device selection interfaces.

## Gotchas

- The response is a large array covering all AP, switch, and gateway models — filter by `type` (ap/switch/gateway) for targeted queries.
- Model-specific fields (e.g., `has_scanning_radio`, `number_of_ports`) vary by device type and may be absent for some models.
- New models are added periodically; do not hardcode the response.

## Related Endpoints

- [GET_const_mxedge_models.md](GET_const_mxedge_models.md) — Mist Edge hardware models (separate from standard devices)
- [GET_const_otherdevice_models.md](GET_const_otherdevice_models.md) — Supported third-party device models
- [GET_const_ap_channels.md](GET_const_ap_channels.md) — Supported channels per AP model/region
- [../orgs/GET_orgs_org_id_inventory.md](../orgs/GET_orgs_org_id_inventory.md) — Actual device inventory (references model strings)

## MistHelper Notes

Not currently used by MistHelper as a direct constants lookup. Menu **12** (`OrgInventoryExporter.inventory`) and Menu **17** (`OrgInventoryExporter.devices`) export inventory data that includes `model` fields matching values defined here.
