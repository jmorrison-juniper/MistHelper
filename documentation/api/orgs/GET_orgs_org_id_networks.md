# listOrgNetworks

> listOrgNetworks

## HTTP

`GET /api/v1/orgs/{org_id}/networks`

## Description

Get List of Org Networks

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
    "title": "network",
    "required": [
      "name"
    ],
    "type": "object",
    "properties": {
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "disallow_mist_services": {
        "type": "boolean",
        "description": "Whether to disallow Mist Devices in the network",
        "default": false
      },
      "gateway": {
        "type": "string",
        "examples": [
          "192.168.70.1"
        ]
      },
      "gateway6": {
        "type": "string",
        "examples": [
          "fdad:b0bc:f29e::1"
        ]
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
      "internal_access": {
        "title": "network_internal_access",
        "type": "object",
        "properties": {
          "enabled": {
            "type": "boolean"
          }
        }
      },
      "internet_access": {
        "type": "object",
        "properties": {
          "create_simple_service_policy": {
            "type": "boolean",
            "default": false
          },
          "destination_nat": {
            "type": "object",
            "additionalProperties": {
              "title": "network_internet_access_destination_nat_property",
              "type": "object",
              "properties": {
                "internal_ip": {
                  "type": "string",
                  "description": "The Destination NAT destination IP Address. Must be an IP (i.e. \"192.168.70.30\") or a Variable (i.e. \"{{myvar}}\")",
                  "examples": [
                    "192.168.70.30"
                  ]
                },
                "name": {
                  "type": "string",
                  "examples": [
                    "web server"
                  ]
                },
                "port": {
                  "type": "string",
                  "description": "The Destination NAT destination IP Address. Must be a Port (i.e. \"443\") or a Variable (i.e. \"{{myvar}}\")",
                  "examples": [
                    "443"
                  ]
                },
                "wan_name": {
                  "type": "string",
                  "description": "SRX Only. If not set, we configure the nat policies against all WAN ports for simplicity",
                  "examples": [
                    "wan0"
                  ]
                }
              }
            },
            "description": "Property key can be an External IP (i.e. \"63.16.0.3\"), an External IP:Port (i.e. \"63.16.0.3:443\"), an External Port (i.e. \":443\"), an External CIDR (i.e. \"63.16.0.0/30\"), an External CIDR:Port (i.e. \"63.16.0.0/30:443\") or a Variable (i.e. \"{{myvar}}\"). At least one of the `internal_ip` or `port` must be defined"
          },
          "enabled": {
            "type": "boolean"
          },
          "restricted": {
            "type": "boolean",
            "description": "By default, all access is allowed, to only allow certain traffic, make `restricted`=`true` and define service_policies",
            "default": false
          },
          "static_nat": {
            "type": "object",
            "additionalProperties": {
              "title": "network_internet_access_static_nat_property",
              "type": "object",
              "properties": {
                "internal_ip": {
                  "type": "string",
                  "description": "The Static NAT destination IP Address. Must be an IP Address (i.e. \"192.168.70.3\") or a Variable (i.e. \"{{myvar}}\")",
                  "examples": [
                    "192.168.70.3"
                  ]
                },
                "name": {
                  "type": "string",
                  "examples": [
                    "pos_station-1"
                  ]
                },
                "wan_name": {
                  "type": "string",
                  "description": "SRX Only. If not set, we configure the nat policies against all WAN ports for simplicity. Can be a Variable (i.e. \"{{myvar}}\")",
                  "examples": [
                    "wan0"
                  ]
                }
              }
            },
            "description": "Property key may be an External IP Address (i.e. \"63.16.0.3\"), a CIDR (i.e. \"63.16.0.12/20\") or a Variable (i.e. \"{{myvar}}\")"
          }
        },
        "description": "Whether this network has direct internet access"
      },
      "isolation": {
        "type": "boolean",
        "description": "Whether to allow clients in the network to talk to each other"
      },
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "multicast": {
        "type": "object",
        "properties": {
          "disable_igmp": {
            "type": "boolean",
            "description": "If the network will only be the source of the multicast traffic, IGMP can be disabled",
            "default": false
          },
          "enabled": {
            "type": "boolean",
            "default": false
          },
          "groups": {
            "type": "object",
            "additionalProperties": {
              "title": "network_multicast_group",
              "type": "object",
              "properties": {
                "rp_ip": {
                  "type": "string",
                  "description": "RP (rendezvous point) IP Address"
                }
              }
            },
            "description": "Group address to RP (rendezvous point) mapping. Property Key is the CIDR (example \"225.1.0.3/32\")"
          }
        },
        "description": "Whether to enable multicast support (only PIM-sparse mode is supported)"
      },
      "name": {
        "type": "string"
      },
      "org_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
        ]
      },
      "routed_for_networks": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "For a Network (usually LAN), it can be routable to other networks (e.g. OSPF)"
      },
      "subnet": {
        "type": "string",
        "examples": [
          "192.168.70.0/24"
        ]
      },
      "subnet6": {
        "type": "string",
        "examples": [
          "fdad:b0bc:f29e::/32"
        ]
      },
      "tenants": {
        "type": "object",
        "additionalProperties": {
          "title": "network_tenant",
          "type": "object",
          "properties": {
            "addresses": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": ""
            }
          }
        },
        "description": "Property key must be the user/tenant name (i.e. \"printer-1\") or a Variable (i.e. \"{{myvar}}\")"
      },
      "vlan_id": {
        "type": "object"
      },
      "vpn_access": {
        "type": "object",
        "additionalProperties": {
          "title": "network_vpn_access_config",
          "type": "object",
          "properties": {
            "advertised_subnet": {
              "type": "string",
              "description": "If `routed`==`true`, whether to advertise an aggregated subnet toward HUB this is useful when there are multiple networks on SPOKE's side",
              "examples": [
                "172.16.0.0/24"
              ]
            },
            "allow_ping": {
              "type": "boolean",
              "description": "Whether to allow ping from vpn into this routed network"
            },
            "destination_nat": {
              "type": "object",
              "additionalProperties": {
                "title": "network_vpn_access_destination_nat_property",
                "type": "object",
                "properties": {
                  "internal_ip": {
                    "type": "string",
                    "description": "The Destination NAT destination IP Address. Must be an IP (i.e. \"192.168.70.30\") or a Variable (i.e. \"{{myvar}}\")",
                    "examples": [
                      "192.168.70.30"
                    ]
                  },
                  "name": {
                    "type": "string",
                    "examples": [
                      "web server"
                    ]
                  },
                  "port": {
                    "type": "string",
                    "examples": [
                      "443"
                    ]
                  }
                }
              },
              "description": "Property key can be an External IP (i.e. \"63.16.0.3\"), an External IP:Port (i.e. \"63.16.0.3:443\"), an External Port (i.e. \":443\"), an External CIDR (i.e. \"63.16.0.0/30\"), an External CIDR:Port (i.e. \"63.16.0.0/30:443\") or a Variable (i.e. \"{{myvar}}\"). At least one of the `internal_ip` or `port` must be defined"
            },
            "nat_pool": {
              "type": "string",
              "description": "If `routed`==`false` (usually at Spoke), but some hosts needs to be reachable from Hub, a subnet is required to create and advertise the route to Hub",
              "examples": [
                "172.16.0.0/26"
              ]
            },
            "no_readvertise_to_lan_bgp": {
              "type": "boolean",
              "description": "toward LAN-side BGP peers",
              "default": false
            },
            "no_readvertise_to_lan_ospf": {
              "type": "boolean",
              "description": "toward LAN-side OSPF peers",
              "default": false
            },
            "no_readvertise_to_overlay": {
              "type": "boolean",
              "description": "toward overlay, how HUB should deal with routes it received from Spokes"
            },
            "other_vrfs": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": "By default, the routes are only readvertised toward the same vrf on spoke. To allow it to be leaked to other vrfs"
            },
            "routed": {
              "type": "boolean",
              "description": "Whether this network is routable"
            },
            "source_nat": {
              "type": "object",
              "properties": {
                "external_ip": {
                  "type": "string",
                  "examples": [
                    "172.16.0.8/30"
                  ]
                }
              },
              "description": "If `routed`==`false` (usually at Spoke), but some hosts needs to be reachable from Hub"
            },
            "static_nat": {
              "type": "object",
              "additionalProperties": {
                "title": "network_vpn_access_static_nat_property",
                "type": "object",
                "properties": {
                  "internal_ip": {
                    "type": "string",
                    "description": "The Static NAT destination IP Address. Must be an IP Address (i.e. \"192.168.70.3\") or a Variable (i.e. \"{{myvar}}\")",
                    "examples": [
                      "192.168.70.3"
                    ]
                  },
                  "name": {
                    "type": "string",
                    "examples": [
                      "pos_station-1"
                    ]
                  }
                }
              },
              "description": "Property key may be an External IP Address (i.e. \"63.16.0.3\"), a CIDR (i.e. \"63.16.0.12/20\") or a Variable (i.e. \"{{myvar}}\")"
            },
            "summarized_subnet": {
              "type": "string",
              "description": "toward overlay, how HUB should deal with routes it received from Spokes",
              "examples": [
                "172.16.0.0/16"
              ]
            },
            "summarized_subnet_to_lan_bgp": {
              "type": "string",
              "description": "toward LAN-side BGP peers",
              "examples": [
                "172.16.0.0/16"
              ]
            },
            "summarized_subnet_to_lan_ospf": {
              "type": "string",
              "description": "toward LAN-side OSPF peers",
              "examples": [
                "172.16.0.0/16"
              ]
            }
          }
        },
        "description": "Property key is the VPN name. Whether this network can be accessed from vpn"
      }
    },
    "description": "Networks are usually subnets that have cross-site significance. `networks`in Org Settings will got merged into `networks`in Site Setting. For gateways, they can be used to define Service Routes."
  },
  "description": "",
  "examples": [
    [
      {
        "created_time": 0,
        "disallow_mist_services": false,
        "gateway": "192.168.70.1",
        "hosts": {
          "property1": {
            "external_ips": "172.16.10.32-172.16.10.35",
            "ips": "192.168.70.32-192.168.70.35"
          },
          "property2": {
            "external_ips": "172.16.10.32-172.16.10.35",
            "ips": "192.168.70.32-192.168.70.35"
          }
        },
        "id": "497f6eca-6276-4993-bfeb-53cbbbba6f13",
        "internal_access": {
          "enabled": true
        },
        "internet_access": {
          "create_simple_service_policy": false,
          "destination_nat": {
            "property1": {
              "internal_ip": "192.168.70.30",
              "name": "web server",
              "port": "443"
            },
            "property2": {
              "internal_ip": "192.168.70.30",
              "name": "web server",
              "port": "443"
            }
          },
          "enabled": true,
          "restricted": false,
          "static_nat": {
            "property1": {
              "internal_ip": "192.168.70.3",
              "name": "printer-1"
            },
            "property2": {
              "internal_ip": "192.168.70.3",
              "name": "printer-1"
            }
          }
        },
        "isolation": true,
        "modified_time": 0,
        "name": "string",
        "org_id": "a40f5d1f-d889-42e9-94ea-b9b33585fc6b",
        "subnet": "192.168.70.0/24",
        "tenants": {
          "property1": {
            "addresses": [
              "10.10.10.10"
            ]
          },
          "property2": {
            "addresses": [
              "10.10.10.45"
            ]
          }
        },
        "vlan_id": 10,
        "vpn_access": {
          "property1": {
            "allow_ping": true,
            "destination_nat": {
              "property1": {
                "internal_ip": "192.168.70.5/30",
                "name": "web server",
                "port": "443"
              },
              "property2": {
                "internal_ip": "192.168.70.5/30",
                "name": "web server",
                "port": "443"
              }
            },
            "nat_pool": "172.16.0.0/26",
            "routed": true,
            "source_nat": {
              "external_ip": "172.16.0.8/30"
            },
            "static_nat": {
              "property1": {
                "internal_ip": "192.168.70.3",
                "name": "pos_station-1"
              },
              "property2": {
                "internal_ip": "192.168.70.3",
                "name": "pos_station-1"
              }
            },
            "summarized_subnet": "172.16.0.0/16"
          },
          "property2": {
            "allow_ping": true,
            "destination_nat": {
              "property1": {
                "internal_ip": "192.168.70.5/30",
                "name": "web server",
                "port": "443"
              },
              "property2": {
                "internal_ip": "192.168.70.5/30",
                "name": "web server",
                "port": "443"
              }
            },
            "nat_pool": "172.16.0.0/26",
            "routed": true,
            "source_nat": {
              "external_ip": "172.16.0.8/30"
            },
            "static_nat": {
              "property1": {
                "internal_ip": "192.168.70.3",
                "name": "pos_station-1"
              },
              "property2": {
                "internal_ip": "192.168.70.3",
                "name": "pos_station-1"
              }
            },
            "summarized_subnet": "172.16.0.0/16"
          }
        }
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

`mistapi.api.v1.orgs.networks.listOrgNetworks()`

## Usage Context

Lists all networks (VLANs/subnets) for the organization.

## Gotchas

- Networks are referenced by WLANs, switch templates, and gateway templates.

## Related Endpoints

- [GET_orgs_org_id_networks_network_id.md](GET_orgs_org_id_networks_network_id.md) — Get specific network
- [POST_orgs_org_id_networks.md](POST_orgs_org_id_networks.md) — Create network

## MistHelper Notes

Used by MistHelper via `listOrgNetworks` in Menu 4.
