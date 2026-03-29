# updateOrgNetworkTemplate

> updateOrgNetworkTemplate

## HTTP

`PUT /api/v1/orgs/{org_id}/networktemplates/{networktemplate_id}`

## Description

Update Org Network Template

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| networktemplate_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "acl_policies": {
      "type": "array",
      "items": {
        "title": "acl_policy",
        "type": "object",
        "properties": {
          "actions": {
            "type": "array",
            "items": {
              "title": "acl_policy_action",
              "required": [
                "dst_tag"
              ],
              "type": "object",
              "properties": {
                "action": {
                  "type": "string",
                  "description": "enum: `allow`, `deny`"
                },
                "dst_tag": {
                  "type": "string",
                  "examples": [
                    "corp"
                  ]
                }
              }
            },
            "description": "ACL Policy Actions:\n  - for GBP-based policy, all src_tags and dst_tags have to be gbp-based\n  - for ACL-based policy, `network` is required in either the source or destination so that we know where to attach the policy to"
          },
          "name": {
            "type": "string",
            "examples": [
              "guest access"
            ]
          },
          "src_tags": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "ACL Policy Source Tags:\n  - for GBP-based policy, all src_tags and dst_tags have to be gbp-based\n  - for ACL-based policy, `network` is required in either the source or destination so that we know where to attach the policy to"
          }
        },
        "description": "ACL Policy:\n  - for GBP-based policy, all src_tags and dst_tags have to be gbp-based\n  - for ACL-based policy, `network` is required in either the source or destination so that we know where to attach the policy to"
      },
      "description": ""
    },
    "acl_tags": {
      "type": "object",
      "additionalProperties": {
        "title": "acl_tag",
        "required": [
          "type"
        ],
        "type": "object",
        "properties": {
          "ether_types": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "ARP / IPv6. Default is `any`",
            "default": [
              "any"
            ]
          },
          "gbp_tag": {
            "type": "integer",
            "description": "Required if\n  - `type`==`dynamic_gbp` (gbp_tag received from RADIUS)\n  - `type`==`gbp_resource`\n  - `type`==`static_gbp` (applying gbp tag against matching conditions)",
            "contentEncoding": "int32"
          },
          "macs": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Required if \n- `type`==`mac`\n- `type`==`static_gbp` if from matching mac"
          },
          "network": {
            "type": "string",
            "description": "If:\n  * `type`==`mac` (optional. default is `any`)\n  * `type`==`subnet` (optional. default is `any`)\n  * `type`==`network`\n  * `type`==`resource` (optional. default is `any`)\n  * `type`==`static_gbp` if from matching network (vlan)"
          },
          "port_usage": {
            "type": "string",
            "description": "Required if `type`==`port_usage`"
          },
          "radius_group": {
            "type": "string",
            "description": "Required if:\n  * `type`==`radius_group`\n  * `type`==`static_gbp`\nif from matching radius_group"
          },
          "specs": {
            "type": "array",
            "items": {
              "title": "acl_tag_spec",
              "type": "object",
              "properties": {
                "port_range": {
                  "type": "string",
                  "description": "Matched dst port, \"0\" means any",
                  "default": "0"
                },
                "protocol": {
                  "type": "string",
                  "description": "`tcp` / `udp` / `icmp` / `icmp6` / `gre` / `any` / `:protocol_number`, `protocol_number` is between 1-254, default is `any` `protocol_number` is between 1-254",
                  "default": "any"
                }
              }
            },
            "description": "If `type`==`resource`, `type`==`radius_group`, `type`==`port_usage` or `type`==`gbp_resource`. Empty means unrestricted, i.e. any"
          },
          "subnets": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "If \n- `type`==`subnet` \n- `type`==`resource` (optional. default is `any`)\n- `type`==`static_gbp` if from matching subnet"
          },
          "type": {
            "type": "string",
            "description": "enum: \n  * `any`: matching anything not identified\n  * `dynamic_gbp`: from the gbp_tag received from RADIUS\n  * `gbp_resource`: can only be used in `dst_tags`\n  * `mac`\n  * `network`\n  * `port_usage`\n  * `radius_group`\n  * `resource`: can only be used in `dst_tags`\n  * `static_gbp`: applying gbp tag against matching conditions\n  * `subnet`'"
          }
        },
        "description": "Resource tags (`type`==`resource` or `type`==`gbp_resource`) can only be used in `dst_tags`"
      },
      "description": "ACL Tags to identify traffic source or destination. Key name is the tag name"
    },
    "additional_config_cmds": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "additional CLI commands to append to the generated Junos config. **Note**: no check is done"
    },
    "bgp_config": {
      "type": "object",
      "additionalProperties": {
        "title": "switch_bgp_config",
        "required": [
          "local_as",
          "type"
        ],
        "type": "object",
        "properties": {
          "auth_key": {
            "type": "string"
          },
          "bfd_minimum_interval": {
            "maximum": 255000.0,
            "minimum": 1.0,
            "type": "integer",
            "description": "Minimum interval in milliseconds for BFD hello packets. A neighbor is considered failed when the device stops receiving replies after the specified interval. Value must be between 1 and 255000.",
            "contentEncoding": "int32"
          },
          "export_policy": {
            "type": "string",
            "description": "Export policy must match one of the policy names defined in the `routing_policies` property."
          },
          "hold_time": {
            "type": "object",
            "description": "Hold time is three times the interval at which keepalive messages are sent. It indicates to the peer the length of time that it should consider the sender valid. Must be 0 or a number in the range 3-65535."
          },
          "import_policy": {
            "type": "string",
            "description": "Import policy must match one of the policy names defined in the `routing_policies` property."
          },
          "local_as": {
            "type": "object",
            "description": "BGP AS, value in range 1-4294967294. Can be a Variable (e.g. `{{bgp_as}}` )"
          },
          "neighbors": {
            "type": "object",
            "additionalProperties": {
              "title": "switch_bgp_config_neighbor",
              "required": [
                "neighbor_as"
              ],
              "type": "object",
              "properties": {
                "export_policy": {
                  "type": "string",
                  "description": "Export policy must match one of the policy names defined in the `routing_policies` property."
                },
                "hold_time": {
                  "type": "object",
                  "description": "Hold time is three times the interval at which keepalive messages are sent. It indicates to the peer the length of time that it should consider the sender valid. Must be 0 or a number in the range 3-65535."
                },
                "import_policy": {
                  "type": "string",
                  "description": "Import policy must match one of the policy names defined in the `routing_policies` property."
                },
                "multihop_ttl": {
                  "maximum": 255.0,
                  "minimum": 1.0,
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "neighbor_as": {
                  "anyOf": [
                    {
                      "type": "string"
                    },
                    {
                      "maximum": 4294967294.0,
                      "minimum": 1.0,
                      "type": "integer",
                      "contentEncoding": "int32"
                    }
                  ],
                  "description": "Autonomous System (AS) number of the BGP neighbor. For internal BGP, this must match `local_as`. For external BGP, this must differ from `local_as`.",
                  "examples": [
                    "65000"
                  ]
                }
              }
            },
            "description": "Property key is the BGP Neighbor IP Address."
          },
          "networks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of network names for BGP configuration. When a network is specified, a BGP group will be added to the VRF that network is part of."
          },
          "type": {
            "type": "string",
            "description": "enum: `external`, `internal`"
          }
        }
      }
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "dhcp_snooping": {
      "title": "dhcp_snooping",
      "type": "object",
      "properties": {
        "all_networks": {
          "type": "boolean"
        },
        "enable_arp_spoof_check": {
          "type": "boolean",
          "description": "Enable for dynamic ARP inspection check"
        },
        "enable_ip_source_guard": {
          "type": "boolean",
          "description": "Enable for check for forging source IP address"
        },
        "enabled": {
          "type": "boolean"
        },
        "networks": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "If `all_networks`==`false`, list of network with DHCP snooping enabled"
        }
      }
    },
    "dns_servers": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Global dns settings. To keep compatibility, dns settings in `ip_config` and `oob_ip_config` will overwrite this setting"
    },
    "dns_suffix": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Global dns settings. To keep compatibility, dns settings in `ip_config` and `oob_ip_config` will overwrite this setting"
    },
    "extra_routes": {
      "type": "object",
      "additionalProperties": {
        "title": "extra_route",
        "type": "object",
        "properties": {
          "discard": {
            "type": "boolean",
            "description": "This takes precedence",
            "default": false
          },
          "metric": {
            "maximum": 2147483647.0,
            "minimum": 0.0,
            "type": [
              "integer",
              "null"
            ],
            "contentEncoding": "int32"
          },
          "next_qualified": {
            "type": "object",
            "additionalProperties": {
              "title": "extra_route_next_qualified_properties",
              "type": "object",
              "properties": {
                "metric": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32"
                },
                "preference": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32"
                }
              }
            },
            "examples": [
              {
                "10.3.1.1": {
                  "metric": null,
                  "preference": 40
                }
              }
            ]
          },
          "no_resolve": {
            "type": "boolean",
            "default": false
          },
          "preference": {
            "maximum": 2147483647.0,
            "minimum": 0.0,
            "type": [
              "integer",
              "null"
            ],
            "contentEncoding": "int32",
            "examples": [
              30
            ]
          },
          "via": {
            "type": "object",
            "description": "Next-hop IP Address. Can be a single IP address or an array of IP addresses for ECMP (Equal-Cost Multi-Path) load balancing across multiple next-hops."
          }
        }
      },
      "description": "Property key is the destination CIDR (e.g. \"10.0.0.0/8\")",
      "examples": [
        {
          "0.0.0.0/0": {
            "via": "192.168.1.10"
          }
        }
      ]
    },
    "extra_routes6": {
      "type": "object",
      "additionalProperties": {
        "title": "extra_route6",
        "type": "object",
        "properties": {
          "discard": {
            "type": "boolean",
            "description": "This takes precedence",
            "default": false
          },
          "metric": {
            "maximum": 2147483647.0,
            "minimum": 0.0,
            "type": [
              "integer",
              "null"
            ],
            "contentEncoding": "int32"
          },
          "next_qualified": {
            "type": "object",
            "additionalProperties": {
              "title": "extra_route6_next_qualified_properties",
              "type": "object",
              "properties": {
                "metric": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32"
                },
                "preference": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32"
                }
              }
            },
            "examples": [
              {
                "2a02:1234:200a::100": {
                  "metric": null,
                  "preference": 40
                }
              }
            ]
          },
          "no_resolve": {
            "type": "boolean",
            "default": false
          },
          "preference": {
            "maximum": 2147483647.0,
            "minimum": 0.0,
            "type": [
              "integer",
              "null"
            ],
            "contentEncoding": "int32",
            "examples": [
              30
            ]
          },
          "via": {
            "type": "object",
            "description": "Next-hop IP Address. Can be a single IP address or an array of IP addresses for ECMP (Equal-Cost Multi-Path) load balancing across multiple next-hops."
          }
        }
      },
      "description": "Property key is the destination CIDR (e.g. \"2a02:1234:420a:10c9::/64\")",
      "examples": [
        {
          "2a02:1234:420a:10c9::/64": {
            "via": "2a02:1234:200a::100"
          }
        }
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
    "import_org_networks": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Org Networks that we'd like to import"
    },
    "mist_nac": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean"
        },
        "network": {
          "type": "string"
        }
      },
      "description": "Enable mist_nac to use RadSec"
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string"
    },
    "networks": {
      "type": "object",
      "additionalProperties": {
        "title": "switch_network",
        "required": [
          "vlan_id"
        ],
        "type": "object",
        "properties": {
          "gateway": {
            "type": "string",
            "description": "Only required for EVPN-VXLAN networks, IPv4 Virtual Gateway"
          },
          "gateway6": {
            "type": "string",
            "description": "Only required for EVPN-VXLAN networks, IPv6 Virtual Gateway"
          },
          "isolation": {
            "type": "boolean",
            "description": "whether to stop clients to talk to each other, default is false (when enabled, a unique isolation_vlan_id is required). NOTE: this features requires uplink device to also a be Juniper device and `inter_switch_link` to be set. See also `inter_isolation_network_link` and `community_vlan_id` in port_usage",
            "default": false
          },
          "isolation_vlan_id": {
            "type": "string",
            "examples": [
              "3070"
            ]
          },
          "subnet": {
            "type": "string",
            "description": "Optional for pure switching, required when L3 / routing features are used"
          },
          "subnet6": {
            "type": "string",
            "description": "Optional for pure switching, required when L3 / routing features are used"
          },
          "vlan_id": {
            "type": "object"
          }
        },
        "description": "A network represents a network segment. It can either represent a VLAN (then usually ties to a L3 subnet), optionally associate it with a subnet which can later be used to create addition routes. Used for ports doing `family ethernet-switching`. It can also be a pure L3-subnet that can then be used against a port that with `family inet`."
      },
      "description": "Property key is network name"
    },
    "ntp_servers": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of NTP servers specific to this device. By default, those in Site Settings will be used"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "ospf_areas": {
      "type": "object",
      "additionalProperties": {
        "title": "ospf_area",
        "type": "object",
        "properties": {
          "include_loopback": {
            "type": "boolean",
            "default": false
          },
          "networks": {
            "type": "object",
            "additionalProperties": {
              "title": "ospf_areas_network",
              "type": "object",
              "properties": {
                "auth_keys": {
                  "type": "object",
                  "additionalProperties": {
                    "type": "string"
                  },
                  "description": "Required if `auth_type`==`md5`. Property key is the key number",
                  "examples": [
                    {
                      "1": "auth-key-1"
                    }
                  ]
                },
                "auth_password": {
                  "type": "string",
                  "description": "Required if `auth_type`==`password`, the password, max length is 8",
                  "examples": [
                    "simple"
                  ]
                },
                "auth_type": {
                  "type": "string",
                  "description": "auth type. enum: `md5`, `none`, `password`"
                },
                "bfd_minimum_interval": {
                  "maximum": 255000.0,
                  "minimum": 1.0,
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    500
                  ]
                },
                "dead_interval": {
                  "maximum": 65535.0,
                  "minimum": 1.0,
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    40
                  ]
                },
                "export_policy": {
                  "type": "string",
                  "examples": [
                    "export_policy"
                  ]
                },
                "hello_interval": {
                  "maximum": 255.0,
                  "minimum": 1.0,
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "import_policy": {
                  "type": "string",
                  "examples": [
                    "import_policy"
                  ]
                },
                "interface_type": {
                  "type": "string",
                  "description": "interface type (nbma = non-broadcast multi-access). enum: `broadcast`, `nbma`, `p2mp`, `p2p`"
                },
                "metric": {
                  "maximum": 65535.0,
                  "minimum": 1.0,
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32",
                  "examples": [
                    10000
                  ]
                },
                "no_readvertise_to_overlay": {
                  "type": "boolean",
                  "description": "By default, we'll re-advertise all learned OSPF routes toward overlay",
                  "default": false
                },
                "passive": {
                  "type": "boolean",
                  "description": "Whether to send OSPF-Hello",
                  "default": false
                }
              },
              "description": "Property key is the network name. Networks to participate in an OSPF area"
            },
            "examples": [
              {
                "corp": {
                  "auth_keys": {
                    "1": "auth-key-1"
                  },
                  "auth_type": "md5",
                  "bfd_minimum_interval": 500,
                  "dead_interval": 40,
                  "hello_interval": 10,
                  "interface_type": "nbma",
                  "metric": 10000
                },
                "guest": {
                  "passive": true
                }
              }
            ]
          },
          "type": {
            "type": "string",
            "description": "OSPF type. enum: `default`, `nssa`, `stub`"
          }
        },
        "description": "Property key is the OSPF Area (Area should be a number (0-255) / IP address)"
      },
      "description": "Junos OSPF areas. Property key is the OSPF Area (Area should be a number (0-255) / IP address)"
    },
    "port_mirroring": {
      "type": "object",
      "additionalProperties": {
        "title": "switch_port_mirroring_property",
        "type": "object",
        "properties": {
          "input_networks_ingress": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "At least one of the `input_port_ids_ingress`, `input_port_ids_egress` or `input_networks_ingress ` should be specified"
          },
          "input_port_ids_egress": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "At least one of the `input_port_ids_ingress`, `input_port_ids_egress` or `input_networks_ingress ` should be specified"
          },
          "input_port_ids_ingress": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "At least one of the `input_port_ids_ingress`, `input_port_ids_egress` or `input_networks_ingress ` should be specified"
          },
          "output_ip_address": {
            "type": "string",
            "description": "Exactly one of the `output_ip_address`, `output_port_id` or `output_network` should be provided",
            "examples": [
              "1.2.3.4"
            ]
          },
          "output_network": {
            "type": "string",
            "description": "Exactly one of the `output_ip_address`, `output_port_id` or `output_network` should be provided",
            "examples": [
              "analyze"
            ]
          },
          "output_port_id": {
            "type": "string",
            "description": "Exactly one of the `output_ip_address`, `output_port_id` or `output_network` should be provided",
            "examples": [
              "ge-0/0/5"
            ]
          }
        }
      },
      "description": "Property key is the port mirroring instance name. `port_mirroring` can be added under device/site settings. It takes interface and ports as input for ingress, interface as input for egress and can take interface and port as output. A maximum 4 mirroring ports is allowed"
    },
    "port_usages": {
      "type": "object",
      "additionalProperties": {
        "title": "switch_port_usage",
        "type": "object",
        "properties": {
          "all_networks": {
            "type": "boolean",
            "description": "Only if `mode`==`trunk`. Whether to trunk all network/vlans",
            "default": false
          },
          "allow_dhcpd": {
            "type": "boolean",
            "description": "Only applies when `mode`!=`dynamic`. Controls whether DHCP server traffic is allowed on ports using this configuration if DHCP snooping is enabled. This is a tri-state setting; `true`: ports become trusted ports allowing DHCP server traffic, `false`: ports become untrusted blocking DHCP server traffic, undefined: use system defaults (access ports default to untrusted, trunk ports default to trusted)."
          },
          "allow_multiple_supplicants": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`",
            "default": false
          },
          "bypass_auth_when_server_down": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic` and `port_auth`==`dot1x`. Bypass auth for known clients if set to true when RADIUS server is down",
            "default": false
          },
          "bypass_auth_when_server_down_for_unknown_client": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic` and `port_auth`=`dot1x`. Bypass auth for all (including unknown clients) if set to true when RADIUS server is down",
            "default": false
          },
          "bypass_auth_when_server_down_for_voip": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic` and `port_auth`==`dot1x`. Bypass auth for VOIP if set to true when RADIUS server is down",
            "default": false
          },
          "community_vlan_id": {
            "type": "integer",
            "description": "Only if `mode`!=`dynamic`. To be used together with `isolation` under networks. Signaling that this port connects to the networks isolated but wired clients belong to the same community can talk to each other",
            "contentEncoding": "int32"
          },
          "description": {
            "type": "string",
            "description": "Only if `mode`!=`dynamic`"
          },
          "disable_autoneg": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`. If speed and duplex are specified, whether to disable autonegotiation",
            "default": false
          },
          "disabled": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`. Whether the port is disabled",
            "default": false
          },
          "duplex": {
            "type": "string",
            "description": "Only if `mode`!=`dynamic`. Link connection mode. enum: `auto`, `full`, `half`"
          },
          "dynamic_vlan_networks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Only if `mode`!=`dynamic` and `port_auth`==`dot1x`, if dynamic vlan is used, specify the possible networks/vlans RADIUS can return",
            "examples": [
              [
                "corp",
                "user"
              ]
            ]
          },
          "enable_mac_auth": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic` and `port_auth`==`dot1x`. Whether to enable MAC Auth",
            "default": false
          },
          "enable_qos": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`",
            "default": false
          },
          "guest_network": {
            "type": [
              "string",
              "null"
            ],
            "description": "Only if `mode`!=`dynamic` and `port_auth`==`dot1x`. Which network to put the device into if the device cannot do dot1x. default is null (i.e. not allowed)"
          },
          "inter_isolation_network_link": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`. `inter_isolation_network_link` is used together with `isolation` under networks, signaling that this port connects to isolated networks",
            "default": false
          },
          "inter_switch_link": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`. `inter_switch_link` is used together with `isolation` under networks. NOTE: `inter_switch_link` works only between Juniper devices. This has to be applied to both ports connected together",
            "default": false
          },
          "mac_auth_only": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic` and `enable_mac_auth`==`true`"
          },
          "mac_auth_preferred": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic` + `enable_mac_auth`==`true` + `mac_auth_only`==`false`, dot1x will be given priority then mac_auth. Enable this to prefer mac_auth over dot1x."
          },
          "mac_auth_protocol": {
            "type": "string",
            "description": "Only if `mode`!=`dynamic` and `enable_mac_auth` ==`true`. This type is ignored if mist_nac is enabled. enum: `eap-md5`, `eap-peap`, `pap`"
          },
          "mac_limit": {
            "type": "object",
            "description": "Only if `mode`!=`dynamic`, max number of mac addresses, default is 0 for unlimited, otherwise range is 1 to 16383 (upper bound constrained by platform)"
          },
          "mode": {
            "type": "string",
            "description": "`mode`==`dynamic` must only be used if the port usage name is `dynamic`. enum: `access`, `dynamic`, `inet`, `trunk`"
          },
          "mtu": {
            "type": "object",
            "description": "Only if `mode`!=`dynamic` media maximum transmission unit (MTU) is the largest data unit that can be forwarded without fragmentation. The default value is 1514."
          },
          "networks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Only if `mode`==`trunk`, the list of network/vlans"
          },
          "persist_mac": {
            "type": "boolean",
            "description": "Only if `mode`==`access` and `port_auth`!=`dot1x`. Whether the port should retain dynamically learned MAC addresses",
            "default": false
          },
          "poe_disabled": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`. Whether PoE capabilities are disabled for a port",
            "default": false
          },
          "poe_priority": {
            "type": "string",
            "description": "PoE priority. enum: `low`, `high`"
          },
          "port_auth": {
            "type": "object",
            "description": "Only if `mode`!=`dynamic`. If dot1x is desired, set to dot1x. enum: `dot1x`"
          },
          "port_network": {
            "type": "string",
            "description": "Only if `mode`!=`dynamic`. Native network/vlan for untagged traffic"
          },
          "reauth_interval": {
            "type": "object",
            "description": "Only if `mode`!=`dynamic` and `port_auth`=`dot1x` reauthentication interval range (min: 10, max: 65535, default: 3600)"
          },
          "reset_default_when": {
            "type": "string",
            "description": "Only if `mode`==`dynamic` Control when the DPC port should be changed to the default port usage. enum: `link_down`, `none` (let the DPC port keep at the current port usage)"
          },
          "rules": {
            "type": "array",
            "items": {
              "title": "switch_port_usage_dynamic_rule",
              "required": [
                "src"
              ],
              "type": "object",
              "properties": {
                "description": {
                  "type": "string",
                  "description": "Optional description of the rule"
                },
                "equals": {
                  "type": "string"
                },
                "equals_any": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": "Use `equals_any` to match any item in a list"
                },
                "expression": {
                  "type": "string",
                  "description": "\"[0:3]\":\"abcdef\" -> \"abc\"\n\"split(.)[1]\": \"a.b.c\" -> \"b\"\n\"split(-)[1][0:3]: \"a1234-b5678-c90\" -> \"b56\""
                },
                "src": {
                  "type": "string",
                  "description": "enum: `link_peermac`, `lldp_chassis_id`, `lldp_hardware_revision`, `lldp_manufacturer_name`, `lldp_oui`, `lldp_serial_number`, `lldp_system_description`, `lldp_system_name`, `radius_dynamicfilter`, `radius_usermac`, `radius_username`"
                },
                "usage": {
                  "type": "string",
                  "description": "`port_usage` name"
                }
              }
            },
            "description": "Only if `mode`==`dynamic`"
          },
          "server_fail_network": {
            "type": [
              "string",
              "null"
            ],
            "description": "Only if `mode`!=`dynamic` and `port_auth`==`dot1x`. Sets server fail fallback vlan"
          },
          "server_reject_network": {
            "type": [
              "string",
              "null"
            ],
            "description": "Only if `mode`!=`dynamic` and `port_auth`==`dot1x`. When radius server reject / fails"
          },
          "speed": {
            "type": "string",
            "description": "Only if `mode`!=`dynamic`, Port speed, default is auto to automatically negotiate speed enum: `100m`, `10m`, `1g`, `2.5g`, `5g`, `10g`, `25g`, `40g`, `100g`,`auto`"
          },
          "storm_control": {
            "type": "object",
            "properties": {
              "disable_port": {
                "type": "boolean",
                "description": "Whether to disable the port when storm control is triggered",
                "default": false
              },
              "no_broadcast": {
                "type": "boolean",
                "description": "Whether to disable storm control on broadcast traffic",
                "default": false
              },
              "no_multicast": {
                "type": "boolean",
                "description": "Whether to disable storm control on multicast traffic",
                "default": false
              },
              "no_registered_multicast": {
                "type": "boolean",
                "description": "Whether to disable storm control on registered multicast traffic",
                "default": false
              },
              "no_unknown_unicast": {
                "type": "boolean",
                "description": "Whether to disable storm control on unknown unicast traffic",
                "default": false
              },
              "percentage": {
                "maximum": 100.0,
                "minimum": 0.0,
                "type": "integer",
                "description": "Bandwidth-percentage, configures the storm control level as a percentage of the available bandwidth",
                "contentEncoding": "int32",
                "default": 80
              }
            },
            "description": "Switch storm control. Only if `mode`!=`dynamic`"
          },
          "stp_disable": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic` and `stp_required`==`false`. Drop bridge protocol data units (BPDUs ) that enter any interface or a specified interface",
            "default": false
          },
          "stp_edge": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`. When enabled, the port is not expected to receive BPDU frames",
            "default": false
          },
          "stp_no_root_port": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`",
            "default": false
          },
          "stp_p2p": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`",
            "default": false
          },
          "stp_required": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`. Whether to remain in block state if no BPDU is received",
            "default": false
          },
          "ui_evpntopo_id": {
            "type": "string",
            "description": "Optional for Campus Fabric Core-Distribution ESI-LAG profile. Helper used by the UI to select this port profile as the ESI-Lag between Distribution and Access switches",
            "contentEncoding": "uuid"
          },
          "use_vstp": {
            "type": "boolean",
            "description": "If this is connected to a vstp network",
            "default": false
          },
          "voip_network": {
            "type": [
              "string",
              "null"
            ],
            "description": "Only if `mode`!=`dynamic`. Network/vlan for voip traffic, must also set port_network. to authenticate device, set port_auth"
          }
        },
        "description": "Junos port usages"
      },
      "description": "Property key is the port usage name. Defines the profiles of port configuration configured on the switch"
    },
    "radius_config": {
      "type": "object",
      "properties": {
        "acct_immediate_update": {
          "type": "boolean"
        },
        "acct_interim_interval": {
          "maximum": 65535.0,
          "minimum": 0.0,
          "type": "integer",
          "description": "How frequently should interim accounting be reported, 60-65535. default is 0 (use one specified in Access-Accept request from RADIUS Server). Very frequent messages can affect the performance of the radius server, 600 and up is recommended when enabled",
          "contentEncoding": "int32",
          "default": 0
        },
        "acct_servers": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "title": "radius_acct_server",
            "required": [
              "host",
              "secret"
            ],
            "type": "object",
            "properties": {
              "host": {
                "type": "string",
                "description": "IP/ hostname of RADIUS server",
                "examples": [
                  "1.2.3.4"
                ]
              },
              "keywrap_enabled": {
                "type": "boolean"
              },
              "keywrap_format": {
                "type": "string",
                "description": "enum: `ascii`, `hex`"
              },
              "keywrap_kek": {
                "type": "string",
                "examples": [
                  "1122334455"
                ]
              },
              "keywrap_mack": {
                "type": "string",
                "examples": [
                  "1122334455"
                ]
              },
              "port": {
                "type": "object",
                "description": "Radius Auth Port, value from 1 to 65535, default is 1813"
              },
              "secret": {
                "type": "string",
                "description": "Secret of RADIUS server",
                "examples": [
                  "testing123"
                ]
              }
            }
          },
          "description": ""
        },
        "auth_server_selection": {
          "type": "string",
          "description": "enum: `ordered`, `unordered`"
        },
        "auth_servers": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "title": "radius_auth_server",
            "required": [
              "host",
              "secret"
            ],
            "type": "object",
            "properties": {
              "host": {
                "type": "string",
                "description": "IP/ hostname of RADIUS server",
                "examples": [
                  "1.2.3.4"
                ]
              },
              "keywrap_enabled": {
                "type": "boolean"
              },
              "keywrap_format": {
                "type": "string",
                "description": "enum: `ascii`, `hex`"
              },
              "keywrap_kek": {
                "type": "string",
                "examples": [
                  "1122334455"
                ]
              },
              "keywrap_mack": {
                "type": "string",
                "examples": [
                  "1122334455"
                ]
              },
              "port": {
                "type": "object",
                "description": "Radius Auth Port, value from 1 to 65535, default is 1812"
              },
              "require_message_authenticator": {
                "type": "boolean",
                "description": "Whether to require Message-Authenticator in requests",
                "default": false
              },
              "secret": {
                "type": "string",
                "description": "Secret of RADIUS server",
                "examples": [
                  "testing123"
                ]
              }
            },
            "description": "Authentication Server"
          },
          "description": ""
        },
        "auth_servers_retries": {
          "type": "integer",
          "description": "Radius auth session retries",
          "contentEncoding": "int32",
          "default": 3
        },
        "auth_servers_timeout": {
          "type": "integer",
          "description": "Radius auth session timeout",
          "contentEncoding": "int32",
          "default": 5
        },
        "coa_enabled": {
          "type": "boolean",
          "default": false
        },
        "coa_port": {
          "type": "object",
          "description": "Radius CoA Port, value from 1 to 65535, default is 3799"
        },
        "fast_dot1x_timers": {
          "type": "boolean",
          "default": false
        },
        "network": {
          "type": "string",
          "description": "Use `network`or `source_ip`. Which network the RADIUS server resides, if there's static IP for this network, we'd use it as source-ip"
        },
        "source_ip": {
          "type": "string",
          "description": "Use `network`or `source_ip`"
        }
      },
      "description": "Junos Radius config"
    },
    "remote_syslog": {
      "title": "remote_syslog",
      "type": "object",
      "properties": {
        "archive": {
          "title": "remote_syslog_archive",
          "type": "object",
          "properties": {
            "files": {
              "type": "object"
            },
            "size": {
              "type": "string",
              "examples": [
                "5m"
              ]
            }
          }
        },
        "cacerts": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "",
          "examples": [
            [
              "-----BEGIN CERTIFICATE-----\\nMIIFZjCCA06gAwIBAgIIP61/1qm/uDowDQYJKoZIhvcNAQELBQE\\n-----END CERTIFICATE-----",
              "-----BEGIN CERTIFICATE-----\\nBhMCRVMxFDASBgNVBAoMC1N0YXJ0Q29tIENBMSwwKgYDVn-----END CERTIFICATE-----"
            ]
          ]
        },
        "console": {
          "title": "remote_syslog_console",
          "type": "object",
          "properties": {
            "contents": {
              "type": "array",
              "items": {
                "title": "remote_syslog_content",
                "type": "object",
                "properties": {
                  "facility": {
                    "type": "string",
                    "description": "enum: `any`, `authorization`, `change-log`, `config`, `conflict-log`, `daemon`, `dfc`, `external`, `firewall`, `ftp`, `interactive-commands`, `kernel`, `ntp`, `pfe`, `security`, `user`"
                  },
                  "severity": {
                    "type": "string",
                    "description": "enum: `alert`, `any`, `critical`, `emergency`, `error`, `info`, `notice`, `warning`"
                  }
                }
              },
              "description": ""
            }
          }
        },
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "files": {
          "type": "array",
          "items": {
            "title": "remote_syslog_file_config",
            "type": "object",
            "properties": {
              "archive": {
                "title": "remote_syslog_archive",
                "type": "object",
                "properties": {
                  "files": {
                    "type": "object"
                  },
                  "size": {
                    "type": "string",
                    "examples": [
                      "5m"
                    ]
                  }
                }
              },
              "contents": {
                "type": "array",
                "items": {
                  "title": "remote_syslog_content",
                  "type": "object",
                  "properties": {
                    "facility": {
                      "type": "string",
                      "description": "enum: `any`, `authorization`, `change-log`, `config`, `conflict-log`, `daemon`, `dfc`, `external`, `firewall`, `ftp`, `interactive-commands`, `kernel`, `ntp`, `pfe`, `security`, `user`"
                    },
                    "severity": {
                      "type": "string",
                      "description": "enum: `alert`, `any`, `critical`, `emergency`, `error`, `info`, `notice`, `warning`"
                    }
                  }
                },
                "description": ""
              },
              "enable_tls": {
                "type": "boolean",
                "description": "Only if `protocol`==`tcp`"
              },
              "explicit_priority": {
                "type": "boolean"
              },
              "file": {
                "type": "string",
                "examples": [
                  "file-name"
                ]
              },
              "match": {
                "type": "string",
                "examples": [
                  "!alarm|ntp|errors.crc_error[chan]"
                ]
              },
              "structured_data": {
                "type": "boolean"
              }
            }
          },
          "description": ""
        },
        "network": {
          "type": "string",
          "description": "If source_address is configured, will use the vlan firstly otherwise use source_ip",
          "examples": [
            "default"
          ]
        },
        "send_to_all_servers": {
          "type": "boolean",
          "default": false
        },
        "servers": {
          "type": "array",
          "items": {
            "title": "remote_syslog_server",
            "type": "object",
            "properties": {
              "contents": {
                "type": "array",
                "items": {
                  "title": "remote_syslog_content",
                  "type": "object",
                  "properties": {
                    "facility": {
                      "type": "string",
                      "description": "enum: `any`, `authorization`, `change-log`, `config`, `conflict-log`, `daemon`, `dfc`, `external`, `firewall`, `ftp`, `interactive-commands`, `kernel`, `ntp`, `pfe`, `security`, `user`"
                    },
                    "severity": {
                      "type": "string",
                      "description": "enum: `alert`, `any`, `critical`, `emergency`, `error`, `info`, `notice`, `warning`"
                    }
                  }
                },
                "description": ""
              },
              "explicit_priority": {
                "type": "boolean"
              },
              "facility": {
                "type": "string",
                "description": "enum: `any`, `authorization`, `change-log`, `config`, `conflict-log`, `daemon`, `dfc`, `external`, `firewall`, `ftp`, `interactive-commands`, `kernel`, `ntp`, `pfe`, `security`, `user`"
              },
              "host": {
                "type": "string",
                "examples": [
                  "syslogd.internal"
                ]
              },
              "match": {
                "type": "string",
                "examples": [
                  "!alarm|ntp|errors.crc_error[chan]"
                ]
              },
              "port": {
                "type": "object",
                "description": "Syslog Service Port, value from 1 to 65535"
              },
              "protocol": {
                "type": "string",
                "description": "enum: `tcp`, `udp`"
              },
              "routing_instance": {
                "type": "string",
                "examples": [
                  "routing-instance-name"
                ]
              },
              "server_name": {
                "type": "string",
                "description": "Name of the server",
                "examples": [
                  "syslogd.internal"
                ]
              },
              "severity": {
                "type": "string",
                "description": "enum: `alert`, `any`, `critical`, `emergency`, `error`, `info`, `notice`, `warning`"
              },
              "source_address": {
                "type": "string",
                "description": "If source_address is configured, will use the vlan firstly otherwise use source_ip"
              },
              "structured_data": {
                "type": "boolean"
              },
              "tag": {
                "type": "string"
              }
            }
          },
          "description": "",
          "examples": [
            [
              {
                "facility": "config",
                "host": "syslogd.internal",
                "port": 514,
                "protocol": "udp",
                "severity": "info",
                "tag": ""
              }
            ]
          ]
        },
        "time_format": {
          "type": "string",
          "description": "enum: `millisecond`, `year`, `year millisecond`"
        },
        "users": {
          "type": "array",
          "items": {
            "title": "remote_syslog_user",
            "type": "object",
            "properties": {
              "contents": {
                "type": "array",
                "items": {
                  "title": "remote_syslog_content",
                  "type": "object",
                  "properties": {
                    "facility": {
                      "type": "string",
                      "description": "enum: `any`, `authorization`, `change-log`, `config`, `conflict-log`, `daemon`, `dfc`, `external`, `firewall`, `ftp`, `interactive-commands`, `kernel`, `ntp`, `pfe`, `security`, `user`"
                    },
                    "severity": {
                      "type": "string",
                      "description": "enum: `alert`, `any`, `critical`, `emergency`, `error`, `info`, `notice`, `warning`"
                    }
                  }
                },
                "description": ""
              },
              "match": {
                "type": "string",
                "examples": [
                  "\"!alarm|ntp|errors.crc_error[chan]\""
                ]
              },
              "user": {
                "type": "string",
                "examples": [
                  "*"
                ]
              }
            }
          },
          "description": ""
        }
      }
    },
    "remove_existing_configs": {
      "type": "boolean",
      "description": "By default, only the configuration generated by Mist is cleaned up during the configuration process. If `true`, all the existing configuration will be removed.",
      "default": false
    },
    "routing_policies": {
      "type": "object",
      "additionalProperties": {
        "title": "sw_routing_policy",
        "type": "object",
        "properties": {
          "terms": {
            "minItems": 1,
            "uniqueItems": true,
            "type": "array",
            "items": {
              "title": "sw_routing_policy_term",
              "required": [
                "name"
              ],
              "type": "object",
              "properties": {
                "actions": {
                  "type": "object",
                  "properties": {
                    "accept": {
                      "type": "boolean"
                    },
                    "community": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "When used as export policy, optional"
                    },
                    "local_preference": {
                      "type": "object",
                      "description": "Optional, for an import policy, local_preference can be changed, value in range 1-4294967294. Can be a Variable (e.g. `{{bgp_as}}`)"
                    },
                    "prepend_as_path": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "When used as export policy, optional. By default, the local AS will be prepended, to change it. Can be a Variable (e.g. `{{as_path}}`)"
                    }
                  },
                  "description": "When used as import policy"
                },
                "matching": {
                  "type": "object",
                  "properties": {
                    "as_path": {
                      "type": "array",
                      "items": {
                        "anyOf": [
                          {
                            "type": "string"
                          },
                          {
                            "maximum": 4294967294.0,
                            "minimum": 1.0,
                            "type": "integer",
                            "contentEncoding": "int32"
                          }
                        ],
                        "description": "BGP AS, value in range 1-4294967294. Can be a Variable (e.g. `{{bgp_as}}` )",
                        "examples": [
                          "65000"
                        ]
                      },
                      "description": ""
                    },
                    "community": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": ""
                    },
                    "prefix": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "zero or more criteria/filter can be specified to match the term, all criteria have to be met"
                    },
                    "protocol": {
                      "type": "array",
                      "items": {
                        "title": "sw_routing_policy_term_matching_protocol_enum",
                        "enum": [
                          "bgp",
                          "direct",
                          "evpn",
                          "ospf",
                          "static"
                        ],
                        "type": "string",
                        "description": "enum: `bgp`, `direct`, `evpn`, `ospf`, `static`"
                      },
                      "description": ""
                    }
                  },
                  "description": "zero or more criteria/filter can be specified to match the term, all criteria have to be met"
                },
                "name": {
                  "type": "string"
                }
              }
            },
            "description": "at least criteria/filter must be specified to match the term, all criteria have to be met"
          }
        }
      },
      "description": "Property key is the routing policy name"
    },
    "snmp_config": {
      "title": "snmp_config",
      "type": "object",
      "properties": {
        "client_list": {
          "type": "array",
          "items": {
            "title": "snmp_config_client_list",
            "type": "object",
            "properties": {
              "client_list_name": {
                "type": "string",
                "examples": [
                  "clist-1"
                ]
              },
              "clients": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              }
            }
          },
          "description": ""
        },
        "contact": {
          "type": "string",
          "examples": [
            "cns@juniper.net"
          ]
        },
        "description": {
          "type": "string",
          "examples": [
            "Juniper QFX Series Switch - 1K_5LA"
          ]
        },
        "enabled": {
          "type": "boolean",
          "default": true
        },
        "engine_id": {
          "maxLength": 27,
          "type": "string"
        },
        "engine_id_type": {
          "type": "string",
          "description": "enum: `local`, `use_mac_address`"
        },
        "location": {
          "type": "string",
          "examples": [
            "Las Vegas, NV"
          ]
        },
        "name": {
          "type": "string",
          "examples": [
            "TGH-1K-QFX10K"
          ]
        },
        "network": {
          "type": "string",
          "default": "default"
        },
        "trap_groups": {
          "type": "array",
          "items": {
            "title": "snmp_config_trap_group",
            "type": "object",
            "properties": {
              "categories": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "group_name": {
                "type": "string",
                "description": "Categories list can refer to https://www.juniper.net/documentation/software/topics/task/configuration/snmp_trap-groups-configuring-junos-nm.html",
                "examples": [
                  "profiler"
                ]
              },
              "targets": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "version": {
                "type": "string",
                "description": "enum: `all`, `v1`, `v2`"
              }
            }
          },
          "description": ""
        },
        "v2c_config": {
          "type": "array",
          "items": {
            "title": "snmp_config_v2c_config",
            "type": "object",
            "properties": {
              "authorization": {
                "type": "string",
                "examples": [
                  "read-only"
                ]
              },
              "client_list_name": {
                "type": "string",
                "description": "Client_list_name here should refer to client_list above",
                "examples": [
                  "clist-1"
                ]
              },
              "community_name": {
                "type": "string",
                "examples": [
                  "abc123"
                ]
              },
              "view": {
                "type": "string",
                "description": "View name here should be defined in views above",
                "examples": [
                  "all"
                ]
              }
            }
          },
          "description": ""
        },
        "v3_config": {
          "title": "snmpv3_config",
          "type": "object",
          "properties": {
            "notify": {
              "type": "array",
              "items": {
                "title": "snmpv3_config_notify_items",
                "type": "object",
                "properties": {
                  "name": {
                    "type": "string"
                  },
                  "tag": {
                    "type": "string"
                  },
                  "type": {
                    "type": "string",
                    "description": "enum: `inform`, `trap`"
                  }
                }
              },
              "description": ""
            },
            "notify_filter": {
              "type": "array",
              "items": {
                "title": "snmpv3_config_notify_filter_item",
                "type": "object",
                "properties": {
                  "contents": {
                    "type": "array",
                    "items": {
                      "title": "snmpv3_config_notify_filter_item_content",
                      "type": "object",
                      "properties": {
                        "include": {
                          "type": "boolean"
                        },
                        "oid": {
                          "type": "string",
                          "examples": [
                            "1.3.6.1.4.1"
                          ]
                        }
                      }
                    },
                    "description": ""
                  },
                  "profile_name": {
                    "type": "string"
                  }
                }
              },
              "description": ""
            },
            "target_address": {
              "type": "array",
              "items": {
                "title": "snmpv3_config_target_address_item",
                "type": "object",
                "properties": {
                  "address": {
                    "type": "string",
                    "examples": [
                      "10.11.0.2"
                    ]
                  },
                  "address_mask": {
                    "type": "string",
                    "examples": [
                      "255.255.255.0"
                    ]
                  },
                  "port": {
                    "type": [
                      "string",
                      "null"
                    ],
                    "default": "161"
                  },
                  "tag_list": {
                    "type": "string",
                    "description": "Refer to notify tag, can be multiple with blank"
                  },
                  "target_address_name": {
                    "type": "string",
                    "examples": [
                      "target_address_name"
                    ]
                  },
                  "target_parameters": {
                    "type": "string",
                    "description": "Refer to notify target parameters name"
                  }
                }
              },
              "description": ""
            },
            "target_parameters": {
              "type": "array",
              "items": {
                "title": "snmpv3_config_target_param",
                "type": "object",
                "properties": {
                  "message_processing_model": {
                    "type": "string",
                    "description": "enum: `v1`, `v2c`, `v3`"
                  },
                  "name": {
                    "type": "string"
                  },
                  "notify_filter": {
                    "type": "string",
                    "description": "Refer to profile-name in notify_filter"
                  },
                  "security_level": {
                    "type": "string",
                    "description": "enum: `authentication`, `none`, `privacy`"
                  },
                  "security_model": {
                    "type": "string",
                    "description": "enum: `usm`, `v1`, `v2c`"
                  },
                  "security_name": {
                    "type": "string",
                    "description": "Refer to security_name in usm",
                    "examples": [
                      "m01620"
                    ]
                  }
                }
              },
              "description": ""
            },
            "usm": {
              "type": "array",
              "items": {
                "title": "snmp_usm",
                "type": "object",
                "properties": {
                  "engine_type": {
                    "type": "string",
                    "description": "enum: `local_engine`, `remote_engine`"
                  },
                  "remote_engine_id": {
                    "type": "string",
                    "description": "Required only if `engine_type`==`remote_engine`",
                    "examples": [
                      "00:00:00:0b:00:00:70:10:6f:08:b6:3f"
                    ]
                  },
                  "users": {
                    "type": "array",
                    "items": {
                      "title": "snmp_usm_user",
                      "type": "object",
                      "properties": {
                        "authentication_password": {
                          "minLength": 7,
                          "type": "string",
                          "description": "Not required if `authentication_type`==`authentication-none`. Include alphabetic, numeric, and special characters, but it cannot include control characters."
                        },
                        "authentication_type": {
                          "type": "string",
                          "description": "sha224, sha256, sha384, sha512 are supported in 21.1 and newer release. enum: `authentication-md5`, `authentication-none`, `authentication-sha`, `authentication-sha224`, `authentication-sha256`, `authentication-sha384`, `authentication-sha512`"
                        },
                        "encryption_password": {
                          "minLength": 8,
                          "type": "string",
                          "description": "Not required if `encryption_type`==`privacy-none`. Include alphabetic, numeric, and special characters, but it cannot include control characters"
                        },
                        "encryption_type": {
                          "type": "string",
                          "description": "enum: `privacy-3des`, `privacy-aes128`, `privacy-des`, `privacy-none`"
                        },
                        "name": {
                          "type": "string"
                        }
                      }
                    },
                    "description": ""
                  }
                }
              },
              "description": ""
            },
            "vacm": {
              "title": "snmp_vacm",
              "type": "object",
              "properties": {
                "access": {
                  "type": "array",
                  "items": {
                    "title": "snmp_vacm_access_item",
                    "type": "object",
                    "properties": {
                      "group_name": {
                        "type": "string"
                      },
                      "prefix_list": {
                        "type": "array",
                        "items": {
                          "title": "snmp_vacm_access_item_prefix_list_item",
                          "type": "object",
                          "properties": {
                            "context_prefix": {
                              "type": "string",
                              "description": "Only required if `type`==`context_prefix`",
                              "examples": [
                                "iil"
                              ]
                            },
                            "notify_view": {
                              "type": "string",
                              "description": "Refer to view name",
                              "examples": [
                                "all"
                              ]
                            },
                            "read_view": {
                              "type": "string",
                              "description": "Refer to view name",
                              "examples": [
                                "all"
                              ]
                            },
                            "security_level": {
                              "type": "string",
                              "description": "enum: `authentication`, `none`, `privacy`"
                            },
                            "security_model": {
                              "type": "string",
                              "description": "enum: `any`, `usm`, `v1`, `v2c`"
                            },
                            "type": {
                              "type": "string",
                              "description": "enum: `context_prefix`, `default_context_prefix`"
                            },
                            "write_view": {
                              "type": "string",
                              "description": "Refer to view name",
                              "examples": [
                                "all"
                              ]
                            }
                          }
                        },
                        "description": ""
                      }
                    }
                  },
                  "description": ""
                },
                "security_to_group": {
                  "title": "snmp_vacm_security_to_group",
                  "type": "object",
                  "properties": {
                    "content": {
                      "type": "array",
                      "items": {
                        "title": "snmp_vacm_security_to_group_content_item",
                        "type": "object",
                        "properties": {
                          "group": {
                            "type": "string",
                            "description": "Refer to group_name under access"
                          },
                          "security_name": {
                            "type": "string"
                          }
                        }
                      },
                      "description": ""
                    },
                    "security_model": {
                      "type": "string",
                      "description": "enum: `usm`, `v1`, `v2c`"
                    }
                  }
                }
              }
            }
          }
        },
        "views": {
          "type": "array",
          "items": {
            "title": "snmp_config_view",
            "type": "object",
            "properties": {
              "include": {
                "type": "boolean",
                "description": "If the root oid configured is included"
              },
              "oid": {
                "type": "string",
                "examples": [
                  "1.3.6.1"
                ]
              },
              "view_name": {
                "type": "string",
                "examples": [
                  "all"
                ]
              }
            }
          },
          "description": ""
        }
      }
    },
    "switch_matching": {
      "type": "object",
      "properties": {
        "enable": {
          "type": "boolean"
        },
        "rules": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "title": "switch_matching_rule",
            "type": "object",
            "properties": {
              "additional_config_cmds": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "additional CLI commands to append to the generated Junos config. **Note**: no check is done"
              },
              "default_port_usage": {
                "type": "string",
                "description": "Port usage to assign to switch ports without any port usage assigned. Default: `default` to preserve default behavior",
                "default": "default"
              },
              "ip_config": {
                "type": "object",
                "properties": {
                  "network": {
                    "type": "string",
                    "description": "VLAN Name for the management interface"
                  },
                  "type": {
                    "type": "string",
                    "description": "enum: `dhcp`, `static`"
                  }
                },
                "description": "In-Band Management interface configuration"
              },
              "name": {
                "maxLength": 32,
                "minLength": 1,
                "type": "string",
                "description": "Rule name. WARNING: the name `default` is reserved and can only be used for the last rule in the list"
              },
              "oob_ip_config": {
                "type": "object",
                "properties": {
                  "type": {
                    "type": "string",
                    "description": "enum: `dhcp`, `static`"
                  },
                  "use_mgmt_vrf": {
                    "type": "boolean",
                    "description": "If supported on the platform. If enabled, DNS will be using this routing-instance, too",
                    "default": false
                  },
                  "use_mgmt_vrf_for_host_out": {
                    "type": "boolean",
                    "description": "For host-out traffic (NTP/TACPLUS/RADIUS/SYSLOG/SNMP), if alternative source network/ip is desired",
                    "default": false
                  }
                },
                "description": "Out-of-Band Management interface configuration"
              },
              "port_config": {
                "type": "object",
                "additionalProperties": {
                  "title": "junos_port_config",
                  "required": [
                    "usage"
                  ],
                  "type": "object",
                  "properties": {
                    "ae_disable_lacp": {
                      "type": "boolean",
                      "description": "To disable LACP support for the AE interface"
                    },
                    "ae_idx": {
                      "type": "integer",
                      "description": "Users could force to use the designated AE name",
                      "contentEncoding": "int32"
                    },
                    "ae_lacp_slow": {
                      "type": "boolean",
                      "description": "To use fast timeout"
                    },
                    "aggregated": {
                      "type": "boolean",
                      "default": false
                    },
                    "critical": {
                      "type": "boolean",
                      "description": "To generate port up/down alarm",
                      "default": false
                    },
                    "description": {
                      "type": "string"
                    },
                    "disable_autoneg": {
                      "type": "boolean",
                      "description": "If `speed` and `duplex` are specified, whether to disable autonegotiation",
                      "default": false
                    },
                    "duplex": {
                      "type": "string",
                      "description": "enum: `auto`, `full`, `half`"
                    },
                    "dynamic_usage": {
                      "type": [
                        "string",
                        "null"
                      ],
                      "description": "Enable dynamic usage for this port. Set to `dynamic` to enable."
                    },
                    "esilag": {
                      "type": "boolean"
                    },
                    "mtu": {
                      "type": "integer",
                      "description": "Media maximum transmission unit (MTU) is the largest data unit that can be forwarded without fragmentation",
                      "contentEncoding": "int32",
                      "default": 1514
                    },
                    "networks": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "List of network names. Required if `usage`==`inet`"
                    },
                    "no_local_overwrite": {
                      "type": "boolean",
                      "description": "Prevent helpdesk to override the port config",
                      "default": true
                    },
                    "poe_disabled": {
                      "type": "boolean",
                      "default": false
                    },
                    "port_network": {
                      "type": "string",
                      "description": "Required if `usage`==`vlan_tunnel`. Q-in-Q tunneling using All-in-one bundling. This also enables standard L2PT for interfaces that are not encapsulation tunnel interfaces and uses MAC rewrite operation. [View more information](https://www.juniper.net/documentation/us/en/software/junos/multicast-l2/topics/topic-map/q-in-q.html#id-understanding-qinq-tunneling-and-vlan-translation)"
                    },
                    "speed": {
                      "type": "string",
                      "description": "enum: `100m`, `10m`, `1g`, `2.5g`, `5g`, `10g`, `25g`, `40g`, `100g`,`auto`"
                    },
                    "usage": {
                      "type": "string",
                      "description": "Port usage name. For Q-in-Q, use `vlan_tunnel`. If EVPN is used, use `evpn_uplink`or `evpn_downlink`"
                    }
                  },
                  "description": "Switch port config"
                },
                "description": "Property key is the port name or range (e.g. \"ge-0/0/0-10\")"
              },
              "port_mirroring": {
                "type": "object",
                "additionalProperties": {
                  "title": "switch_port_mirroring_property",
                  "type": "object",
                  "properties": {
                    "input_networks_ingress": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "At least one of the `input_port_ids_ingress`, `input_port_ids_egress` or `input_networks_ingress ` should be specified"
                    },
                    "input_port_ids_egress": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "At least one of the `input_port_ids_ingress`, `input_port_ids_egress` or `input_networks_ingress ` should be specified"
                    },
                    "input_port_ids_ingress": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "At least one of the `input_port_ids_ingress`, `input_port_ids_egress` or `input_networks_ingress ` should be specified"
                    },
                    "output_ip_address": {
                      "type": "string",
                      "description": "Exactly one of the `output_ip_address`, `output_port_id` or `output_network` should be provided",
                      "examples": [
                        "1.2.3.4"
                      ]
                    },
                    "output_network": {
                      "type": "string",
                      "description": "Exactly one of the `output_ip_address`, `output_port_id` or `output_network` should be provided",
                      "examples": [
                        "analyze"
                      ]
                    },
                    "output_port_id": {
                      "type": "string",
                      "description": "Exactly one of the `output_ip_address`, `output_port_id` or `output_network` should be provided",
                      "examples": [
                        "ge-0/0/5"
                      ]
                    }
                  }
                },
                "description": "Property key is the port mirroring instance name. `port_mirroring` can be added under device/site settings. It takes interface and ports as input for ingress, interface as input for egress and can take interface and port as output. A maximum 4 mirroring ports is allowed"
              },
              "stp_config": {
                "title": "switch_stp_config",
                "type": "object",
                "properties": {
                  "bridge_priority": {
                    "type": "string",
                    "description": "Switch STP priority. Range [0, 4k, 8k.. 60k] in steps of 4k. Bridge priority applies to both VSTP and RSTP.",
                    "default": "32k",
                    "examples": [
                      "40k"
                    ]
                  }
                }
              },
              "switch_mgmt": {
                "type": "object",
                "properties": {
                  "ap_affinity_threshold": {
                    "type": "integer",
                    "description": "AP_affinity_threshold ap_affinity_threshold can be added as a field under site/setting. By default, this value is set to 12. If the field is set in both site/setting and org/setting, the value from site/setting will be used.",
                    "contentEncoding": "int32",
                    "default": 10
                  },
                  "cli_banner": {
                    "type": "string",
                    "description": "Set Banners for switches. Allows markup formatting",
                    "examples": [
                      "\\t\\tWELCOME!"
                    ]
                  },
                  "cli_idle_timeout": {
                    "maximum": 60.0,
                    "minimum": 1.0,
                    "type": "integer",
                    "description": "Sets timeout for switches",
                    "contentEncoding": "int32"
                  },
                  "config_revert_timer": {
                    "maximum": 30.0,
                    "minimum": 1.0,
                    "type": "integer",
                    "description": "Rollback timer for commit confirmed",
                    "contentEncoding": "int32",
                    "default": 10
                  },
                  "dhcp_option_fqdn": {
                    "type": "boolean",
                    "description": "Enable to provide the FQDN with DHCP option 81",
                    "default": false
                  },
                  "disable_oob_down_alarm": {
                    "type": "boolean"
                  },
                  "fips_enabled": {
                    "type": "boolean",
                    "default": false
                  },
                  "local_accounts": {
                    "type": "object",
                    "additionalProperties": {
                      "title": "config_switch_local_accounts_user",
                      "type": "object",
                      "properties": {
                        "password": {
                          "type": "string",
                          "examples": [
                            "Juniper123"
                          ]
                        },
                        "role": {
                          "type": "string",
                          "description": "enum: `admin`, `helpdesk`, `none`, `read`"
                        }
                      }
                    },
                    "description": "Property key is the user name. For Local user authentication"
                  },
                  "mxedge_proxy_host": {
                    "type": "string",
                    "description": "IP Address or FQDN of the Mist Edge used to proxy the switch management traffic to the Mist Cloud"
                  },
                  "mxedge_proxy_port": {
                    "type": "object",
                    "description": "Mist Edge port used to proxy the switch management traffic to the Mist Cloud. Value in range 1-65535"
                  },
                  "protect_re": {
                    "type": "object",
                    "properties": {
                      "allowed_services": {
                        "type": "array",
                        "items": {
                          "title": "protect_re_allowed_service",
                          "enum": [
                            "icmp",
                            "ssh"
                          ],
                          "type": "string",
                          "description": "enum: `icmp`, `ssh`"
                        },
                        "description": "Optionally, services we'll allow",
                        "examples": [
                          [
                            "icmp",
                            "ssh"
                          ]
                        ]
                      },
                      "custom": {
                        "type": "array",
                        "items": {
                          "title": "protect_re_custom",
                          "type": "object",
                          "properties": {
                            "port_range": {
                              "type": "string",
                              "description": "Matched dst port, \"0\" means any",
                              "default": "0",
                              "examples": [
                                "80,1035-1040"
                              ]
                            },
                            "protocol": {
                              "type": "string",
                              "description": "enum: `any`, `icmp`, `tcp`, `udp`"
                            },
                            "subnets": {
                              "type": "array",
                              "items": {
                                "type": "string"
                              },
                              "description": ""
                            }
                          },
                          "description": "Custom acls"
                        },
                        "description": ""
                      },
                      "enabled": {
                        "type": "boolean",
                        "description": "When enabled, all traffic that is not essential to our operation will be dropped\ne.g. ntp / dns / traffic to mist will be allowed by default\n     if dhcpd is enabled, we'll make sure it works",
                        "default": false
                      },
                      "hit_count": {
                        "type": "boolean",
                        "description": "Whether to enable hit count for Protect_RE policy",
                        "default": false
                      },
                      "trusted_hosts": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "description": "host/subnets we'll allow traffic to/from"
                      }
                    },
                    "description": "Restrict inbound-traffic to host\nwhen enabled, all traffic that is not essential to our operation will be dropped \ne.g. ntp / dns / traffic to mist will be allowed by default, if dhcpd is enabled, we'll make sure it works"
                  },
                  "radius": {
                    "type": "object",
                    "properties": {
                      "enabled": {
                        "type": "boolean"
                      },
                      "radius_config": {
                        "type": "object",
                        "properties": {
                          "acct_immediate_update": {
                            "type": "boolean"
                          },
                          "acct_interim_interval": {
                            "maximum": 65535.0,
                            "minimum": 0.0,
                            "type": "integer",
                            "description": "How frequently should interim accounting be reported, 60-65535. default is 0 (use one specified in Access-Accept request from RADIUS Server). Very frequent messages can affect the performance of the radius server, 600 and up is recommended when enabled",
                            "contentEncoding": "int32",
                            "default": 0
                          },
                          "acct_servers": {
                            "uniqueItems": true,
                            "type": "array",
                            "items": {
                              "title": "radius_acct_server",
                              "required": [
                                "host",
                                "secret"
                              ],
                              "type": "object",
                              "properties": {
                                "host": {
                                  "type": "string",
                                  "description": "IP/ hostname of RADIUS server",
                                  "examples": [
                                    "1.2.3.4"
                                  ]
                                },
                                "keywrap_enabled": {
                                  "type": "boolean"
                                },
                                "keywrap_format": {
                                  "type": "string",
                                  "description": "enum: `ascii`, `hex`"
                                },
                                "keywrap_kek": {
                                  "type": "string",
                                  "examples": [
                                    "1122334455"
                                  ]
                                },
                                "keywrap_mack": {
                                  "type": "string",
                                  "examples": [
                                    "1122334455"
                                  ]
                                },
                                "port": {
                                  "type": "object",
                                  "description": "Radius Auth Port, value from 1 to 65535, default is 1813"
                                },
                                "secret": {
                                  "type": "string",
                                  "description": "Secret of RADIUS server",
                                  "examples": [
                                    "testing123"
                                  ]
                                }
                              }
                            },
                            "description": ""
                          },
                          "auth_server_selection": {
                            "type": "string",
                            "description": "enum: `ordered`, `unordered`"
                          },
                          "auth_servers": {
                            "uniqueItems": true,
                            "type": "array",
                            "items": {
                              "title": "radius_auth_server",
                              "required": [
                                "host",
                                "secret"
                              ],
                              "type": "object",
                              "properties": {
                                "host": {
                                  "type": "string",
                                  "description": "IP/ hostname of RADIUS server",
                                  "examples": [
                                    "1.2.3.4"
                                  ]
                                },
                                "keywrap_enabled": {
                                  "type": "boolean"
                                },
                                "keywrap_format": {
                                  "type": "string",
                                  "description": "enum: `ascii`, `hex`"
                                },
                                "keywrap_kek": {
                                  "type": "string",
                                  "examples": [
                                    "1122334455"
                                  ]
                                },
                                "keywrap_mack": {
                                  "type": "string",
                                  "examples": [
                                    "1122334455"
                                  ]
                                },
                                "port": {
                                  "type": "object",
                                  "description": "Radius Auth Port, value from 1 to 65535, default is 1812"
                                },
                                "require_message_authenticator": {
                                  "type": "boolean",
                                  "description": "Whether to require Message-Authenticator in requests",
                                  "default": false
                                },
                                "secret": {
                                  "type": "string",
                                  "description": "Secret of RADIUS server",
                                  "examples": [
                                    "testing123"
                                  ]
                                }
                              },
                              "description": "Authentication Server"
                            },
                            "description": ""
                          },
                          "auth_servers_retries": {
                            "type": "integer",
                            "description": "Radius auth session retries",
                            "contentEncoding": "int32",
                            "default": 3
                          },
                          "auth_servers_timeout": {
                            "type": "integer",
                            "description": "Radius auth session timeout",
                            "contentEncoding": "int32",
                            "default": 5
                          },
                          "coa_enabled": {
                            "type": "boolean",
                            "default": false
                          },
                          "coa_port": {
                            "type": "object",
                            "description": "Radius CoA Port, value from 1 to 65535, default is 3799"
                          },
                          "fast_dot1x_timers": {
                            "type": "boolean",
                            "default": false
                          },
                          "network": {
                            "type": "string",
                            "description": "Use `network`or `source_ip`. Which network the RADIUS server resides, if there's static IP for this network, we'd use it as source-ip"
                          },
                          "source_ip": {
                            "type": "string",
                            "description": "Use `network`or `source_ip`"
                          }
                        },
                        "description": "Junos Radius config"
                      },
                      "use_different_radius": {
                        "type": "string"
                      }
                    },
                    "description": "By default, `radius_config` will be used. if a different one has to be used set `use_different_radius"
                  },
                  "remove_existing_configs": {
                    "type": "boolean",
                    "description": "By default, only the configuration generated by Mist is cleaned up during the configuration process. If `true`, all the existing configuration will be removed.",
                    "default": false
                  },
                  "root_password": {
                    "type": "string"
                  },
                  "tacacs": {
                    "title": "tacacs",
                    "type": "object",
                    "properties": {
                      "acct_servers": {
                        "type": "array",
                        "items": {
                          "title": "tacacs_acct_server",
                          "type": "object",
                          "properties": {
                            "host": {
                              "type": "string"
                            },
                            "port": {
                              "type": "string"
                            },
                            "secret": {
                              "type": "string"
                            },
                            "timeout": {
                              "type": "integer",
                              "contentEncoding": "int32",
                              "default": 10
                            }
                          }
                        },
                        "description": ""
                      },
                      "default_role": {
                        "type": "string",
                        "description": "enum: `admin`, `helpdesk`, `none`, `read`"
                      },
                      "enabled": {
                        "type": "boolean"
                      },
                      "network": {
                        "type": "string",
                        "description": "Which network the TACACS server resides"
                      },
                      "tacplus_servers": {
                        "type": "array",
                        "items": {
                          "title": "tacacs_auth_server",
                          "type": "object",
                          "properties": {
                            "host": {
                              "type": "string"
                            },
                            "port": {
                              "type": "string"
                            },
                            "secret": {
                              "type": "string"
                            },
                            "timeout": {
                              "type": "integer",
                              "contentEncoding": "int32",
                              "default": 10
                            }
                          }
                        },
                        "description": ""
                      }
                    }
                  },
                  "use_mxedge_proxy": {
                    "type": "boolean",
                    "description": "To use mxedge as proxy"
                  }
                },
                "description": "Switch settings"
              }
            },
            "additionalProperties": {
              "type": "string"
            },
            "description": "Property key defines the type of matching, value is the string to match. e.g:\n  * `match_name[0:3]`: switch name must match the first 3 letters of the property value\n  * `match_name[2:6]`: switch name must match the property value from the 2nd to the 6th letter\n  * `match_model[0-8]`: switch model must match the first 8 letters of the property value\n  * `match_role`: switch role must match the property value",
            "examples": [
              {
                "match_model": "EX4300",
                "match_name[0:3]": "abc"
              }
            ]
          },
          "description": ""
        }
      },
      "description": "Defines custom switch configuration based on different criteria"
    },
    "switch_mgmt": {
      "type": "object",
      "properties": {
        "ap_affinity_threshold": {
          "type": "integer",
          "description": "AP_affinity_threshold ap_affinity_threshold can be added as a field under site/setting. By default, this value is set to 12. If the field is set in both site/setting and org/setting, the value from site/setting will be used.",
          "contentEncoding": "int32",
          "default": 10
        },
        "cli_banner": {
          "type": "string",
          "description": "Set Banners for switches. Allows markup formatting",
          "examples": [
            "\\t\\tWELCOME!"
          ]
        },
        "cli_idle_timeout": {
          "maximum": 60.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "Sets timeout for switches",
          "contentEncoding": "int32"
        },
        "config_revert_timer": {
          "maximum": 30.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "Rollback timer for commit confirmed",
          "contentEncoding": "int32",
          "default": 10
        },
        "dhcp_option_fqdn": {
          "type": "boolean",
          "description": "Enable to provide the FQDN with DHCP option 81",
          "default": false
        },
        "disable_oob_down_alarm": {
          "type": "boolean"
        },
        "fips_enabled": {
          "type": "boolean",
          "default": false
        },
        "local_accounts": {
          "type": "object",
          "additionalProperties": {
            "title": "config_switch_local_accounts_user",
            "type": "object",
            "properties": {
              "password": {
                "type": "string",
                "examples": [
                  "Juniper123"
                ]
              },
              "role": {
                "type": "string",
                "description": "enum: `admin`, `helpdesk`, `none`, `read`"
              }
            }
          },
          "description": "Property key is the user name. For Local user authentication"
        },
        "mxedge_proxy_host": {
          "type": "string",
          "description": "IP Address or FQDN of the Mist Edge used to proxy the switch management traffic to the Mist Cloud"
        },
        "mxedge_proxy_port": {
          "type": "object",
          "description": "Mist Edge port used to proxy the switch management traffic to the Mist Cloud. Value in range 1-65535"
        },
        "protect_re": {
          "type": "object",
          "properties": {
            "allowed_services": {
              "type": "array",
              "items": {
                "title": "protect_re_allowed_service",
                "enum": [
                  "icmp",
                  "ssh"
                ],
                "type": "string",
                "description": "enum: `icmp`, `ssh`"
              },
              "description": "Optionally, services we'll allow",
              "examples": [
                [
                  "icmp",
                  "ssh"
                ]
              ]
            },
            "custom": {
              "type": "array",
              "items": {
                "title": "protect_re_custom",
                "type": "object",
                "properties": {
                  "port_range": {
                    "type": "string",
                    "description": "Matched dst port, \"0\" means any",
                    "default": "0",
                    "examples": [
                      "80,1035-1040"
                    ]
                  },
                  "protocol": {
                    "type": "string",
                    "description": "enum: `any`, `icmp`, `tcp`, `udp`"
                  },
                  "subnets": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": ""
                  }
                },
                "description": "Custom acls"
              },
              "description": ""
            },
            "enabled": {
              "type": "boolean",
              "description": "When enabled, all traffic that is not essential to our operation will be dropped\ne.g. ntp / dns / traffic to mist will be allowed by default\n     if dhcpd is enabled, we'll make sure it works",
              "default": false
            },
            "hit_count": {
              "type": "boolean",
              "description": "Whether to enable hit count for Protect_RE policy",
              "default": false
            },
            "trusted_hosts": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": "host/subnets we'll allow traffic to/from"
            }
          },
          "description": "Restrict inbound-traffic to host\nwhen enabled, all traffic that is not essential to our operation will be dropped \ne.g. ntp / dns / traffic to mist will be allowed by default, if dhcpd is enabled, we'll make sure it works"
        },
        "radius": {
          "type": "object",
          "properties": {
            "enabled": {
              "type": "boolean"
            },
            "radius_config": {
              "type": "object",
              "properties": {
                "acct_immediate_update": {
                  "type": "boolean"
                },
                "acct_interim_interval": {
                  "maximum": 65535.0,
                  "minimum": 0.0,
                  "type": "integer",
                  "description": "How frequently should interim accounting be reported, 60-65535. default is 0 (use one specified in Access-Accept request from RADIUS Server). Very frequent messages can affect the performance of the radius server, 600 and up is recommended when enabled",
                  "contentEncoding": "int32",
                  "default": 0
                },
                "acct_servers": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "title": "radius_acct_server",
                    "required": [
                      "host",
                      "secret"
                    ],
                    "type": "object",
                    "properties": {
                      "host": {
                        "type": "string",
                        "description": "IP/ hostname of RADIUS server",
                        "examples": [
                          "1.2.3.4"
                        ]
                      },
                      "keywrap_enabled": {
                        "type": "boolean"
                      },
                      "keywrap_format": {
                        "type": "string",
                        "description": "enum: `ascii`, `hex`"
                      },
                      "keywrap_kek": {
                        "type": "string",
                        "examples": [
                          "1122334455"
                        ]
                      },
                      "keywrap_mack": {
                        "type": "string",
                        "examples": [
                          "1122334455"
                        ]
                      },
                      "port": {
                        "type": "object",
                        "description": "Radius Auth Port, value from 1 to 65535, default is 1813"
                      },
                      "secret": {
                        "type": "string",
                        "description": "Secret of RADIUS server",
                        "examples": [
                          "testing123"
                        ]
                      }
                    }
                  },
                  "description": ""
                },
                "auth_server_selection": {
                  "type": "string",
                  "description": "enum: `ordered`, `unordered`"
                },
                "auth_servers": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "title": "radius_auth_server",
                    "required": [
                      "host",
                      "secret"
                    ],
                    "type": "object",
                    "properties": {
                      "host": {
                        "type": "string",
                        "description": "IP/ hostname of RADIUS server",
                        "examples": [
                          "1.2.3.4"
                        ]
                      },
                      "keywrap_enabled": {
                        "type": "boolean"
                      },
                      "keywrap_format": {
                        "type": "string",
                        "description": "enum: `ascii`, `hex`"
                      },
                      "keywrap_kek": {
                        "type": "string",
                        "examples": [
                          "1122334455"
                        ]
                      },
                      "keywrap_mack": {
                        "type": "string",
                        "examples": [
                          "1122334455"
                        ]
                      },
                      "port": {
                        "type": "object",
                        "description": "Radius Auth Port, value from 1 to 65535, default is 1812"
                      },
                      "require_message_authenticator": {
                        "type": "boolean",
                        "description": "Whether to require Message-Authenticator in requests",
                        "default": false
                      },
                      "secret": {
                        "type": "string",
                        "description": "Secret of RADIUS server",
                        "examples": [
                          "testing123"
                        ]
                      }
                    },
                    "description": "Authentication Server"
                  },
                  "description": ""
                },
                "auth_servers_retries": {
                  "type": "integer",
                  "description": "Radius auth session retries",
                  "contentEncoding": "int32",
                  "default": 3
                },
                "auth_servers_timeout": {
                  "type": "integer",
                  "description": "Radius auth session timeout",
                  "contentEncoding": "int32",
                  "default": 5
                },
                "coa_enabled": {
                  "type": "boolean",
                  "default": false
                },
                "coa_port": {
                  "type": "object",
                  "description": "Radius CoA Port, value from 1 to 65535, default is 3799"
                },
                "fast_dot1x_timers": {
                  "type": "boolean",
                  "default": false
                },
                "network": {
                  "type": "string",
                  "description": "Use `network`or `source_ip`. Which network the RADIUS server resides, if there's static IP for this network, we'd use it as source-ip"
                },
                "source_ip": {
                  "type": "string",
                  "description": "Use `network`or `source_ip`"
                }
              },
              "description": "Junos Radius config"
            },
            "use_different_radius": {
              "type": "string"
            }
          },
          "description": "By default, `radius_config` will be used. if a different one has to be used set `use_different_radius"
        },
        "remove_existing_configs": {
          "type": "boolean",
          "description": "By default, only the configuration generated by Mist is cleaned up during the configuration process. If `true`, all the existing configuration will be removed.",
          "default": false
        },
        "root_password": {
          "type": "string"
        },
        "tacacs": {
          "title": "tacacs",
          "type": "object",
          "properties": {
            "acct_servers": {
              "type": "array",
              "items": {
                "title": "tacacs_acct_server",
                "type": "object",
                "properties": {
                  "host": {
                    "type": "string"
                  },
                  "port": {
                    "type": "string"
                  },
                  "secret": {
                    "type": "string"
                  },
                  "timeout": {
                    "type": "integer",
                    "contentEncoding": "int32",
                    "default": 10
                  }
                }
              },
              "description": ""
            },
            "default_role": {
              "type": "string",
              "description": "enum: `admin`, `helpdesk`, `none`, `read`"
            },
            "enabled": {
              "type": "boolean"
            },
            "network": {
              "type": "string",
              "description": "Which network the TACACS server resides"
            },
            "tacplus_servers": {
              "type": "array",
              "items": {
                "title": "tacacs_auth_server",
                "type": "object",
                "properties": {
                  "host": {
                    "type": "string"
                  },
                  "port": {
                    "type": "string"
                  },
                  "secret": {
                    "type": "string"
                  },
                  "timeout": {
                    "type": "integer",
                    "contentEncoding": "int32",
                    "default": 10
                  }
                }
              },
              "description": ""
            }
          }
        },
        "use_mxedge_proxy": {
          "type": "boolean",
          "description": "To use mxedge as proxy"
        }
      },
      "description": "Switch settings"
    },
    "vrf_config": {
      "title": "vrf_config",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "Whether to enable VRF (when supported on the device)"
        }
      }
    },
    "vrf_instances": {
      "type": "object",
      "additionalProperties": {
        "title": "switch_vrf_instance",
        "type": "object",
        "properties": {
          "aggregate_routes": {
            "type": "object",
            "additionalProperties": {
              "title": "aggregate_route",
              "type": "object",
              "properties": {
                "discard": {
                  "type": "boolean",
                  "default": false
                },
                "metric": {
                  "maximum": 4294967295.0,
                  "minimum": 0.0,
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32"
                },
                "preference": {
                  "maximum": 4294967295.0,
                  "minimum": 0.0,
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32"
                }
              }
            },
            "description": "Property key is the destination subnet (e.g. \"172.16.3.0/24\")",
            "examples": [
              {
                "172.16.3.0/24": {
                  "discard": false,
                  "metric": null,
                  "preference": 30
                }
              }
            ]
          },
          "aggregate_routes6": {
            "type": "object",
            "additionalProperties": {
              "title": "aggregate_route",
              "type": "object",
              "properties": {
                "discard": {
                  "type": "boolean",
                  "default": false
                },
                "metric": {
                  "maximum": 4294967295.0,
                  "minimum": 0.0,
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32"
                },
                "preference": {
                  "maximum": 4294967295.0,
                  "minimum": 0.0,
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32"
                }
              }
            },
            "description": "Property key is the destination subnet (e.g. \"2a02:1234:420a:10c9::/64\")",
            "examples": [
              {
                "2a02:1234:420a:10c9::/64": {
                  "discard": false,
                  "metric": null,
                  "preference": 30
                }
              }
            ]
          },
          "evpn_auto_loopback_subnet": {
            "type": "string",
            "examples": [
              "100.101.0.0/24"
            ]
          },
          "evpn_auto_loopback_subnet6": {
            "type": "string"
          },
          "extra_routes": {
            "type": "object",
            "additionalProperties": {
              "title": "vrf_extra_route",
              "type": "object",
              "properties": {
                "via": {
                  "type": "string",
                  "description": "Next-hop address"
                }
              }
            },
            "description": "Property key is the destination CIDR (e.g. \"10.0.0.0/8\")",
            "examples": [
              {
                "0.0.0.0/0": {
                  "via": "192.168.1.10"
                }
              }
            ]
          },
          "extra_routes6": {
            "type": "object",
            "additionalProperties": {
              "title": "vrf_extra_route",
              "type": "object",
              "properties": {
                "via": {
                  "type": "string",
                  "description": "Next-hop address"
                }
              }
            },
            "description": "Property key is the destination CIDR (e.g. \"2a02:1234:420a:10c9::/64\")",
            "examples": [
              {
                "2a02:1234:420a:10c9::/64": {
                  "via": "2a02:1234:200a::100"
                }
              }
            ]
          },
          "networks": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          }
        },
        "examples": [
          {
            "extra_routes": {
              "0.0.0.0/0": {
                "via": "192.168.31.1"
              }
            },
            "networks": [
              "guest"
            ]
          }
        ]
      },
      "description": "Property key is the network name",
      "examples": [
        {
          "guest": {
            "extra_routes": {
              "0.0.0.0/0": {
                "via": "192.168.31.1"
              }
            },
            "networks": [
              "guest"
            ]
          }
        }
      ]
    }
  },
  "description": "Request Body"
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "acl_policies": {
      "type": "array",
      "items": {
        "title": "acl_policy",
        "type": "object",
        "properties": {
          "actions": {
            "type": "array",
            "items": {
              "title": "acl_policy_action",
              "required": [
                "dst_tag"
              ],
              "type": "object",
              "properties": {
                "action": {
                  "type": "string",
                  "description": "enum: `allow`, `deny`"
                },
                "dst_tag": {
                  "type": "string",
                  "examples": [
                    "corp"
                  ]
                }
              }
            },
            "description": "ACL Policy Actions:\n  - for GBP-based policy, all src_tags and dst_tags have to be gbp-based\n  - for ACL-based policy, `network` is required in either the source or destination so that we know where to attach the policy to"
          },
          "name": {
            "type": "string",
            "examples": [
              "guest access"
            ]
          },
          "src_tags": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "ACL Policy Source Tags:\n  - for GBP-based policy, all src_tags and dst_tags have to be gbp-based\n  - for ACL-based policy, `network` is required in either the source or destination so that we know where to attach the policy to"
          }
        },
        "description": "ACL Policy:\n  - for GBP-based policy, all src_tags and dst_tags have to be gbp-based\n  - for ACL-based policy, `network` is required in either the source or destination so that we know where to attach the policy to"
      },
      "description": ""
    },
    "acl_tags": {
      "type": "object",
      "additionalProperties": {
        "title": "acl_tag",
        "required": [
          "type"
        ],
        "type": "object",
        "properties": {
          "ether_types": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "ARP / IPv6. Default is `any`",
            "default": [
              "any"
            ]
          },
          "gbp_tag": {
            "type": "integer",
            "description": "Required if\n  - `type`==`dynamic_gbp` (gbp_tag received from RADIUS)\n  - `type`==`gbp_resource`\n  - `type`==`static_gbp` (applying gbp tag against matching conditions)",
            "contentEncoding": "int32"
          },
          "macs": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Required if \n- `type`==`mac`\n- `type`==`static_gbp` if from matching mac"
          },
          "network": {
            "type": "string",
            "description": "If:\n  * `type`==`mac` (optional. default is `any`)\n  * `type`==`subnet` (optional. default is `any`)\n  * `type`==`network`\n  * `type`==`resource` (optional. default is `any`)\n  * `type`==`static_gbp` if from matching network (vlan)"
          },
          "port_usage": {
            "type": "string",
            "description": "Required if `type`==`port_usage`"
          },
          "radius_group": {
            "type": "string",
            "description": "Required if:\n  * `type`==`radius_group`\n  * `type`==`static_gbp`\nif from matching radius_group"
          },
          "specs": {
            "type": "array",
            "items": {
              "title": "acl_tag_spec",
              "type": "object",
              "properties": {
                "port_range": {
                  "type": "string",
                  "description": "Matched dst port, \"0\" means any",
                  "default": "0"
                },
                "protocol": {
                  "type": "string",
                  "description": "`tcp` / `udp` / `icmp` / `icmp6` / `gre` / `any` / `:protocol_number`, `protocol_number` is between 1-254, default is `any` `protocol_number` is between 1-254",
                  "default": "any"
                }
              }
            },
            "description": "If `type`==`resource`, `type`==`radius_group`, `type`==`port_usage` or `type`==`gbp_resource`. Empty means unrestricted, i.e. any"
          },
          "subnets": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "If \n- `type`==`subnet` \n- `type`==`resource` (optional. default is `any`)\n- `type`==`static_gbp` if from matching subnet"
          },
          "type": {
            "type": "string",
            "description": "enum: \n  * `any`: matching anything not identified\n  * `dynamic_gbp`: from the gbp_tag received from RADIUS\n  * `gbp_resource`: can only be used in `dst_tags`\n  * `mac`\n  * `network`\n  * `port_usage`\n  * `radius_group`\n  * `resource`: can only be used in `dst_tags`\n  * `static_gbp`: applying gbp tag against matching conditions\n  * `subnet`'"
          }
        },
        "description": "Resource tags (`type`==`resource` or `type`==`gbp_resource`) can only be used in `dst_tags`"
      },
      "description": "ACL Tags to identify traffic source or destination. Key name is the tag name"
    },
    "additional_config_cmds": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "additional CLI commands to append to the generated Junos config. **Note**: no check is done"
    },
    "bgp_config": {
      "type": "object",
      "additionalProperties": {
        "title": "switch_bgp_config",
        "required": [
          "local_as",
          "type"
        ],
        "type": "object",
        "properties": {
          "auth_key": {
            "type": "string"
          },
          "bfd_minimum_interval": {
            "maximum": 255000.0,
            "minimum": 1.0,
            "type": "integer",
            "description": "Minimum interval in milliseconds for BFD hello packets. A neighbor is considered failed when the device stops receiving replies after the specified interval. Value must be between 1 and 255000.",
            "contentEncoding": "int32"
          },
          "export_policy": {
            "type": "string",
            "description": "Export policy must match one of the policy names defined in the `routing_policies` property."
          },
          "hold_time": {
            "type": "object",
            "description": "Hold time is three times the interval at which keepalive messages are sent. It indicates to the peer the length of time that it should consider the sender valid. Must be 0 or a number in the range 3-65535."
          },
          "import_policy": {
            "type": "string",
            "description": "Import policy must match one of the policy names defined in the `routing_policies` property."
          },
          "local_as": {
            "type": "object",
            "description": "BGP AS, value in range 1-4294967294. Can be a Variable (e.g. `{{bgp_as}}` )"
          },
          "neighbors": {
            "type": "object",
            "additionalProperties": {
              "title": "switch_bgp_config_neighbor",
              "required": [
                "neighbor_as"
              ],
              "type": "object",
              "properties": {
                "export_policy": {
                  "type": "string",
                  "description": "Export policy must match one of the policy names defined in the `routing_policies` property."
                },
                "hold_time": {
                  "type": "object",
                  "description": "Hold time is three times the interval at which keepalive messages are sent. It indicates to the peer the length of time that it should consider the sender valid. Must be 0 or a number in the range 3-65535."
                },
                "import_policy": {
                  "type": "string",
                  "description": "Import policy must match one of the policy names defined in the `routing_policies` property."
                },
                "multihop_ttl": {
                  "maximum": 255.0,
                  "minimum": 1.0,
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "neighbor_as": {
                  "anyOf": [
                    {
                      "type": "string"
                    },
                    {
                      "maximum": 4294967294.0,
                      "minimum": 1.0,
                      "type": "integer",
                      "contentEncoding": "int32"
                    }
                  ],
                  "description": "Autonomous System (AS) number of the BGP neighbor. For internal BGP, this must match `local_as`. For external BGP, this must differ from `local_as`.",
                  "examples": [
                    "65000"
                  ]
                }
              }
            },
            "description": "Property key is the BGP Neighbor IP Address."
          },
          "networks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of network names for BGP configuration. When a network is specified, a BGP group will be added to the VRF that network is part of."
          },
          "type": {
            "type": "string",
            "description": "enum: `external`, `internal`"
          }
        }
      }
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "dhcp_snooping": {
      "title": "dhcp_snooping",
      "type": "object",
      "properties": {
        "all_networks": {
          "type": "boolean"
        },
        "enable_arp_spoof_check": {
          "type": "boolean",
          "description": "Enable for dynamic ARP inspection check"
        },
        "enable_ip_source_guard": {
          "type": "boolean",
          "description": "Enable for check for forging source IP address"
        },
        "enabled": {
          "type": "boolean"
        },
        "networks": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "If `all_networks`==`false`, list of network with DHCP snooping enabled"
        }
      }
    },
    "dns_servers": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Global dns settings. To keep compatibility, dns settings in `ip_config` and `oob_ip_config` will overwrite this setting"
    },
    "dns_suffix": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Global dns settings. To keep compatibility, dns settings in `ip_config` and `oob_ip_config` will overwrite this setting"
    },
    "extra_routes": {
      "type": "object",
      "additionalProperties": {
        "title": "extra_route",
        "type": "object",
        "properties": {
          "discard": {
            "type": "boolean",
            "description": "This takes precedence",
            "default": false
          },
          "metric": {
            "maximum": 2147483647.0,
            "minimum": 0.0,
            "type": [
              "integer",
              "null"
            ],
            "contentEncoding": "int32"
          },
          "next_qualified": {
            "type": "object",
            "additionalProperties": {
              "title": "extra_route_next_qualified_properties",
              "type": "object",
              "properties": {
                "metric": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32"
                },
                "preference": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32"
                }
              }
            },
            "examples": [
              {
                "10.3.1.1": {
                  "metric": null,
                  "preference": 40
                }
              }
            ]
          },
          "no_resolve": {
            "type": "boolean",
            "default": false
          },
          "preference": {
            "maximum": 2147483647.0,
            "minimum": 0.0,
            "type": [
              "integer",
              "null"
            ],
            "contentEncoding": "int32",
            "examples": [
              30
            ]
          },
          "via": {
            "type": "object",
            "description": "Next-hop IP Address. Can be a single IP address or an array of IP addresses for ECMP (Equal-Cost Multi-Path) load balancing across multiple next-hops."
          }
        }
      },
      "description": "Property key is the destination CIDR (e.g. \"10.0.0.0/8\")",
      "examples": [
        {
          "0.0.0.0/0": {
            "via": "192.168.1.10"
          }
        }
      ]
    },
    "extra_routes6": {
      "type": "object",
      "additionalProperties": {
        "title": "extra_route6",
        "type": "object",
        "properties": {
          "discard": {
            "type": "boolean",
            "description": "This takes precedence",
            "default": false
          },
          "metric": {
            "maximum": 2147483647.0,
            "minimum": 0.0,
            "type": [
              "integer",
              "null"
            ],
            "contentEncoding": "int32"
          },
          "next_qualified": {
            "type": "object",
            "additionalProperties": {
              "title": "extra_route6_next_qualified_properties",
              "type": "object",
              "properties": {
                "metric": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32"
                },
                "preference": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32"
                }
              }
            },
            "examples": [
              {
                "2a02:1234:200a::100": {
                  "metric": null,
                  "preference": 40
                }
              }
            ]
          },
          "no_resolve": {
            "type": "boolean",
            "default": false
          },
          "preference": {
            "maximum": 2147483647.0,
            "minimum": 0.0,
            "type": [
              "integer",
              "null"
            ],
            "contentEncoding": "int32",
            "examples": [
              30
            ]
          },
          "via": {
            "type": "object",
            "description": "Next-hop IP Address. Can be a single IP address or an array of IP addresses for ECMP (Equal-Cost Multi-Path) load balancing across multiple next-hops."
          }
        }
      },
      "description": "Property key is the destination CIDR (e.g. \"2a02:1234:420a:10c9::/64\")",
      "examples": [
        {
          "2a02:1234:420a:10c9::/64": {
            "via": "2a02:1234:200a::100"
          }
        }
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
    "import_org_networks": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Org Networks that we'd like to import"
    },
    "mist_nac": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean"
        },
        "network": {
          "type": "string"
        }
      },
      "description": "Enable mist_nac to use RadSec"
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string"
    },
    "networks": {
      "type": "object",
      "additionalProperties": {
        "title": "switch_network",
        "required": [
          "vlan_id"
        ],
        "type": "object",
        "properties": {
          "gateway": {
            "type": "string",
            "description": "Only required for EVPN-VXLAN networks, IPv4 Virtual Gateway"
          },
          "gateway6": {
            "type": "string",
            "description": "Only required for EVPN-VXLAN networks, IPv6 Virtual Gateway"
          },
          "isolation": {
            "type": "boolean",
            "description": "whether to stop clients to talk to each other, default is false (when enabled, a unique isolation_vlan_id is required). NOTE: this features requires uplink device to also a be Juniper device and `inter_switch_link` to be set. See also `inter_isolation_network_link` and `community_vlan_id` in port_usage",
            "default": false
          },
          "isolation_vlan_id": {
            "type": "string",
            "examples": [
              "3070"
            ]
          },
          "subnet": {
            "type": "string",
            "description": "Optional for pure switching, required when L3 / routing features are used"
          },
          "subnet6": {
            "type": "string",
            "description": "Optional for pure switching, required when L3 / routing features are used"
          },
          "vlan_id": {
            "type": "object"
          }
        },
        "description": "A network represents a network segment. It can either represent a VLAN (then usually ties to a L3 subnet), optionally associate it with a subnet which can later be used to create addition routes. Used for ports doing `family ethernet-switching`. It can also be a pure L3-subnet that can then be used against a port that with `family inet`."
      },
      "description": "Property key is network name"
    },
    "ntp_servers": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of NTP servers specific to this device. By default, those in Site Settings will be used"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "ospf_areas": {
      "type": "object",
      "additionalProperties": {
        "title": "ospf_area",
        "type": "object",
        "properties": {
          "include_loopback": {
            "type": "boolean",
            "default": false
          },
          "networks": {
            "type": "object",
            "additionalProperties": {
              "title": "ospf_areas_network",
              "type": "object",
              "properties": {
                "auth_keys": {
                  "type": "object",
                  "additionalProperties": {
                    "type": "string"
                  },
                  "description": "Required if `auth_type`==`md5`. Property key is the key number",
                  "examples": [
                    {
                      "1": "auth-key-1"
                    }
                  ]
                },
                "auth_password": {
                  "type": "string",
                  "description": "Required if `auth_type`==`password`, the password, max length is 8",
                  "examples": [
                    "simple"
                  ]
                },
                "auth_type": {
                  "type": "string",
                  "description": "auth type. enum: `md5`, `none`, `password`"
                },
                "bfd_minimum_interval": {
                  "maximum": 255000.0,
                  "minimum": 1.0,
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    500
                  ]
                },
                "dead_interval": {
                  "maximum": 65535.0,
                  "minimum": 1.0,
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    40
                  ]
                },
                "export_policy": {
                  "type": "string",
                  "examples": [
                    "export_policy"
                  ]
                },
                "hello_interval": {
                  "maximum": 255.0,
                  "minimum": 1.0,
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "import_policy": {
                  "type": "string",
                  "examples": [
                    "import_policy"
                  ]
                },
                "interface_type": {
                  "type": "string",
                  "description": "interface type (nbma = non-broadcast multi-access). enum: `broadcast`, `nbma`, `p2mp`, `p2p`"
                },
                "metric": {
                  "maximum": 65535.0,
                  "minimum": 1.0,
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32",
                  "examples": [
                    10000
                  ]
                },
                "no_readvertise_to_overlay": {
                  "type": "boolean",
                  "description": "By default, we'll re-advertise all learned OSPF routes toward overlay",
                  "default": false
                },
                "passive": {
                  "type": "boolean",
                  "description": "Whether to send OSPF-Hello",
                  "default": false
                }
              },
              "description": "Property key is the network name. Networks to participate in an OSPF area"
            },
            "examples": [
              {
                "corp": {
                  "auth_keys": {
                    "1": "auth-key-1"
                  },
                  "auth_type": "md5",
                  "bfd_minimum_interval": 500,
                  "dead_interval": 40,
                  "hello_interval": 10,
                  "interface_type": "nbma",
                  "metric": 10000
                },
                "guest": {
                  "passive": true
                }
              }
            ]
          },
          "type": {
            "type": "string",
            "description": "OSPF type. enum: `default`, `nssa`, `stub`"
          }
        },
        "description": "Property key is the OSPF Area (Area should be a number (0-255) / IP address)"
      },
      "description": "Junos OSPF areas. Property key is the OSPF Area (Area should be a number (0-255) / IP address)"
    },
    "port_mirroring": {
      "type": "object",
      "additionalProperties": {
        "title": "switch_port_mirroring_property",
        "type": "object",
        "properties": {
          "input_networks_ingress": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "At least one of the `input_port_ids_ingress`, `input_port_ids_egress` or `input_networks_ingress ` should be specified"
          },
          "input_port_ids_egress": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "At least one of the `input_port_ids_ingress`, `input_port_ids_egress` or `input_networks_ingress ` should be specified"
          },
          "input_port_ids_ingress": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "At least one of the `input_port_ids_ingress`, `input_port_ids_egress` or `input_networks_ingress ` should be specified"
          },
          "output_ip_address": {
            "type": "string",
            "description": "Exactly one of the `output_ip_address`, `output_port_id` or `output_network` should be provided",
            "examples": [
              "1.2.3.4"
            ]
          },
          "output_network": {
            "type": "string",
            "description": "Exactly one of the `output_ip_address`, `output_port_id` or `output_network` should be provided",
            "examples": [
              "analyze"
            ]
          },
          "output_port_id": {
            "type": "string",
            "description": "Exactly one of the `output_ip_address`, `output_port_id` or `output_network` should be provided",
            "examples": [
              "ge-0/0/5"
            ]
          }
        }
      },
      "description": "Property key is the port mirroring instance name. `port_mirroring` can be added under device/site settings. It takes interface and ports as input for ingress, interface as input for egress and can take interface and port as output. A maximum 4 mirroring ports is allowed"
    },
    "port_usages": {
      "type": "object",
      "additionalProperties": {
        "title": "switch_port_usage",
        "type": "object",
        "properties": {
          "all_networks": {
            "type": "boolean",
            "description": "Only if `mode`==`trunk`. Whether to trunk all network/vlans",
            "default": false
          },
          "allow_dhcpd": {
            "type": "boolean",
            "description": "Only applies when `mode`!=`dynamic`. Controls whether DHCP server traffic is allowed on ports using this configuration if DHCP snooping is enabled. This is a tri-state setting; `true`: ports become trusted ports allowing DHCP server traffic, `false`: ports become untrusted blocking DHCP server traffic, undefined: use system defaults (access ports default to untrusted, trunk ports default to trusted)."
          },
          "allow_multiple_supplicants": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`",
            "default": false
          },
          "bypass_auth_when_server_down": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic` and `port_auth`==`dot1x`. Bypass auth for known clients if set to true when RADIUS server is down",
            "default": false
          },
          "bypass_auth_when_server_down_for_unknown_client": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic` and `port_auth`=`dot1x`. Bypass auth for all (including unknown clients) if set to true when RADIUS server is down",
            "default": false
          },
          "bypass_auth_when_server_down_for_voip": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic` and `port_auth`==`dot1x`. Bypass auth for VOIP if set to true when RADIUS server is down",
            "default": false
          },
          "community_vlan_id": {
            "type": "integer",
            "description": "Only if `mode`!=`dynamic`. To be used together with `isolation` under networks. Signaling that this port connects to the networks isolated but wired clients belong to the same community can talk to each other",
            "contentEncoding": "int32"
          },
          "description": {
            "type": "string",
            "description": "Only if `mode`!=`dynamic`"
          },
          "disable_autoneg": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`. If speed and duplex are specified, whether to disable autonegotiation",
            "default": false
          },
          "disabled": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`. Whether the port is disabled",
            "default": false
          },
          "duplex": {
            "type": "string",
            "description": "Only if `mode`!=`dynamic`. Link connection mode. enum: `auto`, `full`, `half`"
          },
          "dynamic_vlan_networks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Only if `mode`!=`dynamic` and `port_auth`==`dot1x`, if dynamic vlan is used, specify the possible networks/vlans RADIUS can return",
            "examples": [
              [
                "corp",
                "user"
              ]
            ]
          },
          "enable_mac_auth": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic` and `port_auth`==`dot1x`. Whether to enable MAC Auth",
            "default": false
          },
          "enable_qos": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`",
            "default": false
          },
          "guest_network": {
            "type": [
              "string",
              "null"
            ],
            "description": "Only if `mode`!=`dynamic` and `port_auth`==`dot1x`. Which network to put the device into if the device cannot do dot1x. default is null (i.e. not allowed)"
          },
          "inter_isolation_network_link": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`. `inter_isolation_network_link` is used together with `isolation` under networks, signaling that this port connects to isolated networks",
            "default": false
          },
          "inter_switch_link": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`. `inter_switch_link` is used together with `isolation` under networks. NOTE: `inter_switch_link` works only between Juniper devices. This has to be applied to both ports connected together",
            "default": false
          },
          "mac_auth_only": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic` and `enable_mac_auth`==`true`"
          },
          "mac_auth_preferred": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic` + `enable_mac_auth`==`true` + `mac_auth_only`==`false`, dot1x will be given priority then mac_auth. Enable this to prefer mac_auth over dot1x."
          },
          "mac_auth_protocol": {
            "type": "string",
            "description": "Only if `mode`!=`dynamic` and `enable_mac_auth` ==`true`. This type is ignored if mist_nac is enabled. enum: `eap-md5`, `eap-peap`, `pap`"
          },
          "mac_limit": {
            "type": "object",
            "description": "Only if `mode`!=`dynamic`, max number of mac addresses, default is 0 for unlimited, otherwise range is 1 to 16383 (upper bound constrained by platform)"
          },
          "mode": {
            "type": "string",
            "description": "`mode`==`dynamic` must only be used if the port usage name is `dynamic`. enum: `access`, `dynamic`, `inet`, `trunk`"
          },
          "mtu": {
            "type": "object",
            "description": "Only if `mode`!=`dynamic` media maximum transmission unit (MTU) is the largest data unit that can be forwarded without fragmentation. The default value is 1514."
          },
          "networks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Only if `mode`==`trunk`, the list of network/vlans"
          },
          "persist_mac": {
            "type": "boolean",
            "description": "Only if `mode`==`access` and `port_auth`!=`dot1x`. Whether the port should retain dynamically learned MAC addresses",
            "default": false
          },
          "poe_disabled": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`. Whether PoE capabilities are disabled for a port",
            "default": false
          },
          "poe_priority": {
            "type": "string",
            "description": "PoE priority. enum: `low`, `high`"
          },
          "port_auth": {
            "type": "object",
            "description": "Only if `mode`!=`dynamic`. If dot1x is desired, set to dot1x. enum: `dot1x`"
          },
          "port_network": {
            "type": "string",
            "description": "Only if `mode`!=`dynamic`. Native network/vlan for untagged traffic"
          },
          "reauth_interval": {
            "type": "object",
            "description": "Only if `mode`!=`dynamic` and `port_auth`=`dot1x` reauthentication interval range (min: 10, max: 65535, default: 3600)"
          },
          "reset_default_when": {
            "type": "string",
            "description": "Only if `mode`==`dynamic` Control when the DPC port should be changed to the default port usage. enum: `link_down`, `none` (let the DPC port keep at the current port usage)"
          },
          "rules": {
            "type": "array",
            "items": {
              "title": "switch_port_usage_dynamic_rule",
              "required": [
                "src"
              ],
              "type": "object",
              "properties": {
                "description": {
                  "type": "string",
                  "description": "Optional description of the rule"
                },
                "equals": {
                  "type": "string"
                },
                "equals_any": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": "Use `equals_any` to match any item in a list"
                },
                "expression": {
                  "type": "string",
                  "description": "\"[0:3]\":\"abcdef\" -> \"abc\"\n\"split(.)[1]\": \"a.b.c\" -> \"b\"\n\"split(-)[1][0:3]: \"a1234-b5678-c90\" -> \"b56\""
                },
                "src": {
                  "type": "string",
                  "description": "enum: `link_peermac`, `lldp_chassis_id`, `lldp_hardware_revision`, `lldp_manufacturer_name`, `lldp_oui`, `lldp_serial_number`, `lldp_system_description`, `lldp_system_name`, `radius_dynamicfilter`, `radius_usermac`, `radius_username`"
                },
                "usage": {
                  "type": "string",
                  "description": "`port_usage` name"
                }
              }
            },
            "description": "Only if `mode`==`dynamic`"
          },
          "server_fail_network": {
            "type": [
              "string",
              "null"
            ],
            "description": "Only if `mode`!=`dynamic` and `port_auth`==`dot1x`. Sets server fail fallback vlan"
          },
          "server_reject_network": {
            "type": [
              "string",
              "null"
            ],
            "description": "Only if `mode`!=`dynamic` and `port_auth`==`dot1x`. When radius server reject / fails"
          },
          "speed": {
            "type": "string",
            "description": "Only if `mode`!=`dynamic`, Port speed, default is auto to automatically negotiate speed enum: `100m`, `10m`, `1g`, `2.5g`, `5g`, `10g`, `25g`, `40g`, `100g`,`auto`"
          },
          "storm_control": {
            "type": "object",
            "properties": {
              "disable_port": {
                "type": "boolean",
                "description": "Whether to disable the port when storm control is triggered",
                "default": false
              },
              "no_broadcast": {
                "type": "boolean",
                "description": "Whether to disable storm control on broadcast traffic",
                "default": false
              },
              "no_multicast": {
                "type": "boolean",
                "description": "Whether to disable storm control on multicast traffic",
                "default": false
              },
              "no_registered_multicast": {
                "type": "boolean",
                "description": "Whether to disable storm control on registered multicast traffic",
                "default": false
              },
              "no_unknown_unicast": {
                "type": "boolean",
                "description": "Whether to disable storm control on unknown unicast traffic",
                "default": false
              },
              "percentage": {
                "maximum": 100.0,
                "minimum": 0.0,
                "type": "integer",
                "description": "Bandwidth-percentage, configures the storm control level as a percentage of the available bandwidth",
                "contentEncoding": "int32",
                "default": 80
              }
            },
            "description": "Switch storm control. Only if `mode`!=`dynamic`"
          },
          "stp_disable": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic` and `stp_required`==`false`. Drop bridge protocol data units (BPDUs ) that enter any interface or a specified interface",
            "default": false
          },
          "stp_edge": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`. When enabled, the port is not expected to receive BPDU frames",
            "default": false
          },
          "stp_no_root_port": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`",
            "default": false
          },
          "stp_p2p": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`",
            "default": false
          },
          "stp_required": {
            "type": "boolean",
            "description": "Only if `mode`!=`dynamic`. Whether to remain in block state if no BPDU is received",
            "default": false
          },
          "ui_evpntopo_id": {
            "type": "string",
            "description": "Optional for Campus Fabric Core-Distribution ESI-LAG profile. Helper used by the UI to select this port profile as the ESI-Lag between Distribution and Access switches",
            "contentEncoding": "uuid"
          },
          "use_vstp": {
            "type": "boolean",
            "description": "If this is connected to a vstp network",
            "default": false
          },
          "voip_network": {
            "type": [
              "string",
              "null"
            ],
            "description": "Only if `mode`!=`dynamic`. Network/vlan for voip traffic, must also set port_network. to authenticate device, set port_auth"
          }
        },
        "description": "Junos port usages"
      },
      "description": "Property key is the port usage name. Defines the profiles of port configuration configured on the switch"
    },
    "radius_config": {
      "type": "object",
      "properties": {
        "acct_immediate_update": {
          "type": "boolean"
        },
        "acct_interim_interval": {
          "maximum": 65535.0,
          "minimum": 0.0,
          "type": "integer",
          "description": "How frequently should interim accounting be reported, 60-65535. default is 0 (use one specified in Access-Accept request from RADIUS Server). Very frequent messages can affect the performance of the radius server, 600 and up is recommended when enabled",
          "contentEncoding": "int32",
          "default": 0
        },
        "acct_servers": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "title": "radius_acct_server",
            "required": [
              "host",
              "secret"
            ],
            "type": "object",
            "properties": {
              "host": {
                "type": "string",
                "description": "IP/ hostname of RADIUS server",
                "examples": [
                  "1.2.3.4"
                ]
              },
              "keywrap_enabled": {
                "type": "boolean"
              },
              "keywrap_format": {
                "type": "string",
                "description": "enum: `ascii`, `hex`"
              },
              "keywrap_kek": {
                "type": "string",
                "examples": [
                  "1122334455"
                ]
              },
              "keywrap_mack": {
                "type": "string",
                "examples": [
                  "1122334455"
                ]
              },
              "port": {
                "type": "object",
                "description": "Radius Auth Port, value from 1 to 65535, default is 1813"
              },
              "secret": {
                "type": "string",
                "description": "Secret of RADIUS server",
                "examples": [
                  "testing123"
                ]
              }
            }
          },
          "description": ""
        },
        "auth_server_selection": {
          "type": "string",
          "description": "enum: `ordered`, `unordered`"
        },
        "auth_servers": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "title": "radius_auth_server",
            "required": [
              "host",
              "secret"
            ],
            "type": "object",
            "properties": {
              "host": {
                "type": "string",
                "description": "IP/ hostname of RADIUS server",
                "examples": [
                  "1.2.3.4"
                ]
              },
              "keywrap_enabled": {
                "type": "boolean"
              },
              "keywrap_format": {
                "type": "string",
                "description": "enum: `ascii`, `hex`"
              },
              "keywrap_kek": {
                "type": "string",
                "examples": [
                  "1122334455"
                ]
              },
              "keywrap_mack": {
                "type": "string",
                "examples": [
                  "1122334455"
                ]
              },
              "port": {
                "type": "object",
                "description": "Radius Auth Port, value from 1 to 65535, default is 1812"
              },
              "require_message_authenticator": {
                "type": "boolean",
                "description": "Whether to require Message-Authenticator in requests",
                "default": false
              },
              "secret": {
                "type": "string",
                "description": "Secret of RADIUS server",
                "examples": [
                  "testing123"
                ]
              }
            },
            "description": "Authentication Server"
          },
          "description": ""
        },
        "auth_servers_retries": {
          "type": "integer",
          "description": "Radius auth session retries",
          "contentEncoding": "int32",
          "default": 3
        },
        "auth_servers_timeout": {
          "type": "integer",
          "description": "Radius auth session timeout",
          "contentEncoding": "int32",
          "default": 5
        },
        "coa_enabled": {
          "type": "boolean",
          "default": false
        },
        "coa_port": {
          "type": "object",
          "description": "Radius CoA Port, value from 1 to 65535, default is 3799"
        },
        "fast_dot1x_timers": {
          "type": "boolean",
          "default": false
        },
        "network": {
          "type": "string",
          "description": "Use `network`or `source_ip`. Which network the RADIUS server resides, if there's static IP for this network, we'd use it as source-ip"
        },
        "source_ip": {
          "type": "string",
          "description": "Use `network`or `source_ip`"
        }
      },
      "description": "Junos Radius config"
    },
    "remote_syslog": {
      "title": "remote_syslog",
      "type": "object",
      "properties": {
        "archive": {
          "title": "remote_syslog_archive",
          "type": "object",
          "properties": {
            "files": {
              "type": "object"
            },
            "size": {
              "type": "string",
              "examples": [
                "5m"
              ]
            }
          }
        },
        "cacerts": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "",
          "examples": [
            [
              "-----BEGIN CERTIFICATE-----\\nMIIFZjCCA06gAwIBAgIIP61/1qm/uDowDQYJKoZIhvcNAQELBQE\\n-----END CERTIFICATE-----",
              "-----BEGIN CERTIFICATE-----\\nBhMCRVMxFDASBgNVBAoMC1N0YXJ0Q29tIENBMSwwKgYDVn-----END CERTIFICATE-----"
            ]
          ]
        },
        "console": {
          "title": "remote_syslog_console",
          "type": "object",
          "properties": {
            "contents": {
              "type": "array",
              "items": {
                "title": "remote_syslog_content",
                "type": "object",
                "properties": {
                  "facility": {
                    "type": "string",
                    "description": "enum: `any`, `authorization`, `change-log`, `config`, `conflict-log`, `daemon`, `dfc`, `external`, `firewall`, `ftp`, `interactive-commands`, `kernel`, `ntp`, `pfe`, `security`, `user`"
                  },
                  "severity": {
                    "type": "string",
                    "description": "enum: `alert`, `any`, `critical`, `emergency`, `error`, `info`, `notice`, `warning`"
                  }
                }
              },
              "description": ""
            }
          }
        },
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "files": {
          "type": "array",
          "items": {
            "title": "remote_syslog_file_config",
            "type": "object",
            "properties": {
              "archive": {
                "title": "remote_syslog_archive",
                "type": "object",
                "properties": {
                  "files": {
                    "type": "object"
                  },
                  "size": {
                    "type": "string",
                    "examples": [
                      "5m"
                    ]
                  }
                }
              },
              "contents": {
                "type": "array",
                "items": {
                  "title": "remote_syslog_content",
                  "type": "object",
                  "properties": {
                    "facility": {
                      "type": "string",
                      "description": "enum: `any`, `authorization`, `change-log`, `config`, `conflict-log`, `daemon`, `dfc`, `external`, `firewall`, `ftp`, `interactive-commands`, `kernel`, `ntp`, `pfe`, `security`, `user`"
                    },
                    "severity": {
                      "type": "string",
                      "description": "enum: `alert`, `any`, `critical`, `emergency`, `error`, `info`, `notice`, `warning`"
                    }
                  }
                },
                "description": ""
              },
              "enable_tls": {
                "type": "boolean",
                "description": "Only if `protocol`==`tcp`"
              },
              "explicit_priority": {
                "type": "boolean"
              },
              "file": {
                "type": "string",
                "examples": [
                  "file-name"
                ]
              },
              "match": {
                "type": "string",
                "examples": [
                  "!alarm|ntp|errors.crc_error[chan]"
                ]
              },
              "structured_data": {
                "type": "boolean"
              }
            }
          },
          "description": ""
        },
        "network": {
          "type": "string",
          "description": "If source_address is configured, will use the vlan firstly otherwise use source_ip",
          "examples": [
            "default"
          ]
        },
        "send_to_all_servers": {
          "type": "boolean",
          "default": false
        },
        "servers": {
          "type": "array",
          "items": {
            "title": "remote_syslog_server",
            "type": "object",
            "properties": {
              "contents": {
                "type": "array",
                "items": {
                  "title": "remote_syslog_content",
                  "type": "object",
                  "properties": {
                    "facility": {
                      "type": "string",
                      "description": "enum: `any`, `authorization`, `change-log`, `config`, `conflict-log`, `daemon`, `dfc`, `external`, `firewall`, `ftp`, `interactive-commands`, `kernel`, `ntp`, `pfe`, `security`, `user`"
                    },
                    "severity": {
                      "type": "string",
                      "description": "enum: `alert`, `any`, `critical`, `emergency`, `error`, `info`, `notice`, `warning`"
                    }
                  }
                },
                "description": ""
              },
              "explicit_priority": {
                "type": "boolean"
              },
              "facility": {
                "type": "string",
                "description": "enum: `any`, `authorization`, `change-log`, `config`, `conflict-log`, `daemon`, `dfc`, `external`, `firewall`, `ftp`, `interactive-commands`, `kernel`, `ntp`, `pfe`, `security`, `user`"
              },
              "host": {
                "type": "string",
                "examples": [
                  "syslogd.internal"
                ]
              },
              "match": {
                "type": "string",
                "examples": [
                  "!alarm|ntp|errors.crc_error[chan]"
                ]
              },
              "port": {
                "type": "object",
                "description": "Syslog Service Port, value from 1 to 65535"
              },
              "protocol": {
                "type": "string",
                "description": "enum: `tcp`, `udp`"
              },
              "routing_instance": {
                "type": "string",
                "examples": [
                  "routing-instance-name"
                ]
              },
              "server_name": {
                "type": "string",
                "description": "Name of the server",
                "examples": [
                  "syslogd.internal"
                ]
              },
              "severity": {
                "type": "string",
                "description": "enum: `alert`, `any`, `critical`, `emergency`, `error`, `info`, `notice`, `warning`"
              },
              "source_address": {
                "type": "string",
                "description": "If source_address is configured, will use the vlan firstly otherwise use source_ip"
              },
              "structured_data": {
                "type": "boolean"
              },
              "tag": {
                "type": "string"
              }
            }
          },
          "description": "",
          "examples": [
            [
              {
                "facility": "config",
                "host": "syslogd.internal",
                "port": 514,
                "protocol": "udp",
                "severity": "info",
                "tag": ""
              }
            ]
          ]
        },
        "time_format": {
          "type": "string",
          "description": "enum: `millisecond`, `year`, `year millisecond`"
        },
        "users": {
          "type": "array",
          "items": {
            "title": "remote_syslog_user",
            "type": "object",
            "properties": {
              "contents": {
                "type": "array",
                "items": {
                  "title": "remote_syslog_content",
                  "type": "object",
                  "properties": {
                    "facility": {
                      "type": "string",
                      "description": "enum: `any`, `authorization`, `change-log`, `config`, `conflict-log`, `daemon`, `dfc`, `external`, `firewall`, `ftp`, `interactive-commands`, `kernel`, `ntp`, `pfe`, `security`, `user`"
                    },
                    "severity": {
                      "type": "string",
                      "description": "enum: `alert`, `any`, `critical`, `emergency`, `error`, `info`, `notice`, `warning`"
                    }
                  }
                },
                "description": ""
              },
              "match": {
                "type": "string",
                "examples": [
                  "\"!alarm|ntp|errors.crc_error[chan]\""
                ]
              },
              "user": {
                "type": "string",
                "examples": [
                  "*"
                ]
              }
            }
          },
          "description": ""
        }
      }
    },
    "remove_existing_configs": {
      "type": "boolean",
      "description": "By default, only the configuration generated by Mist is cleaned up during the configuration process. If `true`, all the existing configuration will be removed.",
      "default": false
    },
    "routing_policies": {
      "type": "object",
      "additionalProperties": {
        "title": "sw_routing_policy",
        "type": "object",
        "properties": {
          "terms": {
            "minItems": 1,
            "uniqueItems": true,
            "type": "array",
            "items": {
              "title": "sw_routing_policy_term",
              "required": [
                "name"
              ],
              "type": "object",
              "properties": {
                "actions": {
                  "type": "object",
                  "properties": {
                    "accept": {
                      "type": "boolean"
                    },
                    "community": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "When used as export policy, optional"
                    },
                    "local_preference": {
                      "type": "object",
                      "description": "Optional, for an import policy, local_preference can be changed, value in range 1-4294967294. Can be a Variable (e.g. `{{bgp_as}}`)"
                    },
                    "prepend_as_path": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "When used as export policy, optional. By default, the local AS will be prepended, to change it. Can be a Variable (e.g. `{{as_path}}`)"
                    }
                  },
                  "description": "When used as import policy"
                },
                "matching": {
                  "type": "object",
                  "properties": {
                    "as_path": {
                      "type": "array",
                      "items": {
                        "anyOf": [
                          {
                            "type": "string"
                          },
                          {
                            "maximum": 4294967294.0,
                            "minimum": 1.0,
                            "type": "integer",
                            "contentEncoding": "int32"
                          }
                        ],
                        "description": "BGP AS, value in range 1-4294967294. Can be a Variable (e.g. `{{bgp_as}}` )",
                        "examples": [
                          "65000"
                        ]
                      },
                      "description": ""
                    },
                    "community": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": ""
                    },
                    "prefix": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "zero or more criteria/filter can be specified to match the term, all criteria have to be met"
                    },
                    "protocol": {
                      "type": "array",
                      "items": {
                        "title": "sw_routing_policy_term_matching_protocol_enum",
                        "enum": [
                          "bgp",
                          "direct",
                          "evpn",
                          "ospf",
                          "static"
                        ],
                        "type": "string",
                        "description": "enum: `bgp`, `direct`, `evpn`, `ospf`, `static`"
                      },
                      "description": ""
                    }
                  },
                  "description": "zero or more criteria/filter can be specified to match the term, all criteria have to be met"
                },
                "name": {
                  "type": "string"
                }
              }
            },
            "description": "at least criteria/filter must be specified to match the term, all criteria have to be met"
          }
        }
      },
      "description": "Property key is the routing policy name"
    },
    "snmp_config": {
      "title": "snmp_config",
      "type": "object",
      "properties": {
        "client_list": {
          "type": "array",
          "items": {
            "title": "snmp_config_client_list",
            "type": "object",
            "properties": {
              "client_list_name": {
                "type": "string",
                "examples": [
                  "clist-1"
                ]
              },
              "clients": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              }
            }
          },
          "description": ""
        },
        "contact": {
          "type": "string",
          "examples": [
            "cns@juniper.net"
          ]
        },
        "description": {
          "type": "string",
          "examples": [
            "Juniper QFX Series Switch - 1K_5LA"
          ]
        },
        "enabled": {
          "type": "boolean",
          "default": true
        },
        "engine_id": {
          "maxLength": 27,
          "type": "string"
        },
        "engine_id_type": {
          "type": "string",
          "description": "enum: `local`, `use_mac_address`"
        },
        "location": {
          "type": "string",
          "examples": [
            "Las Vegas, NV"
          ]
        },
        "name": {
          "type": "string",
          "examples": [
            "TGH-1K-QFX10K"
          ]
        },
        "network": {
          "type": "string",
          "default": "default"
        },
        "trap_groups": {
          "type": "array",
          "items": {
            "title": "snmp_config_trap_group",
            "type": "object",
            "properties": {
              "categories": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "group_name": {
                "type": "string",
                "description": "Categories list can refer to https://www.juniper.net/documentation/software/topics/task/configuration/snmp_trap-groups-configuring-junos-nm.html",
                "examples": [
                  "profiler"
                ]
              },
              "targets": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "version": {
                "type": "string",
                "description": "enum: `all`, `v1`, `v2`"
              }
            }
          },
          "description": ""
        },
        "v2c_config": {
          "type": "array",
          "items": {
            "title": "snmp_config_v2c_config",
            "type": "object",
            "properties": {
              "authorization": {
                "type": "string",
                "examples": [
                  "read-only"
                ]
              },
              "client_list_name": {
                "type": "string",
                "description": "Client_list_name here should refer to client_list above",
                "examples": [
                  "clist-1"
                ]
              },
              "community_name": {
                "type": "string",
                "examples": [
                  "abc123"
                ]
              },
              "view": {
                "type": "string",
                "description": "View name here should be defined in views above",
                "examples": [
                  "all"
                ]
              }
            }
          },
          "description": ""
        },
        "v3_config": {
          "title": "snmpv3_config",
          "type": "object",
          "properties": {
            "notify": {
              "type": "array",
              "items": {
                "title": "snmpv3_config_notify_items",
                "type": "object",
                "properties": {
                  "name": {
                    "type": "string"
                  },
                  "tag": {
                    "type": "string"
                  },
                  "type": {
                    "type": "string",
                    "description": "enum: `inform`, `trap`"
                  }
                }
              },
              "description": ""
            },
            "notify_filter": {
              "type": "array",
              "items": {
                "title": "snmpv3_config_notify_filter_item",
                "type": "object",
                "properties": {
                  "contents": {
                    "type": "array",
                    "items": {
                      "title": "snmpv3_config_notify_filter_item_content",
                      "type": "object",
                      "properties": {
                        "include": {
                          "type": "boolean"
                        },
                        "oid": {
                          "type": "string",
                          "examples": [
                            "1.3.6.1.4.1"
                          ]
                        }
                      }
                    },
                    "description": ""
                  },
                  "profile_name": {
                    "type": "string"
                  }
                }
              },
              "description": ""
            },
            "target_address": {
              "type": "array",
              "items": {
                "title": "snmpv3_config_target_address_item",
                "type": "object",
                "properties": {
                  "address": {
                    "type": "string",
                    "examples": [
                      "10.11.0.2"
                    ]
                  },
                  "address_mask": {
                    "type": "string",
                    "examples": [
                      "255.255.255.0"
                    ]
                  },
                  "port": {
                    "type": [
                      "string",
                      "null"
                    ],
                    "default": "161"
                  },
                  "tag_list": {
                    "type": "string",
                    "description": "Refer to notify tag, can be multiple with blank"
                  },
                  "target_address_name": {
                    "type": "string",
                    "examples": [
                      "target_address_name"
                    ]
                  },
                  "target_parameters": {
                    "type": "string",
                    "description": "Refer to notify target parameters name"
                  }
                }
              },
              "description": ""
            },
            "target_parameters": {
              "type": "array",
              "items": {
                "title": "snmpv3_config_target_param",
                "type": "object",
                "properties": {
                  "message_processing_model": {
                    "type": "string",
                    "description": "enum: `v1`, `v2c`, `v3`"
                  },
                  "name": {
                    "type": "string"
                  },
                  "notify_filter": {
                    "type": "string",
                    "description": "Refer to profile-name in notify_filter"
                  },
                  "security_level": {
                    "type": "string",
                    "description": "enum: `authentication`, `none`, `privacy`"
                  },
                  "security_model": {
                    "type": "string",
                    "description": "enum: `usm`, `v1`, `v2c`"
                  },
                  "security_name": {
                    "type": "string",
                    "description": "Refer to security_name in usm",
                    "examples": [
                      "m01620"
                    ]
                  }
                }
              },
              "description": ""
            },
            "usm": {
              "type": "array",
              "items": {
                "title": "snmp_usm",
                "type": "object",
                "properties": {
                  "engine_type": {
                    "type": "string",
                    "description": "enum: `local_engine`, `remote_engine`"
                  },
                  "remote_engine_id": {
                    "type": "string",
                    "description": "Required only if `engine_type`==`remote_engine`",
                    "examples": [
                      "00:00:00:0b:00:00:70:10:6f:08:b6:3f"
                    ]
                  },
                  "users": {
                    "type": "array",
                    "items": {
                      "title": "snmp_usm_user",
                      "type": "object",
                      "properties": {
                        "authentication_password": {
                          "minLength": 7,
                          "type": "string",
                          "description": "Not required if `authentication_type`==`authentication-none`. Include alphabetic, numeric, and special characters, but it cannot include control characters."
                        },
                        "authentication_type": {
                          "type": "string",
                          "description": "sha224, sha256, sha384, sha512 are supported in 21.1 and newer release. enum: `authentication-md5`, `authentication-none`, `authentication-sha`, `authentication-sha224`, `authentication-sha256`, `authentication-sha384`, `authentication-sha512`"
                        },
                        "encryption_password": {
                          "minLength": 8,
                          "type": "string",
                          "description": "Not required if `encryption_type`==`privacy-none`. Include alphabetic, numeric, and special characters, but it cannot include control characters"
                        },
                        "encryption_type": {
                          "type": "string",
                          "description": "enum: `privacy-3des`, `privacy-aes128`, `privacy-des`, `privacy-none`"
                        },
                        "name": {
                          "type": "string"
                        }
                      }
                    },
                    "description": ""
                  }
                }
              },
              "description": ""
            },
            "vacm": {
              "title": "snmp_vacm",
              "type": "object",
              "properties": {
                "access": {
                  "type": "array",
                  "items": {
                    "title": "snmp_vacm_access_item",
                    "type": "object",
                    "properties": {
                      "group_name": {
                        "type": "string"
                      },
                      "prefix_list": {
                        "type": "array",
                        "items": {
                          "title": "snmp_vacm_access_item_prefix_list_item",
                          "type": "object",
                          "properties": {
                            "context_prefix": {
                              "type": "string",
                              "description": "Only required if `type`==`context_prefix`",
                              "examples": [
                                "iil"
                              ]
                            },
                            "notify_view": {
                              "type": "string",
                              "description": "Refer to view name",
                              "examples": [
                                "all"
                              ]
                            },
                            "read_view": {
                              "type": "string",
                              "description": "Refer to view name",
                              "examples": [
                                "all"
                              ]
                            },
                            "security_level": {
                              "type": "string",
                              "description": "enum: `authentication`, `none`, `privacy`"
                            },
                            "security_model": {
                              "type": "string",
                              "description": "enum: `any`, `usm`, `v1`, `v2c`"
                            },
                            "type": {
                              "type": "string",
                              "description": "enum: `context_prefix`, `default_context_prefix`"
                            },
                            "write_view": {
                              "type": "string",
                              "description": "Refer to view name",
                              "examples": [
                                "all"
                              ]
                            }
                          }
                        },
                        "description": ""
                      }
                    }
                  },
                  "description": ""
                },
                "security_to_group": {
                  "title": "snmp_vacm_security_to_group",
                  "type": "object",
                  "properties": {
                    "content": {
                      "type": "array",
                      "items": {
                        "title": "snmp_vacm_security_to_group_content_item",
                        "type": "object",
                        "properties": {
                          "group": {
                            "type": "string",
                            "description": "Refer to group_name under access"
                          },
                          "security_name": {
                            "type": "string"
                          }
                        }
                      },
                      "description": ""
                    },
                    "security_model": {
                      "type": "string",
                      "description": "enum: `usm`, `v1`, `v2c`"
                    }
                  }
                }
              }
            }
          }
        },
        "views": {
          "type": "array",
          "items": {
            "title": "snmp_config_view",
            "type": "object",
            "properties": {
              "include": {
                "type": "boolean",
                "description": "If the root oid configured is included"
              },
              "oid": {
                "type": "string",
                "examples": [
                  "1.3.6.1"
                ]
              },
              "view_name": {
                "type": "string",
                "examples": [
                  "all"
                ]
              }
            }
          },
          "description": ""
        }
      }
    },
    "switch_matching": {
      "type": "object",
      "properties": {
        "enable": {
          "type": "boolean"
        },
        "rules": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "title": "switch_matching_rule",
            "type": "object",
            "properties": {
              "additional_config_cmds": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "additional CLI commands to append to the generated Junos config. **Note**: no check is done"
              },
              "default_port_usage": {
                "type": "string",
                "description": "Port usage to assign to switch ports without any port usage assigned. Default: `default` to preserve default behavior",
                "default": "default"
              },
              "ip_config": {
                "type": "object",
                "properties": {
                  "network": {
                    "type": "string",
                    "description": "VLAN Name for the management interface"
                  },
                  "type": {
                    "type": "string",
                    "description": "enum: `dhcp`, `static`"
                  }
                },
                "description": "In-Band Management interface configuration"
              },
              "name": {
                "maxLength": 32,
                "minLength": 1,
                "type": "string",
                "description": "Rule name. WARNING: the name `default` is reserved and can only be used for the last rule in the list"
              },
              "oob_ip_config": {
                "type": "object",
                "properties": {
                  "type": {
                    "type": "string",
                    "description": "enum: `dhcp`, `static`"
                  },
                  "use_mgmt_vrf": {
                    "type": "boolean",
                    "description": "If supported on the platform. If enabled, DNS will be using this routing-instance, too",
                    "default": false
                  },
                  "use_mgmt_vrf_for_host_out": {
                    "type": "boolean",
                    "description": "For host-out traffic (NTP/TACPLUS/RADIUS/SYSLOG/SNMP), if alternative source network/ip is desired",
                    "default": false
                  }
                },
                "description": "Out-of-Band Management interface configuration"
              },
              "port_config": {
                "type": "object",
                "additionalProperties": {
                  "title": "junos_port_config",
                  "required": [
                    "usage"
                  ],
                  "type": "object",
                  "properties": {
                    "ae_disable_lacp": {
                      "type": "boolean",
                      "description": "To disable LACP support for the AE interface"
                    },
                    "ae_idx": {
                      "type": "integer",
                      "description": "Users could force to use the designated AE name",
                      "contentEncoding": "int32"
                    },
                    "ae_lacp_slow": {
                      "type": "boolean",
                      "description": "To use fast timeout"
                    },
                    "aggregated": {
                      "type": "boolean",
                      "default": false
                    },
                    "critical": {
                      "type": "boolean",
                      "description": "To generate port up/down alarm",
                      "default": false
                    },
                    "description": {
                      "type": "string"
                    },
                    "disable_autoneg": {
                      "type": "boolean",
                      "description": "If `speed` and `duplex` are specified, whether to disable autonegotiation",
                      "default": false
                    },
                    "duplex": {
                      "type": "string",
                      "description": "enum: `auto`, `full`, `half`"
                    },
                    "dynamic_usage": {
                      "type": [
                        "string",
                        "null"
                      ],
                      "description": "Enable dynamic usage for this port. Set to `dynamic` to enable."
                    },
                    "esilag": {
                      "type": "boolean"
                    },
                    "mtu": {
                      "type": "integer",
                      "description": "Media maximum transmission unit (MTU) is the largest data unit that can be forwarded without fragmentation",
                      "contentEncoding": "int32",
                      "default": 1514
                    },
                    "networks": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "List of network names. Required if `usage`==`inet`"
                    },
                    "no_local_overwrite": {
                      "type": "boolean",
                      "description": "Prevent helpdesk to override the port config",
                      "default": true
                    },
                    "poe_disabled": {
                      "type": "boolean",
                      "default": false
                    },
                    "port_network": {
                      "type": "string",
                      "description": "Required if `usage`==`vlan_tunnel`. Q-in-Q tunneling using All-in-one bundling. This also enables standard L2PT for interfaces that are not encapsulation tunnel interfaces and uses MAC rewrite operation. [View more information](https://www.juniper.net/documentation/us/en/software/junos/multicast-l2/topics/topic-map/q-in-q.html#id-understanding-qinq-tunneling-and-vlan-translation)"
                    },
                    "speed": {
                      "type": "string",
                      "description": "enum: `100m`, `10m`, `1g`, `2.5g`, `5g`, `10g`, `25g`, `40g`, `100g`,`auto`"
                    },
                    "usage": {
                      "type": "string",
                      "description": "Port usage name. For Q-in-Q, use `vlan_tunnel`. If EVPN is used, use `evpn_uplink`or `evpn_downlink`"
                    }
                  },
                  "description": "Switch port config"
                },
                "description": "Property key is the port name or range (e.g. \"ge-0/0/0-10\")"
              },
              "port_mirroring": {
                "type": "object",
                "additionalProperties": {
                  "title": "switch_port_mirroring_property",
                  "type": "object",
                  "properties": {
                    "input_networks_ingress": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "At least one of the `input_port_ids_ingress`, `input_port_ids_egress` or `input_networks_ingress ` should be specified"
                    },
                    "input_port_ids_egress": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "At least one of the `input_port_ids_ingress`, `input_port_ids_egress` or `input_networks_ingress ` should be specified"
                    },
                    "input_port_ids_ingress": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "At least one of the `input_port_ids_ingress`, `input_port_ids_egress` or `input_networks_ingress ` should be specified"
                    },
                    "output_ip_address": {
                      "type": "string",
                      "description": "Exactly one of the `output_ip_address`, `output_port_id` or `output_network` should be provided",
                      "examples": [
                        "1.2.3.4"
                      ]
                    },
                    "output_network": {
                      "type": "string",
                      "description": "Exactly one of the `output_ip_address`, `output_port_id` or `output_network` should be provided",
                      "examples": [
                        "analyze"
                      ]
                    },
                    "output_port_id": {
                      "type": "string",
                      "description": "Exactly one of the `output_ip_address`, `output_port_id` or `output_network` should be provided",
                      "examples": [
                        "ge-0/0/5"
                      ]
                    }
                  }
                },
                "description": "Property key is the port mirroring instance name. `port_mirroring` can be added under device/site settings. It takes interface and ports as input for ingress, interface as input for egress and can take interface and port as output. A maximum 4 mirroring ports is allowed"
              },
              "stp_config": {
                "title": "switch_stp_config",
                "type": "object",
                "properties": {
                  "bridge_priority": {
                    "type": "string",
                    "description": "Switch STP priority. Range [0, 4k, 8k.. 60k] in steps of 4k. Bridge priority applies to both VSTP and RSTP.",
                    "default": "32k",
                    "examples": [
                      "40k"
                    ]
                  }
                }
              },
              "switch_mgmt": {
                "type": "object",
                "properties": {
                  "ap_affinity_threshold": {
                    "type": "integer",
                    "description": "AP_affinity_threshold ap_affinity_threshold can be added as a field under site/setting. By default, this value is set to 12. If the field is set in both site/setting and org/setting, the value from site/setting will be used.",
                    "contentEncoding": "int32",
                    "default": 10
                  },
                  "cli_banner": {
                    "type": "string",
                    "description": "Set Banners for switches. Allows markup formatting",
                    "examples": [
                      "\\t\\tWELCOME!"
                    ]
                  },
                  "cli_idle_timeout": {
                    "maximum": 60.0,
                    "minimum": 1.0,
                    "type": "integer",
                    "description": "Sets timeout for switches",
                    "contentEncoding": "int32"
                  },
                  "config_revert_timer": {
                    "maximum": 30.0,
                    "minimum": 1.0,
                    "type": "integer",
                    "description": "Rollback timer for commit confirmed",
                    "contentEncoding": "int32",
                    "default": 10
                  },
                  "dhcp_option_fqdn": {
                    "type": "boolean",
                    "description": "Enable to provide the FQDN with DHCP option 81",
                    "default": false
                  },
                  "disable_oob_down_alarm": {
                    "type": "boolean"
                  },
                  "fips_enabled": {
                    "type": "boolean",
                    "default": false
                  },
                  "local_accounts": {
                    "type": "object",
                    "additionalProperties": {
                      "title": "config_switch_local_accounts_user",
                      "type": "object",
                      "properties": {
                        "password": {
                          "type": "string",
                          "examples": [
                            "Juniper123"
                          ]
                        },
                        "role": {
                          "type": "string",
                          "description": "enum: `admin`, `helpdesk`, `none`, `read`"
                        }
                      }
                    },
                    "description": "Property key is the user name. For Local user authentication"
                  },
                  "mxedge_proxy_host": {
                    "type": "string",
                    "description": "IP Address or FQDN of the Mist Edge used to proxy the switch management traffic to the Mist Cloud"
                  },
                  "mxedge_proxy_port": {
                    "type": "object",
                    "description": "Mist Edge port used to proxy the switch management traffic to the Mist Cloud. Value in range 1-65535"
                  },
                  "protect_re": {
                    "type": "object",
                    "properties": {
                      "allowed_services": {
                        "type": "array",
                        "items": {
                          "title": "protect_re_allowed_service",
                          "enum": [
                            "icmp",
                            "ssh"
                          ],
                          "type": "string",
                          "description": "enum: `icmp`, `ssh`"
                        },
                        "description": "Optionally, services we'll allow",
                        "examples": [
                          [
                            "icmp",
                            "ssh"
                          ]
                        ]
                      },
                      "custom": {
                        "type": "array",
                        "items": {
                          "title": "protect_re_custom",
                          "type": "object",
                          "properties": {
                            "port_range": {
                              "type": "string",
                              "description": "Matched dst port, \"0\" means any",
                              "default": "0",
                              "examples": [
                                "80,1035-1040"
                              ]
                            },
                            "protocol": {
                              "type": "string",
                              "description": "enum: `any`, `icmp`, `tcp`, `udp`"
                            },
                            "subnets": {
                              "type": "array",
                              "items": {
                                "type": "string"
                              },
                              "description": ""
                            }
                          },
                          "description": "Custom acls"
                        },
                        "description": ""
                      },
                      "enabled": {
                        "type": "boolean",
                        "description": "When enabled, all traffic that is not essential to our operation will be dropped\ne.g. ntp / dns / traffic to mist will be allowed by default\n     if dhcpd is enabled, we'll make sure it works",
                        "default": false
                      },
                      "hit_count": {
                        "type": "boolean",
                        "description": "Whether to enable hit count for Protect_RE policy",
                        "default": false
                      },
                      "trusted_hosts": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "description": "host/subnets we'll allow traffic to/from"
                      }
                    },
                    "description": "Restrict inbound-traffic to host\nwhen enabled, all traffic that is not essential to our operation will be dropped \ne.g. ntp / dns / traffic to mist will be allowed by default, if dhcpd is enabled, we'll make sure it works"
                  },
                  "radius": {
                    "type": "object",
                    "properties": {
                      "enabled": {
                        "type": "boolean"
                      },
                      "radius_config": {
                        "type": "object",
                        "properties": {
                          "acct_immediate_update": {
                            "type": "boolean"
                          },
                          "acct_interim_interval": {
                            "maximum": 65535.0,
                            "minimum": 0.0,
                            "type": "integer",
                            "description": "How frequently should interim accounting be reported, 60-65535. default is 0 (use one specified in Access-Accept request from RADIUS Server). Very frequent messages can affect the performance of the radius server, 600 and up is recommended when enabled",
                            "contentEncoding": "int32",
                            "default": 0
                          },
                          "acct_servers": {
                            "uniqueItems": true,
                            "type": "array",
                            "items": {
                              "title": "radius_acct_server",
                              "required": [
                                "host",
                                "secret"
                              ],
                              "type": "object",
                              "properties": {
                                "host": {
                                  "type": "string",
                                  "description": "IP/ hostname of RADIUS server",
                                  "examples": [
                                    "1.2.3.4"
                                  ]
                                },
                                "keywrap_enabled": {
                                  "type": "boolean"
                                },
                                "keywrap_format": {
                                  "type": "string",
                                  "description": "enum: `ascii`, `hex`"
                                },
                                "keywrap_kek": {
                                  "type": "string",
                                  "examples": [
                                    "1122334455"
                                  ]
                                },
                                "keywrap_mack": {
                                  "type": "string",
                                  "examples": [
                                    "1122334455"
                                  ]
                                },
                                "port": {
                                  "type": "object",
                                  "description": "Radius Auth Port, value from 1 to 65535, default is 1813"
                                },
                                "secret": {
                                  "type": "string",
                                  "description": "Secret of RADIUS server",
                                  "examples": [
                                    "testing123"
                                  ]
                                }
                              }
                            },
                            "description": ""
                          },
                          "auth_server_selection": {
                            "type": "string",
                            "description": "enum: `ordered`, `unordered`"
                          },
                          "auth_servers": {
                            "uniqueItems": true,
                            "type": "array",
                            "items": {
                              "title": "radius_auth_server",
                              "required": [
                                "host",
                                "secret"
                              ],
                              "type": "object",
                              "properties": {
                                "host": {
                                  "type": "string",
                                  "description": "IP/ hostname of RADIUS server",
                                  "examples": [
                                    "1.2.3.4"
                                  ]
                                },
                                "keywrap_enabled": {
                                  "type": "boolean"
                                },
                                "keywrap_format": {
                                  "type": "string",
                                  "description": "enum: `ascii`, `hex`"
                                },
                                "keywrap_kek": {
                                  "type": "string",
                                  "examples": [
                                    "1122334455"
                                  ]
                                },
                                "keywrap_mack": {
                                  "type": "string",
                                  "examples": [
                                    "1122334455"
                                  ]
                                },
                                "port": {
                                  "type": "object",
                                  "description": "Radius Auth Port, value from 1 to 65535, default is 1812"
                                },
                                "require_message_authenticator": {
                                  "type": "boolean",
                                  "description": "Whether to require Message-Authenticator in requests",
                                  "default": false
                                },
                                "secret": {
                                  "type": "string",
                                  "description": "Secret of RADIUS server",
                                  "examples": [
                                    "testing123"
                                  ]
                                }
                              },
                              "description": "Authentication Server"
                            },
                            "description": ""
                          },
                          "auth_servers_retries": {
                            "type": "integer",
                            "description": "Radius auth session retries",
                            "contentEncoding": "int32",
                            "default": 3
                          },
                          "auth_servers_timeout": {
                            "type": "integer",
                            "description": "Radius auth session timeout",
                            "contentEncoding": "int32",
                            "default": 5
                          },
                          "coa_enabled": {
                            "type": "boolean",
                            "default": false
                          },
                          "coa_port": {
                            "type": "object",
                            "description": "Radius CoA Port, value from 1 to 65535, default is 3799"
                          },
                          "fast_dot1x_timers": {
                            "type": "boolean",
                            "default": false
                          },
                          "network": {
                            "type": "string",
                            "description": "Use `network`or `source_ip`. Which network the RADIUS server resides, if there's static IP for this network, we'd use it as source-ip"
                          },
                          "source_ip": {
                            "type": "string",
                            "description": "Use `network`or `source_ip`"
                          }
                        },
                        "description": "Junos Radius config"
                      },
                      "use_different_radius": {
                        "type": "string"
                      }
                    },
                    "description": "By default, `radius_config` will be used. if a different one has to be used set `use_different_radius"
                  },
                  "remove_existing_configs": {
                    "type": "boolean",
                    "description": "By default, only the configuration generated by Mist is cleaned up during the configuration process. If `true`, all the existing configuration will be removed.",
                    "default": false
                  },
                  "root_password": {
                    "type": "string"
                  },
                  "tacacs": {
                    "title": "tacacs",
                    "type": "object",
                    "properties": {
                      "acct_servers": {
                        "type": "array",
                        "items": {
                          "title": "tacacs_acct_server",
                          "type": "object",
                          "properties": {
                            "host": {
                              "type": "string"
                            },
                            "port": {
                              "type": "string"
                            },
                            "secret": {
                              "type": "string"
                            },
                            "timeout": {
                              "type": "integer",
                              "contentEncoding": "int32",
                              "default": 10
                            }
                          }
                        },
                        "description": ""
                      },
                      "default_role": {
                        "type": "string",
                        "description": "enum: `admin`, `helpdesk`, `none`, `read`"
                      },
                      "enabled": {
                        "type": "boolean"
                      },
                      "network": {
                        "type": "string",
                        "description": "Which network the TACACS server resides"
                      },
                      "tacplus_servers": {
                        "type": "array",
                        "items": {
                          "title": "tacacs_auth_server",
                          "type": "object",
                          "properties": {
                            "host": {
                              "type": "string"
                            },
                            "port": {
                              "type": "string"
                            },
                            "secret": {
                              "type": "string"
                            },
                            "timeout": {
                              "type": "integer",
                              "contentEncoding": "int32",
                              "default": 10
                            }
                          }
                        },
                        "description": ""
                      }
                    }
                  },
                  "use_mxedge_proxy": {
                    "type": "boolean",
                    "description": "To use mxedge as proxy"
                  }
                },
                "description": "Switch settings"
              }
            },
            "additionalProperties": {
              "type": "string"
            },
            "description": "Property key defines the type of matching, value is the string to match. e.g:\n  * `match_name[0:3]`: switch name must match the first 3 letters of the property value\n  * `match_name[2:6]`: switch name must match the property value from the 2nd to the 6th letter\n  * `match_model[0-8]`: switch model must match the first 8 letters of the property value\n  * `match_role`: switch role must match the property value",
            "examples": [
              {
                "match_model": "EX4300",
                "match_name[0:3]": "abc"
              }
            ]
          },
          "description": ""
        }
      },
      "description": "Defines custom switch configuration based on different criteria"
    },
    "switch_mgmt": {
      "type": "object",
      "properties": {
        "ap_affinity_threshold": {
          "type": "integer",
          "description": "AP_affinity_threshold ap_affinity_threshold can be added as a field under site/setting. By default, this value is set to 12. If the field is set in both site/setting and org/setting, the value from site/setting will be used.",
          "contentEncoding": "int32",
          "default": 10
        },
        "cli_banner": {
          "type": "string",
          "description": "Set Banners for switches. Allows markup formatting",
          "examples": [
            "\\t\\tWELCOME!"
          ]
        },
        "cli_idle_timeout": {
          "maximum": 60.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "Sets timeout for switches",
          "contentEncoding": "int32"
        },
        "config_revert_timer": {
          "maximum": 30.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "Rollback timer for commit confirmed",
          "contentEncoding": "int32",
          "default": 10
        },
        "dhcp_option_fqdn": {
          "type": "boolean",
          "description": "Enable to provide the FQDN with DHCP option 81",
          "default": false
        },
        "disable_oob_down_alarm": {
          "type": "boolean"
        },
        "fips_enabled": {
          "type": "boolean",
          "default": false
        },
        "local_accounts": {
          "type": "object",
          "additionalProperties": {
            "title": "config_switch_local_accounts_user",
            "type": "object",
            "properties": {
              "password": {
                "type": "string",
                "examples": [
                  "Juniper123"
                ]
              },
              "role": {
                "type": "string",
                "description": "enum: `admin`, `helpdesk`, `none`, `read`"
              }
            }
          },
          "description": "Property key is the user name. For Local user authentication"
        },
        "mxedge_proxy_host": {
          "type": "string",
          "description": "IP Address or FQDN of the Mist Edge used to proxy the switch management traffic to the Mist Cloud"
        },
        "mxedge_proxy_port": {
          "type": "object",
          "description": "Mist Edge port used to proxy the switch management traffic to the Mist Cloud. Value in range 1-65535"
        },
        "protect_re": {
          "type": "object",
          "properties": {
            "allowed_services": {
              "type": "array",
              "items": {
                "title": "protect_re_allowed_service",
                "enum": [
                  "icmp",
                  "ssh"
                ],
                "type": "string",
                "description": "enum: `icmp`, `ssh`"
              },
              "description": "Optionally, services we'll allow",
              "examples": [
                [
                  "icmp",
                  "ssh"
                ]
              ]
            },
            "custom": {
              "type": "array",
              "items": {
                "title": "protect_re_custom",
                "type": "object",
                "properties": {
                  "port_range": {
                    "type": "string",
                    "description": "Matched dst port, \"0\" means any",
                    "default": "0",
                    "examples": [
                      "80,1035-1040"
                    ]
                  },
                  "protocol": {
                    "type": "string",
                    "description": "enum: `any`, `icmp`, `tcp`, `udp`"
                  },
                  "subnets": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": ""
                  }
                },
                "description": "Custom acls"
              },
              "description": ""
            },
            "enabled": {
              "type": "boolean",
              "description": "When enabled, all traffic that is not essential to our operation will be dropped\ne.g. ntp / dns / traffic to mist will be allowed by default\n     if dhcpd is enabled, we'll make sure it works",
              "default": false
            },
            "hit_count": {
              "type": "boolean",
              "description": "Whether to enable hit count for Protect_RE policy",
              "default": false
            },
            "trusted_hosts": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": "host/subnets we'll allow traffic to/from"
            }
          },
          "description": "Restrict inbound-traffic to host\nwhen enabled, all traffic that is not essential to our operation will be dropped \ne.g. ntp / dns / traffic to mist will be allowed by default, if dhcpd is enabled, we'll make sure it works"
        },
        "radius": {
          "type": "object",
          "properties": {
            "enabled": {
              "type": "boolean"
            },
            "radius_config": {
              "type": "object",
              "properties": {
                "acct_immediate_update": {
                  "type": "boolean"
                },
                "acct_interim_interval": {
                  "maximum": 65535.0,
                  "minimum": 0.0,
                  "type": "integer",
                  "description": "How frequently should interim accounting be reported, 60-65535. default is 0 (use one specified in Access-Accept request from RADIUS Server). Very frequent messages can affect the performance of the radius server, 600 and up is recommended when enabled",
                  "contentEncoding": "int32",
                  "default": 0
                },
                "acct_servers": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "title": "radius_acct_server",
                    "required": [
                      "host",
                      "secret"
                    ],
                    "type": "object",
                    "properties": {
                      "host": {
                        "type": "string",
                        "description": "IP/ hostname of RADIUS server",
                        "examples": [
                          "1.2.3.4"
                        ]
                      },
                      "keywrap_enabled": {
                        "type": "boolean"
                      },
                      "keywrap_format": {
                        "type": "string",
                        "description": "enum: `ascii`, `hex`"
                      },
                      "keywrap_kek": {
                        "type": "string",
                        "examples": [
                          "1122334455"
                        ]
                      },
                      "keywrap_mack": {
                        "type": "string",
                        "examples": [
                          "1122334455"
                        ]
                      },
                      "port": {
                        "type": "object",
                        "description": "Radius Auth Port, value from 1 to 65535, default is 1813"
                      },
                      "secret": {
                        "type": "string",
                        "description": "Secret of RADIUS server",
                        "examples": [
                          "testing123"
                        ]
                      }
                    }
                  },
                  "description": ""
                },
                "auth_server_selection": {
                  "type": "string",
                  "description": "enum: `ordered`, `unordered`"
                },
                "auth_servers": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "title": "radius_auth_server",
                    "required": [
                      "host",
                      "secret"
                    ],
                    "type": "object",
                    "properties": {
                      "host": {
                        "type": "string",
                        "description": "IP/ hostname of RADIUS server",
                        "examples": [
                          "1.2.3.4"
                        ]
                      },
                      "keywrap_enabled": {
                        "type": "boolean"
                      },
                      "keywrap_format": {
                        "type": "string",
                        "description": "enum: `ascii`, `hex`"
                      },
                      "keywrap_kek": {
                        "type": "string",
                        "examples": [
                          "1122334455"
                        ]
                      },
                      "keywrap_mack": {
                        "type": "string",
                        "examples": [
                          "1122334455"
                        ]
                      },
                      "port": {
                        "type": "object",
                        "description": "Radius Auth Port, value from 1 to 65535, default is 1812"
                      },
                      "require_message_authenticator": {
                        "type": "boolean",
                        "description": "Whether to require Message-Authenticator in requests",
                        "default": false
                      },
                      "secret": {
                        "type": "string",
                        "description": "Secret of RADIUS server",
                        "examples": [
                          "testing123"
                        ]
                      }
                    },
                    "description": "Authentication Server"
                  },
                  "description": ""
                },
                "auth_servers_retries": {
                  "type": "integer",
                  "description": "Radius auth session retries",
                  "contentEncoding": "int32",
                  "default": 3
                },
                "auth_servers_timeout": {
                  "type": "integer",
                  "description": "Radius auth session timeout",
                  "contentEncoding": "int32",
                  "default": 5
                },
                "coa_enabled": {
                  "type": "boolean",
                  "default": false
                },
                "coa_port": {
                  "type": "object",
                  "description": "Radius CoA Port, value from 1 to 65535, default is 3799"
                },
                "fast_dot1x_timers": {
                  "type": "boolean",
                  "default": false
                },
                "network": {
                  "type": "string",
                  "description": "Use `network`or `source_ip`. Which network the RADIUS server resides, if there's static IP for this network, we'd use it as source-ip"
                },
                "source_ip": {
                  "type": "string",
                  "description": "Use `network`or `source_ip`"
                }
              },
              "description": "Junos Radius config"
            },
            "use_different_radius": {
              "type": "string"
            }
          },
          "description": "By default, `radius_config` will be used. if a different one has to be used set `use_different_radius"
        },
        "remove_existing_configs": {
          "type": "boolean",
          "description": "By default, only the configuration generated by Mist is cleaned up during the configuration process. If `true`, all the existing configuration will be removed.",
          "default": false
        },
        "root_password": {
          "type": "string"
        },
        "tacacs": {
          "title": "tacacs",
          "type": "object",
          "properties": {
            "acct_servers": {
              "type": "array",
              "items": {
                "title": "tacacs_acct_server",
                "type": "object",
                "properties": {
                  "host": {
                    "type": "string"
                  },
                  "port": {
                    "type": "string"
                  },
                  "secret": {
                    "type": "string"
                  },
                  "timeout": {
                    "type": "integer",
                    "contentEncoding": "int32",
                    "default": 10
                  }
                }
              },
              "description": ""
            },
            "default_role": {
              "type": "string",
              "description": "enum: `admin`, `helpdesk`, `none`, `read`"
            },
            "enabled": {
              "type": "boolean"
            },
            "network": {
              "type": "string",
              "description": "Which network the TACACS server resides"
            },
            "tacplus_servers": {
              "type": "array",
              "items": {
                "title": "tacacs_auth_server",
                "type": "object",
                "properties": {
                  "host": {
                    "type": "string"
                  },
                  "port": {
                    "type": "string"
                  },
                  "secret": {
                    "type": "string"
                  },
                  "timeout": {
                    "type": "integer",
                    "contentEncoding": "int32",
                    "default": 10
                  }
                }
              },
              "description": ""
            }
          }
        },
        "use_mxedge_proxy": {
          "type": "boolean",
          "description": "To use mxedge as proxy"
        }
      },
      "description": "Switch settings"
    },
    "vrf_config": {
      "title": "vrf_config",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "Whether to enable VRF (when supported on the device)"
        }
      }
    },
    "vrf_instances": {
      "type": "object",
      "additionalProperties": {
        "title": "switch_vrf_instance",
        "type": "object",
        "properties": {
          "aggregate_routes": {
            "type": "object",
            "additionalProperties": {
              "title": "aggregate_route",
              "type": "object",
              "properties": {
                "discard": {
                  "type": "boolean",
                  "default": false
                },
                "metric": {
                  "maximum": 4294967295.0,
                  "minimum": 0.0,
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32"
                },
                "preference": {
                  "maximum": 4294967295.0,
                  "minimum": 0.0,
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32"
                }
              }
            },
            "description": "Property key is the destination subnet (e.g. \"172.16.3.0/24\")",
            "examples": [
              {
                "172.16.3.0/24": {
                  "discard": false,
                  "metric": null,
                  "preference": 30
                }
              }
            ]
          },
          "aggregate_routes6": {
            "type": "object",
            "additionalProperties": {
              "title": "aggregate_route",
              "type": "object",
              "properties": {
                "discard": {
                  "type": "boolean",
                  "default": false
                },
                "metric": {
                  "maximum": 4294967295.0,
                  "minimum": 0.0,
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32"
                },
                "preference": {
                  "maximum": 4294967295.0,
                  "minimum": 0.0,
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32"
                }
              }
            },
            "description": "Property key is the destination subnet (e.g. \"2a02:1234:420a:10c9::/64\")",
            "examples": [
              {
                "2a02:1234:420a:10c9::/64": {
                  "discard": false,
                  "metric": null,
                  "preference": 30
                }
              }
            ]
          },
          "evpn_auto_loopback_subnet": {
            "type": "string",
            "examples": [
              "100.101.0.0/24"
            ]
          },
          "evpn_auto_loopback_subnet6": {
            "type": "string"
          },
          "extra_routes": {
            "type": "object",
            "additionalProperties": {
              "title": "vrf_extra_route",
              "type": "object",
              "properties": {
                "via": {
                  "type": "string",
                  "description": "Next-hop address"
                }
              }
            },
            "description": "Property key is the destination CIDR (e.g. \"10.0.0.0/8\")",
            "examples": [
              {
                "0.0.0.0/0": {
                  "via": "192.168.1.10"
                }
              }
            ]
          },
          "extra_routes6": {
            "type": "object",
            "additionalProperties": {
              "title": "vrf_extra_route",
              "type": "object",
              "properties": {
                "via": {
                  "type": "string",
                  "description": "Next-hop address"
                }
              }
            },
            "description": "Property key is the destination CIDR (e.g. \"2a02:1234:420a:10c9::/64\")",
            "examples": [
              {
                "2a02:1234:420a:10c9::/64": {
                  "via": "2a02:1234:200a::100"
                }
              }
            ]
          },
          "networks": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          }
        },
        "examples": [
          {
            "extra_routes": {
              "0.0.0.0/0": {
                "via": "192.168.31.1"
              }
            },
            "networks": [
              "guest"
            ]
          }
        ]
      },
      "description": "Property key is the network name",
      "examples": [
        {
          "guest": {
            "extra_routes": {
              "0.0.0.0/0": {
                "via": "192.168.31.1"
              }
            },
            "networks": [
              "guest"
            ]
          }
        }
      ]
    }
  },
  "description": "Network Template"
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

`mistapi.api.v1.orgs.network_templates.updateOrgNetworkTemplate()`

## Usage Context

Updates an existing network template (switch configuration template).

## Gotchas

- Changes propagate to all sites using this template.

## Related Endpoints

- [GET_orgs_org_id_networktemplates_networktemplate_id.md](GET_orgs_org_id_networktemplates_networktemplate_id.md) — Get template
- [POST_orgs_org_id_networktemplates.md](POST_orgs_org_id_networktemplates.md) — Create template

## MistHelper Notes

Not currently used by MistHelper directly.
