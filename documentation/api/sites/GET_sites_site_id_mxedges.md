# listSiteMxEdges

> listSiteMxEdges

## HTTP

`GET /api/v1/sites/{site_id}/mxedges`

## Description

Get List of Site Mist Edges

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
    "title": "mxedge",
    "required": [
      "model",
      "name"
    ],
    "type": "object",
    "properties": {
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "for_site": {
        "type": "boolean",
        "readOnly": true
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
      "mac": {
        "type": "string",
        "readOnly": true,
        "examples": [
          "0200009fbe65"
        ]
      },
      "magic": {
        "type": "string",
        "readOnly": true,
        "examples": [
          "L-NpT5gi-ADR8WTFd4EiQPY3cP5WdSoD"
        ]
      },
      "model": {
        "type": "string",
        "examples": [
          "ME-100"
        ]
      },
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "mxagent_registered": {
        "type": "boolean",
        "readOnly": true
      },
      "mxcluster_id": {
        "type": "string",
        "description": "MxCluster this MxEdge belongs to",
        "contentEncoding": "uuid",
        "examples": [
          "572586b7-f97b-a22b-526c-8b97a3f609c4"
        ]
      },
      "mxedge_mgmt": {
        "title": "mxedge_mgmt",
        "type": "object",
        "properties": {
          "config_auto_revert": {
            "type": "boolean",
            "default": false
          },
          "fips_enabled": {
            "type": "boolean",
            "default": false
          },
          "mist_password": {
            "type": "string",
            "examples": [
              "MIST_PASSWORD"
            ]
          },
          "oob_ip_type": {
            "type": "string",
            "description": "enum: `dhcp`, `disabled`, `static`"
          },
          "oob_ip_type6": {
            "type": "string",
            "description": "enum: `autoconf`, `dhcp`, `disabled`, `static`"
          },
          "root_password": {
            "type": "string",
            "examples": [
              "ROOT_PASSWORD"
            ]
          }
        }
      },
      "name": {
        "type": "string",
        "examples": [
          "Guest"
        ]
      },
      "note": {
        "type": "string",
        "examples": [
          "note for mxedge"
        ]
      },
      "ntp_servers": {
        "uniqueItems": true,
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": ""
      },
      "oob_ip_config": {
        "type": "object",
        "properties": {
          "autoconf6": {
            "type": "boolean",
            "default": true
          },
          "dhcp6": {
            "type": "boolean",
            "default": true
          },
          "dns": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "IPv4 ignored if `type`!=`static`, IPv6 ignored if `type6`!=`static`",
            "default": [
              "8.8.8.8",
              "8.8.4.4",
              "2001:4860:4860::8888",
              "2001:4860:4860::8844"
            ],
            "examples": [
              [
                "8.8.8.8",
                "4.4.4.4",
                "2001:4860:4860::8888",
                "2001:4860:4860::8844"
              ]
            ]
          },
          "gateway": {
            "type": "string",
            "description": "If `type`=`static`",
            "examples": [
              "10.2.1.254"
            ]
          },
          "gateway6": {
            "type": "string",
            "examples": [
              "2601:1700:43c0:dc0::1"
            ]
          },
          "ip": {
            "type": "string",
            "description": "If `type`=`static`",
            "examples": [
              "10.2.1.2"
            ]
          },
          "ip6": {
            "type": "string",
            "examples": [
              "2601:1700:43c0:dc0:20c:29ff:fea7:93bc"
            ]
          },
          "netmask": {
            "type": "string",
            "description": "If `type`=`static`",
            "examples": [
              "255.255.255.0"
            ]
          },
          "netmask6": {
            "type": "string",
            "examples": [
              "/64"
            ]
          },
          "type": {
            "type": "string",
            "description": "enum: `dhcp`, `static`"
          },
          "type6": {
            "type": "string",
            "description": "enum: `dhcp`, `static`"
          }
        },
        "description": "IPconfiguration of the Mist Edge out-of_band management interface"
      },
      "org_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
        ]
      },
      "proxy": {
        "type": "object",
        "properties": {
          "disabled": {
            "type": "boolean",
            "default": false,
            "examples": [
              true
            ]
          },
          "url": {
            "type": "string",
            "examples": [
              "https://proxy.corp.com:8080/"
            ]
          }
        },
        "description": "Proxy Configuration to talk to Mist"
      },
      "services": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "List of services to run, tunterm only for now"
      },
      "site_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "441a1214-6928-442a-8e92-e1d34b8ec6a6"
        ]
      },
      "tunterm_dhcpd_config": {
        "type": "object",
        "properties": {
          "enabled": {
            "type": "boolean",
            "default": false
          },
          "servers": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of DHCP servers; required if `type`==`relay`"
          },
          "type": {
            "type": "string",
            "description": "enum: `relay`"
          }
        },
        "description": "Global and per-VLAN. Property key is the VLAN ID"
      },
      "tunterm_extra_routes": {
        "type": "object",
        "additionalProperties": {
          "title": "mxedge_tunterm_extra_route",
          "type": "object",
          "properties": {
            "via": {
              "type": "string"
            }
          }
        },
        "description": "Property key is a CIDR"
      },
      "tunterm_igmp_snooping_config": {
        "title": "mxedge_tunterm_igmp_snooping_config",
        "type": "object",
        "properties": {
          "enabled": {
            "type": "boolean",
            "default": false
          },
          "querier": {
            "title": "mxedge_tunterm_igmp_snooping_querier",
            "type": "object",
            "properties": {
              "max_response_time": {
                "type": "integer",
                "description": "Querier's query response interval, in tenths-of-seconds",
                "contentEncoding": "int32",
                "examples": [
                  10
                ]
              },
              "mtu": {
                "type": "integer",
                "description": "The MTU we use (needed when forming large IGMPv3 Reports)",
                "contentEncoding": "int32",
                "examples": [
                  1500
                ]
              },
              "query_interval": {
                "type": "integer",
                "description": "Querier's query interval, in seconds",
                "contentEncoding": "int32",
                "examples": [
                  125
                ]
              },
              "robustness": {
                "maximum": 7.0,
                "minimum": 1.0,
                "type": "integer",
                "description": "Querier's robustness",
                "contentEncoding": "int32"
              },
              "version": {
                "type": "integer",
                "description": "Querier's maximum protocol version",
                "contentEncoding": "int32",
                "examples": [
                  3
                ]
              }
            }
          },
          "vlan_ids": {
            "type": "array",
            "items": {
              "maximum": 4096.0,
              "minimum": 0.0,
              "type": "integer",
              "contentEncoding": "int32"
            },
            "description": "List of vlans on which tunterm performs IGMP snooping"
          }
        }
      },
      "tunterm_ip_config": {
        "type": "object",
        "properties": {
          "gateway": {
            "type": "string",
            "examples": [
              "10.2.1.254"
            ]
          },
          "gateway6": {
            "type": "string",
            "examples": [
              "2001:1010:1010:1010::1"
            ]
          },
          "ip": {
            "type": "string",
            "description": "Untagged VLAN",
            "examples": [
              "10.2.1.1"
            ]
          },
          "ip6": {
            "type": "string",
            "examples": [
              "2001:1010:1010:1010::2"
            ]
          },
          "netmask": {
            "type": "string",
            "examples": [
              "255.255.255.0"
            ]
          },
          "netmask6": {
            "type": "string",
            "examples": [
              "/64"
            ]
          }
        },
        "required": [
          "gateway",
          "ip",
          "netmask"
        ],
        "description": "IPconfiguration of the Mist Tunnel interface"
      },
      "tunterm_monitoring": {
        "type": "array",
        "items": {
          "type": "array",
          "items": {
            "title": "tunterm_monitoring_item",
            "type": "object",
            "properties": {
              "host": {
                "minLength": 1,
                "type": "string",
                "description": "Can be ip, ipv6, hostname",
                "examples": [
                  "10.2.8.15"
                ]
              },
              "port": {
                "type": "integer",
                "description": "When `protocol`==`tcp`",
                "contentEncoding": "int32",
                "examples": [
                  80
                ]
              },
              "protocol": {
                "type": "string",
                "description": "enum: `arp`, `ping`, `tcp`"
              },
              "src_vlan_id": {
                "type": "integer",
                "description": "Optional source for the monitoring check, vlan_id configured in tunterm_other_ip_configs",
                "contentEncoding": "int32",
                "examples": [
                  5
                ]
              },
              "timeout": {
                "type": "integer",
                "contentEncoding": "int32",
                "default": 300,
                "examples": [
                  300
                ]
              }
            }
          }
        }
      },
      "tunterm_multicast_config": {
        "title": "mxedge_tunterm_multicast_config",
        "type": "object",
        "properties": {
          "mdns": {
            "title": "mxedge_tunterm_multicast_mdns",
            "type": "object",
            "properties": {
              "enabled": {
                "type": "boolean"
              },
              "vlan_ids": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              }
            }
          },
          "ssdp": {
            "title": "mxedge_tunterm_multicast_ssdp",
            "type": "object",
            "properties": {
              "enabled": {
                "type": "boolean"
              },
              "vlan_ids": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              }
            }
          }
        }
      },
      "tunterm_other_ip_configs": {
        "type": "object",
        "additionalProperties": {
          "title": "mxedge_tunterm_other_ip_config",
          "required": [
            "ip",
            "netmask"
          ],
          "type": "object",
          "properties": {
            "ip": {
              "type": "string"
            },
            "netmask": {
              "type": "string"
            }
          }
        },
        "description": "IPconfigs by VLAN ID. Property key is the VLAN ID"
      },
      "tunterm_port_config": {
        "type": "object",
        "properties": {
          "downstream_ports": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of ports to be used for downstream (to AP) purpose",
            "examples": [
              [
                "2",
                "3"
              ]
            ]
          },
          "separate_upstream_downstream": {
            "type": "boolean",
            "description": "Whether to separate upstream / downstream ports. default is false where all ports will be used.",
            "default": false
          },
          "upstream_port_vlan_id": {
            "type": "object",
            "description": "Native VLAN id for upstream ports"
          },
          "upstream_ports": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of ports to be used for upstream purpose (to LAN)",
            "examples": [
              [
                "0",
                "1"
              ]
            ]
          }
        },
        "description": "Ethernet port configurations"
      },
      "tunterm_registered": {
        "type": "boolean",
        "readOnly": true
      },
      "tunterm_switch_config": {
        "type": "object",
        "properties": {
          "enabled": {
            "type": "boolean"
          }
        },
        "description": "If custom vlan settings are desired"
      },
      "versions": {
        "type": "object",
        "properties": {
          "mxagent": {
            "type": "string",
            "readOnly": true
          },
          "tunterm": {
            "type": "string",
            "readOnly": true
          }
        },
        "readOnly": true
      }
    },
    "description": "MxEdge"
  },
  "description": "",
  "examples": [
    [
      {
        "cpu_stat": {
          "cpus": {
            "cpu0": {
              "idle": 79,
              "interrupt": 0,
              "system": 4,
              "usage": 20,
              "user": 16
            },
            "cpu1": {
              "idle": 93,
              "interrupt": 0,
              "system": 4,
              "usage": 6,
              "user": 1
            }
          },
          "idle": 87,
          "interrupt": 0,
          "system": 5,
          "usage": 12,
          "user": 7
        },
        "ext_ip": "116.187.144.16",
        "id": "387804a7-3474-85ce-15a2-f9a9684c9c90",
        "ip_stat": {
          "ip": "172.16.5.3",
          "ips": {
            "ens192": "172.16.5.3/24,fe81::20c:29ff:fef8:d18e/64"
          }
        },
        "lag_stat": {
          "lag0": {
            "active_ports": [
              "0",
              "1"
            ]
          }
        },
        "last_seen": 1547437078,
        "magic": "ExNpT5gi-ADR8WTFd4EiQPY3cP5WdSoD",
        "memory_stats": {
          "active": 1061085184,
          "available": 4124860416,
          "buffers": 789495808,
          "cached": 718016512,
          "free": 2818838528,
          "inactive": 458158080,
          "swap_cached": 0,
          "swap_free": 8161062912,
          "swap_total": 8161062912,
          "total": 7947616256,
          "usage": 65
        },
        "model": "ME-S2019",
        "mxagent_registered": false,
        "mxcluster_id": "572586b7-f97b-a22b-526c-8b97a3f609c4",
        "name": "Guest",
        "num_tunnels": 31,
        "port_stat": {
          "eth0": {
            "full_duplex": true,
            "lldp_stats": {
              "mgmt_addr": "122.16.3.11",
              "port_desc": "GigabitEthernet4/0/16",
              "port_id": "\u0005Gi4/0/16",
              "system_desc": "Cisco IOS Software",
              "system_name": "ME-DC2-DIS-SW"
            },
            "rx_bytes": 2056,
            "rx_errors": 0,
            "rx_pkts": 670,
            "speed": 1000,
            "tx_bytes": 2056,
            "tx_pkts": 670,
            "up": true
          },
          "eth1": {
            "up": false
          },
          "module": {
            "up": false
          }
        },
        "status": "connected",
        "tunterm_registered": false,
        "tunterm_stat": {
          "monitoring_failed": false
        },
        "uptime": 884221,
        "version": "0.1.2",
        "virtualization_type": "VirtualizationVMware"
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

`mistapi.api.v1.sites.mxedges.listSiteMxEdges()`

## Usage Context

Lists Mist Edge appliances at a site. Returns edge device status, tunnel counts, and configuration.

## Gotchas

- Mist Edges at site level may be a subset of org-level edges.

## Related Endpoints

- [GET_sites_site_id_mxedges_mxedge_id.md](GET_sites_site_id_mxedges_mxedge_id.md) — Get specific edge
- [POST_sites_site_id_mxedges.md](POST_sites_site_id_mxedges.md) — Create edge

## MistHelper Notes

Not currently used by MistHelper directly. Menu **59** uses `listOrgMxEdges` at org level.
