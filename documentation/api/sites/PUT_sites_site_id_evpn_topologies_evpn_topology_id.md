# updateSiteEvpnTopology

> updateSiteEvpnTopology

## HTTP

`PUT /api/v1/sites/{site_id}/evpn_topologies/{evpn_topology_id}`

## Description

Update the EVPN Topology

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| evpn_topology_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
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
    },
    "switch_configs": {
      "type": "object",
      "additionalProperties": {
        "title": "evpn_topology_switch_config",
        "type": "object",
        "properties": {
          "dhcpd_config": {
            "title": "evpn_topology_switch_config_dhcpd_config",
            "type": "object",
            "properties": {
              "enabled": {
                "type": "boolean",
                "description": "If DHCPD is enabled on the switch"
              }
            }
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
          "other_ip_configs": {
            "type": "object",
            "additionalProperties": {
              "title": "junos_other_ip_config",
              "type": "object",
              "properties": {
                "evpn_anycast": {
                  "type": "boolean",
                  "description": "For EVPN, if anycast is desired",
                  "default": false
                },
                "ip": {
                  "type": "string",
                  "description": "Required if `type`==`static`",
                  "examples": [
                    "10.3.3.1"
                  ]
                },
                "ip6": {
                  "type": "string",
                  "description": "Required if `type6`==`static`",
                  "examples": [
                    "fdad:b0bc:f29e::3d16"
                  ]
                },
                "netmask": {
                  "type": "string",
                  "description": "Optional, `subnet` from `network` definition will be used if defined",
                  "examples": [
                    "255.255.255.0"
                  ]
                },
                "netmask6": {
                  "type": "string",
                  "description": "Optional, `subnet` from `network` definition will be used if defined",
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
                  "description": "enum: `autoconf`, `dhcp`, `disabled`, `static`"
                }
              },
              "description": "Optional, if it's required to have switch's L3 presence on a network/vlan"
            },
            "description": "Additional IP Addresses configured on the switch. Property key is the port network name"
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
          "router_id": {
            "type": "string",
            "description": "Used for OSPF / BGP / EVPN",
            "examples": [
              "10.2.1.10"
            ]
          },
          "vrf_config": {
            "title": "evpn_topology_switch_config_vrf_config",
            "type": "object",
            "properties": {
              "enabled": {
                "type": "boolean",
                "description": "Whether to enable VRF (when supported on the device)"
              }
            }
          }
        }
      },
      "description": "Property key is the switch mac"
    },
    "switches": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "evpn_topology_switch",
        "required": [
          "mac",
          "role"
        ],
        "type": "object",
        "properties": {
          "config": {
            "title": "evpn_topology_switch_config",
            "type": "object",
            "properties": {
              "dhcpd_config": {
                "title": "evpn_topology_switch_config_dhcpd_config",
                "type": "object",
                "properties": {
                  "enabled": {
                    "type": "boolean",
                    "description": "If DHCPD is enabled on the switch"
                  }
                }
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
              "other_ip_configs": {
                "type": "object",
                "additionalProperties": {
                  "title": "junos_other_ip_config",
                  "type": "object",
                  "properties": {
                    "evpn_anycast": {
                      "type": "boolean",
                      "description": "For EVPN, if anycast is desired",
                      "default": false
                    },
                    "ip": {
                      "type": "string",
                      "description": "Required if `type`==`static`",
                      "examples": [
                        "10.3.3.1"
                      ]
                    },
                    "ip6": {
                      "type": "string",
                      "description": "Required if `type6`==`static`",
                      "examples": [
                        "fdad:b0bc:f29e::3d16"
                      ]
                    },
                    "netmask": {
                      "type": "string",
                      "description": "Optional, `subnet` from `network` definition will be used if defined",
                      "examples": [
                        "255.255.255.0"
                      ]
                    },
                    "netmask6": {
                      "type": "string",
                      "description": "Optional, `subnet` from `network` definition will be used if defined",
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
                      "description": "enum: `autoconf`, `dhcp`, `disabled`, `static`"
                    }
                  },
                  "description": "Optional, if it's required to have switch's L3 presence on a network/vlan"
                },
                "description": "Additional IP Addresses configured on the switch. Property key is the port network name"
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
              "router_id": {
                "type": "string",
                "description": "Used for OSPF / BGP / EVPN",
                "examples": [
                  "10.2.1.10"
                ]
              },
              "vrf_config": {
                "title": "evpn_topology_switch_config_vrf_config",
                "type": "object",
                "properties": {
                  "enabled": {
                    "type": "boolean",
                    "description": "Whether to enable VRF (when supported on the device)"
                  }
                }
              }
            }
          },
          "deviceprofile_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "6a1deab1-96df-4fa2-8455-d5253f943d06"
            ]
          },
          "downlink_ips": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "readOnly": true
          },
          "downlinks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "examples": [
              [
                "5c5b35000005",
                "5c5b35000006"
              ]
            ]
          },
          "esilaglinks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "examples": [
              [
                "5c5b35000005",
                "5c5b35000006"
              ]
            ]
          },
          "evpn_id": {
            "minimum": 1.0,
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "mac": {
            "minLength": 1,
            "type": "string",
            "examples": [
              "5c5b35000003"
            ]
          },
          "model": {
            "type": "string",
            "readOnly": true,
            "examples": [
              "QFX10002-36Q"
            ]
          },
          "pod": {
            "maximum": 255.0,
            "minimum": 1.0,
            "type": "integer",
            "description": "Optionally, for distribution / access / esilag-access, they can be placed into different pods. e.g. \n  * for CLOS, to group dist / access switches into pods\n  * for ERB/CRB, to group dist / esilag-access into pods",
            "contentEncoding": "int32",
            "default": 1
          },
          "pods": {
            "type": "array",
            "items": {
              "type": "integer",
              "contentEncoding": "int32"
            },
            "description": "By default, core switches are assumed to be connecting all pods. \nif you want to limit the pods, you can specify pods."
          },
          "role": {
            "type": "string",
            "description": "use `role`==`none` to remove a switch from the topology. enum: `access`, `collapsed-core`, `core`, `distribution`, `esilag-access`, `none`"
          },
          "router_id": {
            "type": "string",
            "readOnly": true,
            "examples": [
              "172.16.254.4"
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
          "suggested_downlinks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "readOnly": true,
            "examples": [
              [
                "5c5b35000005",
                "5c5b35000006"
              ]
            ]
          },
          "suggested_esilaglinks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "readOnly": true,
            "examples": [
              [
                "5c5b35000005",
                "5c5b35000006"
              ]
            ]
          },
          "suggested_uplinks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "readOnly": true,
            "examples": [
              [
                "5c5b35000005",
                "5c5b35000006"
              ]
            ]
          },
          "uplinks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "examples": [
              [
                "5c5b35000005",
                "5c5b35000006"
              ]
            ]
          }
        }
      },
      "description": ""
    }
  },
  "required": [
    "switches"
  ]
}
```

## Response

### 200

Example response

```json
{
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
    },
    "switch_configs": {
      "type": "object",
      "additionalProperties": {
        "title": "evpn_topology_switch_config",
        "type": "object",
        "properties": {
          "dhcpd_config": {
            "title": "evpn_topology_switch_config_dhcpd_config",
            "type": "object",
            "properties": {
              "enabled": {
                "type": "boolean",
                "description": "If DHCPD is enabled on the switch"
              }
            }
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
          "other_ip_configs": {
            "type": "object",
            "additionalProperties": {
              "title": "junos_other_ip_config",
              "type": "object",
              "properties": {
                "evpn_anycast": {
                  "type": "boolean",
                  "description": "For EVPN, if anycast is desired",
                  "default": false
                },
                "ip": {
                  "type": "string",
                  "description": "Required if `type`==`static`",
                  "examples": [
                    "10.3.3.1"
                  ]
                },
                "ip6": {
                  "type": "string",
                  "description": "Required if `type6`==`static`",
                  "examples": [
                    "fdad:b0bc:f29e::3d16"
                  ]
                },
                "netmask": {
                  "type": "string",
                  "description": "Optional, `subnet` from `network` definition will be used if defined",
                  "examples": [
                    "255.255.255.0"
                  ]
                },
                "netmask6": {
                  "type": "string",
                  "description": "Optional, `subnet` from `network` definition will be used if defined",
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
                  "description": "enum: `autoconf`, `dhcp`, `disabled`, `static`"
                }
              },
              "description": "Optional, if it's required to have switch's L3 presence on a network/vlan"
            },
            "description": "Additional IP Addresses configured on the switch. Property key is the port network name"
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
          "router_id": {
            "type": "string",
            "description": "Used for OSPF / BGP / EVPN",
            "examples": [
              "10.2.1.10"
            ]
          },
          "vrf_config": {
            "title": "evpn_topology_switch_config_vrf_config",
            "type": "object",
            "properties": {
              "enabled": {
                "type": "boolean",
                "description": "Whether to enable VRF (when supported on the device)"
              }
            }
          }
        }
      },
      "description": "Property key is the switch mac"
    },
    "switches": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "evpn_topology_switch",
        "required": [
          "mac",
          "role"
        ],
        "type": "object",
        "properties": {
          "config": {
            "title": "evpn_topology_switch_config",
            "type": "object",
            "properties": {
              "dhcpd_config": {
                "title": "evpn_topology_switch_config_dhcpd_config",
                "type": "object",
                "properties": {
                  "enabled": {
                    "type": "boolean",
                    "description": "If DHCPD is enabled on the switch"
                  }
                }
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
              "other_ip_configs": {
                "type": "object",
                "additionalProperties": {
                  "title": "junos_other_ip_config",
                  "type": "object",
                  "properties": {
                    "evpn_anycast": {
                      "type": "boolean",
                      "description": "For EVPN, if anycast is desired",
                      "default": false
                    },
                    "ip": {
                      "type": "string",
                      "description": "Required if `type`==`static`",
                      "examples": [
                        "10.3.3.1"
                      ]
                    },
                    "ip6": {
                      "type": "string",
                      "description": "Required if `type6`==`static`",
                      "examples": [
                        "fdad:b0bc:f29e::3d16"
                      ]
                    },
                    "netmask": {
                      "type": "string",
                      "description": "Optional, `subnet` from `network` definition will be used if defined",
                      "examples": [
                        "255.255.255.0"
                      ]
                    },
                    "netmask6": {
                      "type": "string",
                      "description": "Optional, `subnet` from `network` definition will be used if defined",
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
                      "description": "enum: `autoconf`, `dhcp`, `disabled`, `static`"
                    }
                  },
                  "description": "Optional, if it's required to have switch's L3 presence on a network/vlan"
                },
                "description": "Additional IP Addresses configured on the switch. Property key is the port network name"
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
              "router_id": {
                "type": "string",
                "description": "Used for OSPF / BGP / EVPN",
                "examples": [
                  "10.2.1.10"
                ]
              },
              "vrf_config": {
                "title": "evpn_topology_switch_config_vrf_config",
                "type": "object",
                "properties": {
                  "enabled": {
                    "type": "boolean",
                    "description": "Whether to enable VRF (when supported on the device)"
                  }
                }
              }
            }
          },
          "deviceprofile_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "6a1deab1-96df-4fa2-8455-d5253f943d06"
            ]
          },
          "downlink_ips": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "readOnly": true
          },
          "downlinks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "examples": [
              [
                "5c5b35000005",
                "5c5b35000006"
              ]
            ]
          },
          "esilaglinks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "examples": [
              [
                "5c5b35000005",
                "5c5b35000006"
              ]
            ]
          },
          "evpn_id": {
            "minimum": 1.0,
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "mac": {
            "minLength": 1,
            "type": "string",
            "examples": [
              "5c5b35000003"
            ]
          },
          "model": {
            "type": "string",
            "readOnly": true,
            "examples": [
              "QFX10002-36Q"
            ]
          },
          "pod": {
            "maximum": 255.0,
            "minimum": 1.0,
            "type": "integer",
            "description": "Optionally, for distribution / access / esilag-access, they can be placed into different pods. e.g. \n  * for CLOS, to group dist / access switches into pods\n  * for ERB/CRB, to group dist / esilag-access into pods",
            "contentEncoding": "int32",
            "default": 1
          },
          "pods": {
            "type": "array",
            "items": {
              "type": "integer",
              "contentEncoding": "int32"
            },
            "description": "By default, core switches are assumed to be connecting all pods. \nif you want to limit the pods, you can specify pods."
          },
          "role": {
            "type": "string",
            "description": "use `role`==`none` to remove a switch from the topology. enum: `access`, `collapsed-core`, `core`, `distribution`, `esilag-access`, `none`"
          },
          "router_id": {
            "type": "string",
            "readOnly": true,
            "examples": [
              "172.16.254.4"
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
          "suggested_downlinks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "readOnly": true,
            "examples": [
              [
                "5c5b35000005",
                "5c5b35000006"
              ]
            ]
          },
          "suggested_esilaglinks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "readOnly": true,
            "examples": [
              [
                "5c5b35000005",
                "5c5b35000006"
              ]
            ]
          },
          "suggested_uplinks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "readOnly": true,
            "examples": [
              [
                "5c5b35000005",
                "5c5b35000006"
              ]
            ]
          },
          "uplinks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "examples": [
              [
                "5c5b35000005",
                "5c5b35000006"
              ]
            ]
          }
        }
      },
      "description": ""
    }
  },
  "required": [
    "switches"
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

`mistapi.api.v1.sites.evpn_topologies.updateSiteEvpnTopology()`

## Usage Context

Updates an EVPN topology configuration at a site.

## Gotchas

- Topology changes may disrupt network traffic. Apply during maintenance windows.

## Related Endpoints

- [POST_sites_site_id_evpn_topologies.md](POST_sites_site_id_evpn_topologies.md) — Create topology
- [GET_sites_site_id_evpn_topologies.md](GET_sites_site_id_evpn_topologies.md) — List topologies

## MistHelper Notes

Not currently used by MistHelper directly.
