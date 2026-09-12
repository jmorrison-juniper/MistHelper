# listOrgEvpnTopologies

> listOrgEvpnTopologies

## HTTP

`GET /api/v1/orgs/{org_id}/evpn_topologies`

## Description

Get List of the existing Org EVPN topologies

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
| for_site | string | No |  |  | Filter for org/site level EVPN Toplogies |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "array",
  "items": {
    "title": "evpn_topology_response",
    "type": "object",
    "properties": {
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "evpn_options": {
        "type": "object",
        "properties": {
          "auto_loopback_subnet": {
            "type": "string",
            "description": "Optional, for dhcp_relay, unique loopback IPs are required for ERB or IPClos where we can set option-82 server_id-overrides",
            "default": "172.16.192.0/24"
          },
          "auto_loopback_subnet6": {
            "type": "string",
            "description": "Optional, for dhcp_relay, unique loopback IPs are required for ERB or IPClos where we can set option-82 server_id-overrides",
            "default": "fd33:ab00:2::/64"
          },
          "auto_router_id_subnet": {
            "type": "string",
            "description": "Optional, this generates router_id automatically, if specified, `router_id_prefix` is ignored",
            "default": "172.16.254.0/23"
          },
          "auto_router_id_subnet6": {
            "type": "string",
            "description": "Optional, this generates router_id automatically, if specified, `router_id_prefix` is ignored",
            "examples": [
              "fd31:5700:1::/64"
            ]
          },
          "core_as_border": {
            "type": "boolean",
            "description": "Optional, for ERB or CLOS, you can either use esilag to upstream routers or to also be the virtual-gateway. When `routed_at` != `core`, whether to do virtual-gateway at core as well",
            "default": false
          },
          "enable_inband_ztp": {
            "type": "boolean",
            "description": "if the mangement traffic goes inbnd, during installation, only the border/core switches are connected to the Internet to allow initial configuration to be pushed down and leave the downstream access switches stay in the Factory Default state enabling inband-ztp allows upstream switches to use LLDP to assign IP and gives Internet to downstream switches in that state",
            "default": false
          },
          "overlay": {
            "title": "evpn_options_overlay",
            "type": "object",
            "properties": {
              "as": {
                "maximum": 65535.0,
                "minimum": 1.0,
                "type": "integer",
                "description": "Overlay BGP Local AS Number",
                "contentEncoding": "int32",
                "default": 65000,
                "examples": [
                  65000
                ]
              }
            }
          },
          "per_vlan_vga_v4_mac": {
            "type": "boolean",
            "description": "Only for by Core-Distribution architecture when `evpn_options.routed_at`==`core`. By default, JUNOS uses 00-00-5e-00-01-01 as the virtual-gateway-address's v4_mac. If enabled, 00-00-5e-00-0X-YY will be used (where XX=vlan_id/256, YY=vlan_id%256)",
            "default": false
          },
          "per_vlan_vga_v6_mac": {
            "type": "boolean",
            "description": "Only for by Core-Distribution architecture when `evpn_options.routed_at`==`core`. By default, JUNOS uses 00-00-5e-00-02-01 as the virtual-gateway-address's v6_mac. If enabled, 00-00-5e-00-1X-YY will be used (where XX=vlan_id/256, YY=vlan_id%256)",
            "default": false
          },
          "routed_at": {
            "type": "string",
            "description": "optional, where virtual-gateway should reside. enum: `core`, `distribution`, `edge`"
          },
          "underlay": {
            "title": "evpn_options_underlay",
            "type": "object",
            "properties": {
              "as_base": {
                "maximum": 65535.0,
                "minimum": 1.0,
                "type": "integer",
                "description": "Underlay BGP Base AS Number",
                "contentEncoding": "int32",
                "default": 65001,
                "examples": [
                  65001
                ]
              },
              "routed_id_prefix": {
                "type": "string",
                "examples": [
                  "/24"
                ]
              },
              "subnet": {
                "type": "string",
                "description": "Underlay subnet, by default, `10.255.240.0/20`, or `fd31:5700::/64` for ipv6",
                "examples": [
                  "10.255.240.0/20"
                ]
              },
              "use_ipv6": {
                "type": "boolean",
                "description": "If v6 is desired for underlay",
                "default": false
              }
            }
          },
          "vs_instances": {
            "type": "object",
            "additionalProperties": {
              "title": "evpn_options_vs_instance",
              "type": "object",
              "properties": {
                "networks": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": ""
                }
              }
            },
            "description": "Optional, for EX9200 only to segregate virtual-switches",
            "examples": [
              {
                "guest": {
                  "networks": [
                    "guest"
                  ]
                },
                "iot": {
                  "networks": [
                    "iot-wifi",
                    "iot-lan"
                  ]
                }
              }
            ]
          }
        },
        "description": "EVPN Options"
      },
      "for_site": {
        "type": "boolean"
      },
      "id": {
        "type": "string",
        "description": "Unique ID of the object instance in the Mist Organization",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "53f10664-3ce8-4c27-b382-0ef66432349f"
        ]
      },
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "name": {
        "type": "string",
        "examples": [
          "CC"
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
      "overwrite": {
        "type": "boolean"
      },
      "pod_names": {
        "type": "object",
        "additionalProperties": {
          "type": "string"
        },
        "description": "Property key is the pod number"
      },
      "site_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "441a1214-6928-442a-8e92-e1d34b8ec6a6"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "created_time": 1736421230,
        "evpn_options": {
          "auto_loopback_subnet": "172.16.192.0/24",
          "auto_loopback_subnet6": "fd33:ab00:2::/64",
          "auto_router_id_subnet": "172.16.254.0/23",
          "core_as_border": true,
          "overlay": {
            "as": 65000
          },
          "per_vlan_vga_v4_mac": false,
          "routed_at": "core",
          "underlay": {
            "as_base": 65001,
            "subnet": "10.255.240.0/20",
            "use_ipv6": false
          }
        },
        "for_site": false,
        "id": "764fb173-94f9-447c-8454-def62e5a999f",
        "modified_time": 1736421230,
        "name": "tert",
        "org_id": "3a2627d7-bfbc-45af-b85d-8841581c6d63",
        "pod_names": {
          "1": "Pod 1"
        },
        "site_id": "00000000-0000-0000-0000-000000000000"
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

`mistapi.api.v1.orgs.evpn_topologies.listOrgEvpnTopologies()`

## Usage Context

Lists all EVPN topologies for the organization.

## Gotchas

- Used for campus fabric and data center deployments with VxLAN.

## Related Endpoints

- [GET_orgs_org_id_evpn_topologies_evpn_topology_id.md](GET_orgs_org_id_evpn_topologies_evpn_topology_id.md) — Get specific topology
- [POST_orgs_org_id_evpn_topologies.md](POST_orgs_org_id_evpn_topologies.md) — Create topology

## MistHelper Notes

Not currently used by MistHelper directly.
