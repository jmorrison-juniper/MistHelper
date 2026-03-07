# getOrgGatewayTemplate

> getOrgGatewayTemplate

## HTTP

`GET /api/v1/orgs/{org_id}/gatewaytemplates/{gatewaytemplate_id}`

## Description

Get Organization Gateway Template details

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| gatewaytemplate_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
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
        "title": "bgp_config",
        "required": [
          "via"
        ],
        "type": "object",
        "properties": {
          "auth_key": {
            "type": "string",
            "description": "Optional if `via`==`lan`, `via`==`tunnel` or `via`==`wan`"
          },
          "bfd_minimum_interval": {
            "maximum": 255000.0,
            "minimum": 1.0,
            "type": [
              "integer",
              "null"
            ],
            "description": "Optional if `via`==`lan`, `via`==`tunnel` or `via`==`wan`, when bfd_multiplier is configured alone. Default:\n  * 1000 if `type`==`external`\n  * 350 `type`==`internal`",
            "contentEncoding": "int32",
            "default": 350
          },
          "bfd_multiplier": {
            "maximum": 255.0,
            "minimum": 1.0,
            "type": [
              "integer",
              "null"
            ],
            "description": "Optional if `via`==`lan`, `via`==`tunnel` or `via`==`wan`, when bfd_minimum_interval_is_configured alone",
            "contentEncoding": "int32",
            "default": 3
          },
          "disable_bfd": {
            "type": "boolean",
            "description": "Optional if `via`==`lan`, `via`==`tunnel` or `via`==`wan`. BFD provides faster path failure detection and is enabled by default",
            "default": false
          },
          "export": {
            "type": "string"
          },
          "export_policy": {
            "type": "string",
            "description": "Default export policies if no per-neighbor policies defined"
          },
          "extended_v4_nexthop": {
            "type": "boolean",
            "description": "Optional if `via`==`lan`, `via`==`tunnel` or `via`==`wan`. By default, either inet/net6 unicast depending on neighbor IP family (v4 or v6). For v6 neighbors, to exchange v4 nexthop, which allows dual-stack support, enable this"
          },
          "graceful_restart_time": {
            "maximum": 4095.0,
            "minimum": 0.0,
            "type": "integer",
            "description": "Optional if `via`==`lan`, `via`==`tunnel` or `via`==`wan`. `0` means disable",
            "contentEncoding": "int32",
            "default": 0
          },
          "hold_time": {
            "maximum": 65535.0,
            "minimum": 0.0,
            "type": "integer",
            "description": "Optional if `via`==`lan`, `via`==`tunnel` or `via`==`wan`. Default is 90.",
            "contentEncoding": "int32",
            "default": 90
          },
          "import": {
            "type": "string"
          },
          "import_policy": {
            "type": "string",
            "description": "Optional if `via`==`lan`, `via`==`tunnel` or `via`==`wan`. Default import policies if no per-neighbor policies defined"
          },
          "local_as": {
            "type": "object",
            "description": "Required if `via`==`lan`, `via`==`tunnel` or `via`==`wan`. BGP AS, value in range 1-4294967295"
          },
          "neighbor_as": {
            "type": "object",
            "description": "BGP AS, value in range 1-4294967294. Can be a Variable (e.g. `{{bgp_as}}` )"
          },
          "neighbors": {
            "type": "object",
            "additionalProperties": {
              "title": "bgp_config_neighbors",
              "required": [
                "neighbor_as"
              ],
              "type": "object",
              "properties": {
                "disabled": {
                  "type": "boolean",
                  "description": "If true, the BGP session to this neighbor will be administratively disabled/shutdown",
                  "default": false
                },
                "export_policy": {
                  "type": "string"
                },
                "hold_time": {
                  "maximum": 65535.0,
                  "minimum": 0.0,
                  "type": "integer",
                  "contentEncoding": "int32",
                  "default": 90
                },
                "import_policy": {
                  "type": "string"
                },
                "multihop_ttl": {
                  "maximum": 255.0,
                  "minimum": 0.0,
                  "type": "integer",
                  "description": "Assuming BGP neighbor is directly connected",
                  "contentEncoding": "int32"
                },
                "neighbor_as": {
                  "type": "object",
                  "description": "BGP AS, value in range 1-4294967294. Can be a Variable (e.g. `{{bgp_as}}` )"
                }
              }
            },
            "description": "Required if `via`==`lan`, `via`==`tunnel` or `via`==`wan`. If per-neighbor as is desired. Property key is the neighbor address"
          },
          "networks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Optional if `via`==`lan`. List of networks where we expect BGP neighbor to connect to/from"
          },
          "no_private_as": {
            "type": "boolean",
            "description": "Optional if `via`==`lan`, `via`==`tunnel` or `via`==`wan`. If true, we will not advertise private ASNs (AS 64512-65534) to this neighbor",
            "default": false
          },
          "no_readvertise_to_overlay": {
            "type": "boolean",
            "description": "Optional if `via`==`lan`, `via`==`tunnel` or `via`==`wan`. By default, we'll re-advertise all learned BGP routers toward overlay",
            "default": false
          },
          "tunnel_name": {
            "type": "string",
            "description": "Optional if `via`==`tunnel`"
          },
          "type": {
            "type": "string",
            "description": "Required if `via`==`lan`, `via`==`tunnel` or `via`==`wan`. enum: `external`, `internal`"
          },
          "via": {
            "type": "string",
            "description": "enum: `lan`, `tunnel`, `vpn`, `wan`"
          },
          "vpn_name": {
            "type": "string",
            "description": "Optional if `via`==`vpn`"
          },
          "wan_name": {
            "type": "string",
            "description": "Optional if `via`==`wan`"
          }
        },
        "description": "BFD is enabled when either bfd_minimum_interval or bfd_multiplier is configured"
      }
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "dhcpd_config": {
      "title": "dhcpd_config",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "If set to `false`, disable the DHCP server",
          "default": true
        }
      },
      "additionalProperties": {
        "title": "dhcpd_config_property",
        "type": "object",
        "properties": {
          "dns_servers": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "If `type`==`local` or `type6`==`local` - optional, if not defined, system one will be used",
            "examples": [
              [
                "8.8.8.8",
                "4.4.4.4",
                "2001:4860:4860::8888"
              ]
            ]
          },
          "dns_suffix": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "If `type`==`local` or `type6`==`local` - optional, if not defined, system one will be used",
            "examples": [
              [
                ".mist.local",
                ".mist.com"
              ]
            ]
          },
          "fixed_bindings": {
            "type": "object",
            "additionalProperties": {
              "title": "dhcpd_config_fixed_binding",
              "type": "object",
              "properties": {
                "ip": {
                  "type": "string",
                  "examples": [
                    "192.168.70.35"
                  ]
                },
                "ip6": {
                  "type": "string",
                  "examples": [
                    "2607:f8b0:4005:808::2"
                  ]
                },
                "name": {
                  "type": "string"
                }
              }
            },
            "description": "If `type`==`local` or `type6`==`local`. Property key is the MAC Address. Format is `[0-9a-f]{12}` (e.g. \"5684dae9ac8b\")",
            "examples": [
              {
                "5684dae9ac8b": {
                  "ip": "192.168.70.35",
                  "name": "John"
                }
              }
            ]
          },
          "gateway": {
            "type": "string",
            "description": "If `type`==`local` - optional, `ip` will be used if not provided",
            "examples": [
              "192.168.70.1"
            ]
          },
          "ip6_end": {
            "type": "string",
            "description": "If `type6`==`local`",
            "examples": [
              "2607:f8b0:4005:808::ff"
            ]
          },
          "ip6_start": {
            "type": "string",
            "description": "If `type6`==`local`",
            "examples": [
              "2607:f8b0:4005:808::2"
            ]
          },
          "ip_end": {
            "type": "string",
            "description": "If `type`==`local`",
            "examples": [
              "192.168.70.200"
            ]
          },
          "ip_start": {
            "type": "string",
            "description": "If `type`==`local`",
            "examples": [
              "192.168.70.100"
            ]
          },
          "lease_time": {
            "maximum": 604800.0,
            "minimum": 3600.0,
            "type": "integer",
            "description": "In seconds, lease time has to be between 3600 [1hr] - 604800 [1 week], default is 86400 [1 day]",
            "contentEncoding": "int32",
            "default": 86400
          },
          "options": {
            "type": "object",
            "additionalProperties": {
              "title": "dhcpd_config_option",
              "type": "object",
              "properties": {
                "type": {
                  "type": "string",
                  "description": "enum: `boolean`, `hex`, `int16`, `int32`, `ip`, `string`, `uint16`, `uint32`"
                },
                "value": {
                  "type": "string"
                }
              }
            },
            "description": "If `type`==`local` or `type6`==`local`. Property key is the DHCP option number"
          },
          "server_id_override": {
            "type": "boolean",
            "description": "`server_id_override`==`true` means the device, when acts as DHCP relay and forwards DHCP responses from DHCP server to clients, \nshould overwrite the Sever Identifier option (i.e. DHCP option 54) in DHCP responses with its own IP address.",
            "default": false
          },
          "servers": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "If `type`==`relay`",
            "examples": [
              [
                "11.2.3.4"
              ]
            ]
          },
          "serversv6": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "If `type6`==`relay`",
            "examples": [
              [
                "2607:f8b0:4005:808::64"
              ]
            ]
          },
          "type": {
            "type": "string",
            "description": "enum: `local` (DHCP Server), `none`, `relay` (DHCP Relay)"
          },
          "type6": {
            "type": "string",
            "description": "enum: `local` (DHCP Server), `none`, `relay` (DHCP Relay)"
          },
          "vendor_encapsulated": {
            "type": "object",
            "additionalProperties": {
              "title": "dhcpd_config_vendor_option",
              "type": "object",
              "properties": {
                "type": {
                  "type": "string",
                  "description": "enum: `boolean`, `hex`, `int16`, `int32`, `ip`, `string`, `uint16`, `uint32`"
                },
                "value": {
                  "type": "string"
                }
              }
            },
            "description": "If `type`==`local` or `type6`==`local`. Property key is <enterprise number>:<sub option code>, with\n  * enterprise number: 1-65535 (https://www.iana.org/assignments/enterprise-numbers/enterprise-numbers)\n  * sub option code: 1-255, sub-option code"
          }
        }
      }
    },
    "dnsOverride": {
      "type": "boolean",
      "default": false
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
        "title": "gateway_extra_route",
        "type": "object",
        "properties": {
          "via": {
            "type": "string"
          }
        }
      },
      "description": "Property key is the destination CIDR (e.g. \"10.0.0.0/8\"), the destination Network name or a variable (e.g. \"{{myvar}}\")"
    },
    "extra_routes6": {
      "type": "object",
      "additionalProperties": {
        "title": "gateway_extra_route",
        "type": "object",
        "properties": {
          "via": {
            "type": "string"
          }
        }
      },
      "description": "Property key is the destination CIDR (e.g. \"2a02:1234:420a:10c9::/64\"), the destination Network name or a variable (e.g. \"{{myvar}}\")",
      "examples": [
        {
          "2a02:1234:420a:10c9::/64": {
            "via": "2a02:1234:200a::100"
          }
        }
      ]
    },
    "gateway_matching": {
      "type": "object",
      "properties": {
        "enable": {
          "type": "boolean"
        },
        "rules": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "title": "gateway_matching_rule",
            "type": "object",
            "properties": {
              "additional_config_cmds": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "additional CLI commands to append to the generated Junos config. **Note**: no check is done"
              },
              "name": {
                "type": "string"
              },
              "port_config": {
                "type": "object",
                "additionalProperties": {
                  "title": "gateway_port_config",
                  "required": [
                    "usage"
                  ],
                  "type": "object",
                  "properties": {
                    "ae_disable_lacp": {
                      "type": "boolean",
                      "description": "If `aggregated`==`true`. To disable LCP support for the AE interface",
                      "default": false
                    },
                    "ae_idx": {
                      "type": [
                        "string",
                        "null"
                      ],
                      "description": "If `aggregated`==`true`. Users could force to use the designated AE name (must be an integer between 0 and 127)"
                    },
                    "ae_lacp_force_up": {
                      "type": "boolean",
                      "description": "For SRX only, if `aggregated`==`true`.Sets the state of the interface as UP when the peer has limited LACP capability. Use case: When a device connected to this AE port is ZTPing for the first time, it will not have LACP configured on the other end. **Note:** Turning this on will enable force-up on one of the interfaces in the bundle only",
                      "default": false
                    },
                    "aggregated": {
                      "type": "boolean",
                      "default": false
                    },
                    "critical": {
                      "type": "boolean",
                      "description": "To generate port up/down alarm, set it to true",
                      "default": false
                    },
                    "description": {
                      "type": "string",
                      "description": "Interface Description. Can be a variable (i.e. \"{{myvar}}\")"
                    },
                    "disable_autoneg": {
                      "type": "boolean",
                      "default": false
                    },
                    "disabled": {
                      "type": "boolean",
                      "description": "Port admin up (true) / down (false)",
                      "default": false
                    },
                    "dsl_type": {
                      "type": "string",
                      "description": "if `wan_type`==`dsl`. enum: `adsl`, `vdsl`"
                    },
                    "dsl_vci": {
                      "type": "integer",
                      "description": "If `wan_type`==`dsl`, 16 bit int",
                      "contentEncoding": "int32",
                      "default": 35
                    },
                    "dsl_vpi": {
                      "type": "integer",
                      "description": "If `wan_type`==`dsl`, 8 bit int",
                      "contentEncoding": "int32",
                      "default": 0
                    },
                    "duplex": {
                      "type": "string",
                      "description": "enum: `auto`, `full`, `half`"
                    },
                    "ip_config": {
                      "type": "object",
                      "properties": {
                        "dns": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "description": "Except for out-of_band interface (vme/em0/fxp0)"
                        },
                        "dns_suffix": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "description": "Except for out-of_band interface (vme/em0/fxp0)"
                        },
                        "gateway": {
                          "type": "string",
                          "description": "Except for out-of_band interface (vme/em0/fxp0). Interface Default Gateway IP Address (i.e. \"192.168.1.1\") or a Variable (i.e. \"{{myvar}}\")",
                          "examples": [
                            "192.168.1.1"
                          ]
                        },
                        "gateway6": {
                          "type": "string",
                          "description": "Except for out-of_band interface (vme/em0/fxp0). Interface Default Gateway IPv6 Address (i.e. \"2001:db8::1\") or a Variable (i.e. \"{{myvar}}\")",
                          "examples": [
                            "2001:db8::1"
                          ]
                        },
                        "ip": {
                          "type": "string",
                          "description": "Interface IP Address (i.e. \"192.168.1.8\") or a Variable (i.e. \"{{myvar}}\")",
                          "examples": [
                            "192.168.1.8"
                          ]
                        },
                        "ip6": {
                          "type": "string",
                          "description": "Interface IPv6 Address (i.e. \"2001:db8::123\") or a Variable (i.e. \"{{myvar}}\")",
                          "examples": [
                            "2001:db8::123"
                          ]
                        },
                        "netmask": {
                          "type": "string",
                          "description": "Used only if `subnet` is not specified in `networks`. Interface Netmask (i.e. \"/24\") or a Variable (i.e. \"{{myvar}}\")",
                          "examples": [
                            "/24"
                          ]
                        },
                        "netmask6": {
                          "type": "string",
                          "description": "Used only if `subnet` is not specified in `networks`. Interface IPv6 Netmask (i.e. \"/64\") or a Variable (i.e. \"{{myvar}}\")",
                          "examples": [
                            "/64"
                          ]
                        },
                        "network": {
                          "type": "string",
                          "description": "Optional, the network to be used for mgmt"
                        },
                        "poser_password": {
                          "type": "string",
                          "description": "If `type`==`pppoe`"
                        },
                        "pppoe_auth": {
                          "type": "string",
                          "description": "if `type`==`pppoe`. enum: `chap`, `none`, `pap`"
                        },
                        "pppoe_username": {
                          "type": "string",
                          "description": "If `type`==`pppoe`"
                        },
                        "type": {
                          "type": "string",
                          "description": "enum: `dhcp`, `pppoe`, `static`"
                        },
                        "type6": {
                          "type": "string",
                          "description": "enum: `autoconf`, `dhcp`, `static`"
                        }
                      },
                      "description": "Junos IP Config"
                    },
                    "lte_apn": {
                      "type": "string",
                      "description": "If `wan_type`==`lte`"
                    },
                    "lte_auth": {
                      "type": "string",
                      "description": "if `wan_type`==`lte`. enum: `chap`, `none`, `pap`"
                    },
                    "lte_backup": {
                      "type": "boolean"
                    },
                    "lte_password": {
                      "type": "string",
                      "description": "If `wan_type`==`lte`"
                    },
                    "lte_username": {
                      "type": "string",
                      "description": "If `wan_type`==`lte`"
                    },
                    "mtu": {
                      "type": "integer",
                      "contentEncoding": "int32"
                    },
                    "name": {
                      "type": "string",
                      "description": "Name that we'll use to derive config"
                    },
                    "networks": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "If `usage`==`lan`, name of the [networks]($h/Orgs%20Networks/_overview) to attach to the interface"
                    },
                    "outer_vlan_id": {
                      "type": "integer",
                      "description": "For Q-in-Q",
                      "contentEncoding": "int32"
                    },
                    "poe_disabled": {
                      "type": "boolean",
                      "default": false
                    },
                    "port_network": {
                      "type": "string",
                      "description": "Only for SRX and if `usage`==`lan`, the name of the Network to be used as the Untagged VLAN"
                    },
                    "preserve_dscp": {
                      "type": "boolean",
                      "description": "Whether to preserve dscp when sending traffic over VPN (SSR-only)",
                      "default": true
                    },
                    "redundant": {
                      "type": "boolean",
                      "description": "If HA mode"
                    },
                    "redundant_group": {
                      "maximum": 128.0,
                      "minimum": 1.0,
                      "type": "integer",
                      "description": "If HA mode, SRX Only - support redundancy-group. 1-128 for physical SRX, 1-64 for virtual SRX",
                      "contentEncoding": "int32"
                    },
                    "reth_idx": {
                      "type": "object",
                      "description": "For SRX only and if HA Mode"
                    },
                    "reth_node": {
                      "type": "string",
                      "description": "If HA mode"
                    },
                    "reth_nodes": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "SSR only - supporting vlan-based redundancy (matching the size of `networks`)",
                      "examples": [
                        [
                          "node0",
                          "node1"
                        ]
                      ]
                    },
                    "speed": {
                      "type": "string",
                      "default": "auto",
                      "examples": [
                        "1g"
                      ]
                    },
                    "ssr_no_virtual_mac": {
                      "type": "boolean",
                      "description": "When SSR is running as VM, this is required on certain hosting platforms",
                      "default": false
                    },
                    "svr_port_range": {
                      "type": "string",
                      "description": "For SSR only",
                      "default": "none",
                      "examples": [
                        "60000-60005"
                      ]
                    },
                    "traffic_shaping": {
                      "title": "gateway_traffic_shaping",
                      "type": "object",
                      "properties": {
                        "class_percentages": {
                          "type": "array",
                          "items": {
                            "type": "integer",
                            "contentEncoding": "int32"
                          },
                          "description": "percentages for different class of traffic: high / medium / low / best-effort. Sum must be equal to 100"
                        },
                        "enabled": {
                          "type": "boolean",
                          "default": false
                        },
                        "max_tx_kbps": {
                          "type": "integer",
                          "description": "Interface Transmit Cap in kbps",
                          "contentEncoding": "int32"
                        }
                      }
                    },
                    "usage": {
                      "type": "string",
                      "description": "port usage name. enum: `ha_control`, `ha_data`, `lan`, `wan`"
                    },
                    "vlan_id": {
                      "type": "object",
                      "description": "If WAN interface is on a VLAN. Can be the VLAN ID (i.e. \"10\") or a Variable (i.e. \"{{myvar}}\")"
                    },
                    "vpn_paths": {
                      "type": "object",
                      "additionalProperties": {
                        "title": "gateway_port_vpn_path",
                        "type": "object",
                        "properties": {
                          "bfd_profile": {
                            "type": "string",
                            "description": "Only if the VPN `type`==`hub_spoke`. enum: `broadband`, `lte`"
                          },
                          "bfd_use_tunnel_mode": {
                            "type": "boolean",
                            "description": "Only if the VPN `type`==`hub_spoke`. Whether to use tunnel mode. SSR only",
                            "default": false
                          },
                          "preference": {
                            "type": "integer",
                            "description": "Only if the VPN `type`==`hub_spoke`. For a given VPN, when `path_selection.strategy`==`simple`, the preference for a path (lower is preferred)",
                            "contentEncoding": "int32"
                          },
                          "role": {
                            "type": "string",
                            "description": "If the VPN `type`==`hub_spoke`, enum: `hub`, `spoke`. If the VPN `type`==`mesh`, enum: `mesh`"
                          },
                          "traffic_shaping": {
                            "title": "gateway_traffic_shaping",
                            "type": "object",
                            "properties": {
                              "class_percentages": {
                                "type": "array",
                                "items": {
                                  "type": "integer",
                                  "contentEncoding": "int32"
                                },
                                "description": "percentages for different class of traffic: high / medium / low / best-effort. Sum must be equal to 100"
                              },
                              "enabled": {
                                "type": "boolean",
                                "default": false
                              },
                              "max_tx_kbps": {
                                "type": "integer",
                                "description": "Interface Transmit Cap in kbps",
                                "contentEncoding": "int32"
                              }
                            }
                          }
                        }
                      },
                      "description": "Property key is the VPN name"
                    },
                    "wan_arp_policer": {
                      "type": "string",
                      "description": "Only when `wan_type`==`broadband`. enum: `default`, `max`, `recommended`"
                    },
                    "wan_ext_ip": {
                      "type": "string",
                      "description": "Only if `usage`==`wan`, optional. If spoke should reach this port by a different IP",
                      "examples": [
                        "64.2.4.3"
                      ]
                    },
                    "wan_ext_ip6": {
                      "type": "string",
                      "description": "Only if `usage`==`wan`, optional. If spoke should reach this port by a different IPv6",
                      "examples": [
                        "2601:1700:43c0:dc0::10"
                      ]
                    },
                    "wan_extra_routes": {
                      "type": "object",
                      "additionalProperties": {
                        "title": "wan_extra_routes",
                        "type": "object",
                        "properties": {
                          "via": {
                            "type": "string"
                          }
                        }
                      },
                      "description": "Only if `usage`==`wan`. Property Key is the destination CIDR (e.g. \"100.100.100.0/24\")"
                    },
                    "wan_extra_routes6": {
                      "type": "object",
                      "additionalProperties": {
                        "title": "wan_extra_routes",
                        "type": "object",
                        "properties": {
                          "via": {
                            "type": "string"
                          }
                        }
                      },
                      "description": "Only if `usage`==`wan`. Property Key is the destination CIDR (e.g. \"2a02:1234:420a:10c9::/64\")"
                    },
                    "wan_networks": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "Only if `usage`==`wan`. If some networks are connected to this WAN port, it can be added here so policies can be defined"
                    },
                    "wan_probe_override": {
                      "type": "object",
                      "properties": {
                        "ip6s": {
                          "uniqueItems": true,
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "description": ""
                        },
                        "ips": {
                          "uniqueItems": true,
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "description": ""
                        },
                        "probe_profile": {
                          "type": "string",
                          "description": "enum: `broadband`, `lte`"
                        }
                      },
                      "description": "Only if `usage`==`wan`"
                    },
                    "wan_source_nat": {
                      "type": "object",
                      "properties": {
                        "disabled": {
                          "type": "boolean",
                          "description": "Or to disable the source-nat",
                          "default": false
                        },
                        "nat6_pool": {
                          "type": "string",
                          "description": "If alternative nat_pool is desired",
                          "examples": [
                            "2601:1700:43c0:dc0:20c:29ff:fea7:93bc/126"
                          ]
                        },
                        "nat_pool": {
                          "type": "string",
                          "description": "If alternative nat_pool is desired",
                          "examples": [
                            "64.2.4.0/30"
                          ]
                        }
                      },
                      "description": "Only if `usage`==`wan`, optional. By default, source-NAT is performed on all WAN Ports using the interface-ip"
                    },
                    "wan_speedtest_mode": {
                      "type": "string",
                      "description": "Controls whether Marvis/scheduler can run speedtest on this port. enum: `auto`, `enabled`, `disabled`"
                    },
                    "wan_type": {
                      "type": "string",
                      "description": "Only if `usage`==`wan`. enum: `broadband`, `dsl`, `lte`"
                    }
                  },
                  "description": "Gateway port config"
                },
                "description": "Property key is the port(s) name or range (e.g. \"ge-0/0/0-10\")."
              }
            },
            "additionalProperties": {
              "type": "string",
              "description": "Property key defines the type of matching. e.g: `match_name[0:3]`, `match_model[0-6]` or `match_role`"
            }
          },
          "description": ""
        }
      },
      "description": "Gateway matching"
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
    "idp_profiles": {
      "type": "object",
      "additionalProperties": {
        "title": "idp_profile",
        "type": "object",
        "properties": {
          "base_profile": {
            "type": "string",
            "description": "enum: `critical`, `standard`, `strict`"
          },
          "created_time": {
            "type": "number",
            "description": "When the object has been created, in epoch",
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
          "modified_time": {
            "type": "number",
            "description": "When the object has been modified for the last time, in epoch",
            "readOnly": true
          },
          "name": {
            "type": "string",
            "examples": [
              "relaxed"
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
          "overwrites": {
            "type": "array",
            "items": {
              "title": "idp_profile_overwrite",
              "type": "object",
              "properties": {
                "action": {
                  "type": "string",
                  "description": "enum:\n  * alert (default)\n  * drop: silently dropping packets\n  * close: notify client/server to close connection"
                },
                "matching": {
                  "title": "idp_profile_matching",
                  "type": "object",
                  "properties": {
                    "attack_name": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": ""
                    },
                    "dst_subnet": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": ""
                    },
                    "severity": {
                      "type": "array",
                      "items": {
                        "title": "idp_profile_matching_severity_value",
                        "enum": [
                          "critical",
                          "info",
                          "major",
                          "minor"
                        ],
                        "type": "string",
                        "description": "enum: `critical`, `info`, `major`, `minor`",
                        "examples": [
                          "major"
                        ]
                      },
                      "description": ""
                    }
                  }
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
      "description": "Property key is the profile name"
    },
    "ip_configs": {
      "type": "object",
      "additionalProperties": {
        "title": "gateway_ip_config_property",
        "type": "object",
        "properties": {
          "ip": {
            "type": "string"
          },
          "ip6": {
            "type": "string"
          },
          "netmask": {
            "type": "string",
            "examples": [
              "/24"
            ]
          },
          "netmask6": {
            "type": "string",
            "examples": [
              "2001:db8:abcd:12::1"
            ]
          },
          "secondary_ips": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Optional list of secondary IPs in CIDR format",
            "examples": [
              [
                "192.168.50.1/24",
                "192.168.60.1/26"
              ]
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
        }
      },
      "description": "Property key is the network name"
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "examples": [
        "gw_template"
      ]
    },
    "networks": {
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
      "description": ""
    },
    "ntpOverride": {
      "type": "boolean",
      "default": false
    },
    "ntp_servers": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of NTP servers specific to this device. By default, those in Site Settings will be used"
    },
    "oob_ip_config": {
      "type": "object",
      "properties": {
        "gateway": {
          "type": "string",
          "description": "If `type`==`static`"
        },
        "ip": {
          "type": "string",
          "description": "If `type`==`static`"
        },
        "netmask": {
          "type": "string",
          "description": "If `type`==`static`"
        },
        "node1": {
          "type": "object",
          "properties": {
            "gateway": {
              "type": "string",
              "description": "If `type`==`static`"
            },
            "ip": {
              "type": "string"
            },
            "netmask": {
              "type": "string",
              "description": "Used only if `subnet` is not specified in `networks`"
            },
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
              "description": "Whether to use `mgmt_junos` for host-out traffic (NTP/TACPLUS/RADIUS/SYSLOG/SNMP), if alternative source network/ip is desired",
              "default": false
            },
            "vlan_id": {
              "type": "string"
            }
          },
          "description": "For HA Cluster, node1 can have different IP Config"
        },
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
        },
        "vlan_id": {
          "type": "string"
        }
      },
      "description": "Out-of-band (vme/em0/fxp0) IP config"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "path_preferences": {
      "type": "object",
      "additionalProperties": {
        "title": "gateway_path_preferences",
        "type": "object",
        "properties": {
          "paths": {
            "type": "array",
            "items": {
              "title": "gateway_path_preferences_path",
              "required": [
                "type"
              ],
              "type": "object",
              "properties": {
                "cost": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "disabled": {
                  "type": "boolean",
                  "description": "For SSR Only. `true`, if this specific path is undesired"
                },
                "gateway_ip": {
                  "type": "string",
                  "description": "Only if `type`==`local`, if a different gateway is desired"
                },
                "internet_access": {
                  "type": "boolean",
                  "description": "Only if `type`==`vpn`, if this vpn path can be used for internet"
                },
                "name": {
                  "type": "string",
                  "description": "Required when \n  * `type`==`vpn`: the name of the VPN Path to use \n  * `type`==`wan`: the name of the WAN interface to use"
                },
                "networks": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": "Required when `type`==`local`"
                },
                "target_ips": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": "If `type`==`local`, if destination IP is to be replaced"
                },
                "type": {
                  "type": "string",
                  "description": "enum: `local`, `tunnel`, `vpn`, `wan`"
                },
                "wan_name": {
                  "type": "string",
                  "description": "Optional if `type`==`vpn`",
                  "examples": [
                    "wan0"
                  ]
                }
              }
            },
            "description": ""
          },
          "strategy": {
            "type": "string",
            "description": "enum: `ecmp`, `ordered`, `weighted`"
          }
        }
      },
      "description": "Property key is the path name"
    },
    "port_config": {
      "type": "object",
      "additionalProperties": {
        "title": "gateway_port_config",
        "required": [
          "usage"
        ],
        "type": "object",
        "properties": {
          "ae_disable_lacp": {
            "type": "boolean",
            "description": "If `aggregated`==`true`. To disable LCP support for the AE interface",
            "default": false
          },
          "ae_idx": {
            "type": [
              "string",
              "null"
            ],
            "description": "If `aggregated`==`true`. Users could force to use the designated AE name (must be an integer between 0 and 127)"
          },
          "ae_lacp_force_up": {
            "type": "boolean",
            "description": "For SRX only, if `aggregated`==`true`.Sets the state of the interface as UP when the peer has limited LACP capability. Use case: When a device connected to this AE port is ZTPing for the first time, it will not have LACP configured on the other end. **Note:** Turning this on will enable force-up on one of the interfaces in the bundle only",
            "default": false
          },
          "aggregated": {
            "type": "boolean",
            "default": false
          },
          "critical": {
            "type": "boolean",
            "description": "To generate port up/down alarm, set it to true",
            "default": false
          },
          "description": {
            "type": "string",
            "description": "Interface Description. Can be a variable (i.e. \"{{myvar}}\")"
          },
          "disable_autoneg": {
            "type": "boolean",
            "default": false
          },
          "disabled": {
            "type": "boolean",
            "description": "Port admin up (true) / down (false)",
            "default": false
          },
          "dsl_type": {
            "type": "string",
            "description": "if `wan_type`==`dsl`. enum: `adsl`, `vdsl`"
          },
          "dsl_vci": {
            "type": "integer",
            "description": "If `wan_type`==`dsl`, 16 bit int",
            "contentEncoding": "int32",
            "default": 35
          },
          "dsl_vpi": {
            "type": "integer",
            "description": "If `wan_type`==`dsl`, 8 bit int",
            "contentEncoding": "int32",
            "default": 0
          },
          "duplex": {
            "type": "string",
            "description": "enum: `auto`, `full`, `half`"
          },
          "ip_config": {
            "type": "object",
            "properties": {
              "dns": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "Except for out-of_band interface (vme/em0/fxp0)"
              },
              "dns_suffix": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "Except for out-of_band interface (vme/em0/fxp0)"
              },
              "gateway": {
                "type": "string",
                "description": "Except for out-of_band interface (vme/em0/fxp0). Interface Default Gateway IP Address (i.e. \"192.168.1.1\") or a Variable (i.e. \"{{myvar}}\")",
                "examples": [
                  "192.168.1.1"
                ]
              },
              "gateway6": {
                "type": "string",
                "description": "Except for out-of_band interface (vme/em0/fxp0). Interface Default Gateway IPv6 Address (i.e. \"2001:db8::1\") or a Variable (i.e. \"{{myvar}}\")",
                "examples": [
                  "2001:db8::1"
                ]
              },
              "ip": {
                "type": "string",
                "description": "Interface IP Address (i.e. \"192.168.1.8\") or a Variable (i.e. \"{{myvar}}\")",
                "examples": [
                  "192.168.1.8"
                ]
              },
              "ip6": {
                "type": "string",
                "description": "Interface IPv6 Address (i.e. \"2001:db8::123\") or a Variable (i.e. \"{{myvar}}\")",
                "examples": [
                  "2001:db8::123"
                ]
              },
              "netmask": {
                "type": "string",
                "description": "Used only if `subnet` is not specified in `networks`. Interface Netmask (i.e. \"/24\") or a Variable (i.e. \"{{myvar}}\")",
                "examples": [
                  "/24"
                ]
              },
              "netmask6": {
                "type": "string",
                "description": "Used only if `subnet` is not specified in `networks`. Interface IPv6 Netmask (i.e. \"/64\") or a Variable (i.e. \"{{myvar}}\")",
                "examples": [
                  "/64"
                ]
              },
              "network": {
                "type": "string",
                "description": "Optional, the network to be used for mgmt"
              },
              "poser_password": {
                "type": "string",
                "description": "If `type`==`pppoe`"
              },
              "pppoe_auth": {
                "type": "string",
                "description": "if `type`==`pppoe`. enum: `chap`, `none`, `pap`"
              },
              "pppoe_username": {
                "type": "string",
                "description": "If `type`==`pppoe`"
              },
              "type": {
                "type": "string",
                "description": "enum: `dhcp`, `pppoe`, `static`"
              },
              "type6": {
                "type": "string",
                "description": "enum: `autoconf`, `dhcp`, `static`"
              }
            },
            "description": "Junos IP Config"
          },
          "lte_apn": {
            "type": "string",
            "description": "If `wan_type`==`lte`"
          },
          "lte_auth": {
            "type": "string",
            "description": "if `wan_type`==`lte`. enum: `chap`, `none`, `pap`"
          },
          "lte_backup": {
            "type": "boolean"
          },
          "lte_password": {
            "type": "string",
            "description": "If `wan_type`==`lte`"
          },
          "lte_username": {
            "type": "string",
            "description": "If `wan_type`==`lte`"
          },
          "mtu": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "name": {
            "type": "string",
            "description": "Name that we'll use to derive config"
          },
          "networks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "If `usage`==`lan`, name of the [networks]($h/Orgs%20Networks/_overview) to attach to the interface"
          },
          "outer_vlan_id": {
            "type": "integer",
            "description": "For Q-in-Q",
            "contentEncoding": "int32"
          },
          "poe_disabled": {
            "type": "boolean",
            "default": false
          },
          "port_network": {
            "type": "string",
            "description": "Only for SRX and if `usage`==`lan`, the name of the Network to be used as the Untagged VLAN"
          },
          "preserve_dscp": {
            "type": "boolean",
            "description": "Whether to preserve dscp when sending traffic over VPN (SSR-only)",
            "default": true
          },
          "redundant": {
            "type": "boolean",
            "description": "If HA mode"
          },
          "redundant_group": {
            "maximum": 128.0,
            "minimum": 1.0,
            "type": "integer",
            "description": "If HA mode, SRX Only - support redundancy-group. 1-128 for physical SRX, 1-64 for virtual SRX",
            "contentEncoding": "int32"
          },
          "reth_idx": {
            "type": "object",
            "description": "For SRX only and if HA Mode"
          },
          "reth_node": {
            "type": "string",
            "description": "If HA mode"
          },
          "reth_nodes": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "SSR only - supporting vlan-based redundancy (matching the size of `networks`)",
            "examples": [
              [
                "node0",
                "node1"
              ]
            ]
          },
          "speed": {
            "type": "string",
            "default": "auto",
            "examples": [
              "1g"
            ]
          },
          "ssr_no_virtual_mac": {
            "type": "boolean",
            "description": "When SSR is running as VM, this is required on certain hosting platforms",
            "default": false
          },
          "svr_port_range": {
            "type": "string",
            "description": "For SSR only",
            "default": "none",
            "examples": [
              "60000-60005"
            ]
          },
          "traffic_shaping": {
            "title": "gateway_traffic_shaping",
            "type": "object",
            "properties": {
              "class_percentages": {
                "type": "array",
                "items": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "description": "percentages for different class of traffic: high / medium / low / best-effort. Sum must be equal to 100"
              },
              "enabled": {
                "type": "boolean",
                "default": false
              },
              "max_tx_kbps": {
                "type": "integer",
                "description": "Interface Transmit Cap in kbps",
                "contentEncoding": "int32"
              }
            }
          },
          "usage": {
            "type": "string",
            "description": "port usage name. enum: `ha_control`, `ha_data`, `lan`, `wan`"
          },
          "vlan_id": {
            "type": "object",
            "description": "If WAN interface is on a VLAN. Can be the VLAN ID (i.e. \"10\") or a Variable (i.e. \"{{myvar}}\")"
          },
          "vpn_paths": {
            "type": "object",
            "additionalProperties": {
              "title": "gateway_port_vpn_path",
              "type": "object",
              "properties": {
                "bfd_profile": {
                  "type": "string",
                  "description": "Only if the VPN `type`==`hub_spoke`. enum: `broadband`, `lte`"
                },
                "bfd_use_tunnel_mode": {
                  "type": "boolean",
                  "description": "Only if the VPN `type`==`hub_spoke`. Whether to use tunnel mode. SSR only",
                  "default": false
                },
                "preference": {
                  "type": "integer",
                  "description": "Only if the VPN `type`==`hub_spoke`. For a given VPN, when `path_selection.strategy`==`simple`, the preference for a path (lower is preferred)",
                  "contentEncoding": "int32"
                },
                "role": {
                  "type": "string",
                  "description": "If the VPN `type`==`hub_spoke`, enum: `hub`, `spoke`. If the VPN `type`==`mesh`, enum: `mesh`"
                },
                "traffic_shaping": {
                  "title": "gateway_traffic_shaping",
                  "type": "object",
                  "properties": {
                    "class_percentages": {
                      "type": "array",
                      "items": {
                        "type": "integer",
                        "contentEncoding": "int32"
                      },
                      "description": "percentages for different class of traffic: high / medium / low / best-effort. Sum must be equal to 100"
                    },
                    "enabled": {
                      "type": "boolean",
                      "default": false
                    },
                    "max_tx_kbps": {
                      "type": "integer",
                      "description": "Interface Transmit Cap in kbps",
                      "contentEncoding": "int32"
                    }
                  }
                }
              }
            },
            "description": "Property key is the VPN name"
          },
          "wan_arp_policer": {
            "type": "string",
            "description": "Only when `wan_type`==`broadband`. enum: `default`, `max`, `recommended`"
          },
          "wan_ext_ip": {
            "type": "string",
            "description": "Only if `usage`==`wan`, optional. If spoke should reach this port by a different IP",
            "examples": [
              "64.2.4.3"
            ]
          },
          "wan_ext_ip6": {
            "type": "string",
            "description": "Only if `usage`==`wan`, optional. If spoke should reach this port by a different IPv6",
            "examples": [
              "2601:1700:43c0:dc0::10"
            ]
          },
          "wan_extra_routes": {
            "type": "object",
            "additionalProperties": {
              "title": "wan_extra_routes",
              "type": "object",
              "properties": {
                "via": {
                  "type": "string"
                }
              }
            },
            "description": "Only if `usage`==`wan`. Property Key is the destination CIDR (e.g. \"100.100.100.0/24\")"
          },
          "wan_extra_routes6": {
            "type": "object",
            "additionalProperties": {
              "title": "wan_extra_routes",
              "type": "object",
              "properties": {
                "via": {
                  "type": "string"
                }
              }
            },
            "description": "Only if `usage`==`wan`. Property Key is the destination CIDR (e.g. \"2a02:1234:420a:10c9::/64\")"
          },
          "wan_networks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Only if `usage`==`wan`. If some networks are connected to this WAN port, it can be added here so policies can be defined"
          },
          "wan_probe_override": {
            "type": "object",
            "properties": {
              "ip6s": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "ips": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "probe_profile": {
                "type": "string",
                "description": "enum: `broadband`, `lte`"
              }
            },
            "description": "Only if `usage`==`wan`"
          },
          "wan_source_nat": {
            "type": "object",
            "properties": {
              "disabled": {
                "type": "boolean",
                "description": "Or to disable the source-nat",
                "default": false
              },
              "nat6_pool": {
                "type": "string",
                "description": "If alternative nat_pool is desired",
                "examples": [
                  "2601:1700:43c0:dc0:20c:29ff:fea7:93bc/126"
                ]
              },
              "nat_pool": {
                "type": "string",
                "description": "If alternative nat_pool is desired",
                "examples": [
                  "64.2.4.0/30"
                ]
              }
            },
            "description": "Only if `usage`==`wan`, optional. By default, source-NAT is performed on all WAN Ports using the interface-ip"
          },
          "wan_speedtest_mode": {
            "type": "string",
            "description": "Controls whether Marvis/scheduler can run speedtest on this port. enum: `auto`, `enabled`, `disabled`"
          },
          "wan_type": {
            "type": "string",
            "description": "Only if `usage`==`wan`. enum: `broadband`, `dsl`, `lte`"
          }
        },
        "description": "Gateway port config"
      },
      "description": "Property key is the Port Name (i.e. \"ge-0/0/0\"), the Ports Range (i.e. \"ge-0/0/0-10\"), the List of Ports (i.e. \"ge-0/0/0,ge-1/0/0\", only allowed for Aggregated or Redundant interfaces) or a Variable (i.e. \"{{myvar}}\")."
    },
    "router_id": {
      "type": "string",
      "description": "Auto assigned if not set",
      "examples": [
        "10.2.1.10"
      ]
    },
    "routing_policies": {
      "type": "object",
      "additionalProperties": {
        "title": "gw_routing_policy",
        "type": "object",
        "properties": {
          "terms": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "title": "gw_routing_policy_term",
              "type": "object",
              "properties": {
                "actions": {
                  "type": "object",
                  "properties": {
                    "accept": {
                      "type": "boolean"
                    },
                    "add_community": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": ""
                    },
                    "add_target_vrfs": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "For SSR, hub decides how VRF routes are leaked on spoke"
                    },
                    "community": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "When used as export policy, optional"
                    },
                    "exclude_as_path": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "When used as export policy, optional. To exclude certain AS"
                    },
                    "exclude_community": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": ""
                    },
                    "export_communities": {
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
                    "network": {
                      "uniqueItems": true,
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
                        "title": "gw_routing_policy_term_matching_protocol_enum",
                        "enum": [
                          "aggregate",
                          "bgp",
                          "direct",
                          "ospf",
                          "static"
                        ],
                        "type": "string",
                        "description": "enum: `aggregate`, `bgp`, `direct`, `ospf`, `static` (SRX Only)"
                      },
                      "description": ""
                    },
                    "route_exists": {
                      "title": "gw_routing_policy_term_matching_route_exists",
                      "type": "object",
                      "properties": {
                        "route": {
                          "type": "string",
                          "examples": [
                            "192.168.0.0/24"
                          ]
                        },
                        "vrf_name": {
                          "type": "string",
                          "description": "Name of the vrf instance, it can also be the name of the VPN or wan if they",
                          "default": "default"
                        }
                      }
                    },
                    "vpn_neighbor_mac": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "overlay-facing criteria (used for bgp_config where via=vpn)"
                    },
                    "vpn_path": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "overlay-facing criteria (used for bgp_config where via=vpn). ordered-"
                    },
                    "vpn_path_sla": {
                      "title": "gw_routing_policy_term_matching_vpn_path_sla",
                      "type": "object",
                      "properties": {
                        "max_jitter": {
                          "type": [
                            "integer",
                            "null"
                          ],
                          "contentEncoding": "int32"
                        },
                        "max_latency": {
                          "type": [
                            "integer",
                            "null"
                          ],
                          "contentEncoding": "int32",
                          "examples": [
                            1500
                          ]
                        },
                        "max_loss": {
                          "type": [
                            "integer",
                            "null"
                          ],
                          "contentEncoding": "int32",
                          "examples": [
                            30
                          ]
                        }
                      }
                    }
                  },
                  "description": "zero or more criteria/filter can be specified to match the term, all criteria have to be met"
                }
              }
            },
            "description": "zero or more criteria/filter can be specified to match the term, all criteria have to be met"
          }
        }
      },
      "description": "Property key is the routing policy name"
    },
    "service_policies": {
      "type": "array",
      "items": {
        "title": "service_policy",
        "type": "object",
        "properties": {
          "action": {
            "type": "string",
            "description": "enum: `allow`, `deny`"
          },
          "antivirus": {
            "type": "object",
            "properties": {
              "avprofile_id": {
                "type": "string",
                "description": "org-level AV Profile can be used, this takes precedence over 'profile'",
                "contentEncoding": "uuid"
              },
              "enabled": {
                "type": "boolean",
                "default": false
              },
              "profile": {
                "type": "string",
                "description": "Default / noftp / httponly / or keys from av_profiles"
              }
            },
            "description": "For SRX-only"
          },
          "appqoe": {
            "type": "object",
            "properties": {
              "enabled": {
                "type": "boolean",
                "default": false
              }
            },
            "description": "SRX only"
          },
          "ewf": {
            "type": "array",
            "items": {
              "title": "service_policy_ewf_rule",
              "type": "object",
              "properties": {
                "alert_only": {
                  "type": "boolean"
                },
                "block_message": {
                  "type": "string",
                  "examples": [
                    "Access to this URL Category has been blocked"
                  ]
                },
                "enabled": {
                  "type": "boolean",
                  "default": false
                },
                "profile": {
                  "type": "string",
                  "description": "enum: `critical`, `standard`, `strict`"
                }
              }
            },
            "description": ""
          },
          "idp": {
            "title": "idp_config",
            "type": "object",
            "properties": {
              "alert_only": {
                "type": "boolean"
              },
              "enabled": {
                "type": "boolean",
                "default": false
              },
              "idpprofile_id": {
                "type": "string",
                "description": "org_level IDP Profile can be used, this takes precedence over `profile`",
                "contentEncoding": "uuid",
                "examples": [
                  "89b9d208-84a4-fa8f-af57-78f92c639cf2"
                ]
              },
              "profile": {
                "type": "string",
                "description": "enum: `Custom`, `strict` (default), `standard` or keys from idp_profiles",
                "default": "strict"
              }
            }
          },
          "local_routing": {
            "type": "boolean",
            "description": "access within the same VRF"
          },
          "name": {
            "type": "string"
          },
          "path_preference": {
            "type": "string",
            "description": "By default, we derive all paths available and use them. Optionally, you can customize by using `path_preference`"
          },
          "secintel": {
            "type": "object",
            "properties": {
              "enabled": {
                "type": "boolean",
                "default": false
              },
              "profile": {
                "type": "string",
                "description": "enum: `default`, `standard`, `strict`"
              },
              "secintelprofile_id": {
                "type": "string",
                "description": "org-level secintel Profile can be used, this takes precedence over 'profile'"
              }
            },
            "description": "SRX only"
          },
          "servicepolicy_id": {
            "type": "string",
            "description": "Used to link servicepolicy defined at org level and overwrite some attributes",
            "contentEncoding": "uuid"
          },
          "services": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          },
          "skyatp": {
            "type": "object",
            "properties": {
              "dns_dga_detection": {
                "title": "service_policy_skyatp_dns_dga_detection",
                "type": "object",
                "properties": {
                  "enabled": {
                    "type": "boolean"
                  },
                  "profile": {
                    "type": "string",
                    "description": "enum: `default`, `standard`, `strict`"
                  }
                }
              },
              "dns_tunnel_detection": {
                "title": "service_policy_skyatp_dns_tunnel_detection",
                "type": "object",
                "properties": {
                  "enabled": {
                    "type": "boolean"
                  },
                  "profile": {
                    "type": "string",
                    "description": "enum: `default`, `standard`, `strict`"
                  }
                }
              },
              "http_inspection": {
                "title": "service_policy_skyatp_http_inspection",
                "type": "object",
                "properties": {
                  "enabled": {
                    "type": "boolean"
                  },
                  "profile": {
                    "type": "string",
                    "description": "enum: `standard`, `strict`"
                  }
                }
              },
              "iot_device_policy": {
                "title": "service_policy_skyatp_iot_device_policy",
                "type": "object",
                "properties": {
                  "enabled": {
                    "type": "boolean"
                  }
                }
              }
            },
            "description": "SRX only"
          },
          "ssl_proxy": {
            "type": "object",
            "properties": {
              "ciphers_category": {
                "type": "string",
                "description": "enum: `medium`, `strong`, `weak`"
              },
              "enabled": {
                "type": "boolean",
                "default": false
              }
            },
            "description": "For SRX-only"
          },
          "syslog": {
            "type": "object",
            "properties": {
              "enabled": {
                "type": "boolean",
                "default": false
              },
              "server_names": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "",
                "examples": [
                  [
                    "dc_syslog_server"
                  ]
                ]
              }
            },
            "description": "Required for syslog logging"
          },
          "tenants": {
            "uniqueItems": true,
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
    "tunnel_configs": {
      "type": "object",
      "additionalProperties": {
        "title": "tunnel_config",
        "type": "object",
        "properties": {
          "auto_provision": {
            "type": "object",
            "properties": {
              "enabled": {
                "type": "boolean",
                "description": "Enable auto provisioning for the tunnel. If enabled, the `primary` and `secondary` nodes will be ignored."
              },
              "latlng": {
                "type": "object",
                "properties": {
                  "lat": {
                    "type": "number",
                    "examples": [
                      37.295833
                    ]
                  },
                  "lng": {
                    "type": "number",
                    "examples": [
                      -122.032946
                    ]
                  }
                },
                "required": [
                  "lat",
                  "lng"
                ],
                "description": "API override for POP selection"
              },
              "primary": {
                "title": "tunnel_config_auto_provision_node",
                "type": "object",
                "properties": {
                  "probe_ips": {
                    "uniqueItems": true,
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": ""
                  },
                  "wan_names": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "Optional, only needed if `vars_only`==`false`"
                  }
                }
              },
              "provider": {
                "type": "string",
                "description": "enum: `jse-ipsec`, `zscaler-ipsec`"
              },
              "region": {
                "type": "string",
                "description": "API override for POP selection in the case user wants to override the auto discovery of remote network location and force the tunnel to use the specified peer location."
              },
              "secondary": {
                "title": "tunnel_config_auto_provision_node",
                "type": "object",
                "properties": {
                  "probe_ips": {
                    "uniqueItems": true,
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": ""
                  },
                  "wan_names": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "Optional, only needed if `vars_only`==`false`"
                  }
                }
              },
              "service_connection": {
                "type": "string",
                "description": "if `provider`==`prisma-ipsec`. By default, we'll use the location of the site to determine the optimal Remote Network location, optionally, service_connection can be considered, then we'll also consider this along with the site location. Define service_connection if the traffic is to be routed to a specific service connection. This field takes a service connection name that is configured in the Prisma cloud, Prisma Access Setup -> Service Connections.",
                "examples": [
                  "Juniper-Lab-SC-1"
                ]
              }
            },
            "required": [
              "provider"
            ],
            "description": "Auto Provisioning configuration for the tunne. This takes precedence over the `primary` and `secondary` nodes."
          },
          "ike_lifetime": {
            "type": "integer",
            "description": "Only if `provider`==`custom-ipsec`",
            "contentEncoding": "int32"
          },
          "ike_mode": {
            "type": "string",
            "description": "Only if `provider`==`custom-ipsec`. enum: `aggressive`, `main`"
          },
          "ike_proposals": {
            "type": "array",
            "items": {
              "title": "tunnel_config_ike_proposal",
              "type": "object",
              "properties": {
                "auth_algo": {
                  "type": "string",
                  "description": "enum: `md5`, `sha1`, `sha2`"
                },
                "dh_group": {
                  "type": "string",
                  "description": "enum:\n  * 1\n  * 2 (1024-bit)\n  * 5\n  * 14 (default, 2048-bit)\n  * 15 (3072-bit)\n  * 16 (4096-bit)\n  * 19 (256-bit ECP)\n  * 20 (384-bit ECP)\n  * 21 (521-bit ECP)\n  * 24 (2048-bit ECP)"
                },
                "enc_algo": {
                  "type": "object",
                  "description": "enum: `3des`, `aes128`, `aes256`, `aes_gcm128`, `aes_gcm256`"
                }
              }
            },
            "description": "If `provider`==`custom-ipsec`"
          },
          "ipsec_lifetime": {
            "type": "integer",
            "description": "If `provider`==`custom-ipsec`",
            "contentEncoding": "int32"
          },
          "ipsec_proposals": {
            "type": "array",
            "items": {
              "title": "tunnel_config_ipsec_proposal",
              "type": "object",
              "properties": {
                "auth_algo": {
                  "type": "string",
                  "description": "enum: `md5`, `sha1`, `sha2`"
                },
                "dh_group": {
                  "type": "string",
                  "description": "Only if `provider`==`custom-ipsec`. enum:\n  * 1\n  * 2 (1024-bit)\n  * 5\n  * 14 (default, 2048-bit)\n  * 15 (3072-bit)\n  * 16 (4096-bit)\n  * 19 (256-bit ECP)\n  * 20 (384-bit ECP)\n  * 21 (521-bit ECP)\n  * 24 (2048-bit ECP)"
                },
                "enc_algo": {
                  "type": "object",
                  "description": "enum: `3des`, `aes128`, `aes256`, `aes_gcm128`, `aes_gcm256`"
                }
              }
            },
            "description": "Only if  `provider`==`custom-ipsec`"
          },
          "local_id": {
            "type": "string",
            "description": "Required if `provider`==`zscaler-ipsec`, `provider`==`jse-ipsec` or `provider`==`custom-ipsec`"
          },
          "local_subnets": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of Local protected subnet for policy-based IPSec negotiation"
          },
          "mode": {
            "type": "string",
            "description": "Required if `provider`==`zscaler-gre`, `provider`==`jse-ipsec`. enum: `active-active`, `active-standby`"
          },
          "networks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "If `provider`==`custom-ipsec` or `provider`==`prisma-ipsec`, networks reachable via this tunnel"
          },
          "primary": {
            "type": "object",
            "properties": {
              "hosts": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "internal_ips": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "Only if `provider`==`zscaler-gre`, `provider`==`jse-ipsec`, `provider`==`custom-ipsec` or `provider`==`custom-gre`"
              },
              "probe_ips": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "remote_ids": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "Only if  `provider`==`jse-ipsec` or `provider`==`custom-ipsec`"
              },
              "wan_names": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              }
            },
            "required": [
              "hosts",
              "wan_names"
            ],
            "description": "Only if `provider`==`zscaler-ipsec`, `provider`==`jse-ipsec` or `provider`==`custom-ipsec`"
          },
          "probe": {
            "type": "object",
            "properties": {
              "interval": {
                "type": "integer",
                "description": "How often to trigger the probe",
                "contentEncoding": "int32"
              },
              "threshold": {
                "type": "integer",
                "description": "Number of consecutive misses before declaring the tunnel down",
                "contentEncoding": "int32"
              },
              "timeout": {
                "type": "integer",
                "description": "Time within which to complete the connectivity check",
                "contentEncoding": "int32"
              },
              "type": {
                "type": "string",
                "description": "enum: `http`, `icmp`"
              }
            },
            "description": "Only if `provider`==`custom-ipsec`"
          },
          "protocol": {
            "type": "string",
            "description": "Only if `provider`==`custom-ipsec`. enum: `gre`, `ipsec`"
          },
          "provider": {
            "type": "string",
            "description": "Only if `auto_provision.enabled`==`false`. enum: `custom-ipsec`, `custom-gre`, `jse-ipsec`, `prisma-ipsec`, `zscaler-gre`, `zscaler-ipsec`"
          },
          "psk": {
            "type": "string",
            "description": "Required if `provider`==`zscaler-ipsec`, `provider`==`jse-ipsec` or `provider`==`custom-ipsec`"
          },
          "remote_subnets": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of Remote protected subnet for policy-based IPSec negotiation"
          },
          "secondary": {
            "type": "object",
            "properties": {
              "hosts": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "internal_ips": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "Only if `provider`==`zscaler-gre`, `provider`==`jse-ipsec`, `provider`==`custom-ipsec` or `provider`==`custom-gre`"
              },
              "probe_ips": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "remote_ids": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "Only if  `provider`==`jse-ipsec` or `provider`==`custom-ipsec`"
              },
              "wan_names": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              }
            },
            "required": [
              "hosts",
              "wan_names"
            ],
            "description": "Only if `provider`==`zscaler-ipsec`, `provider`==`jse-ipsec` or `provider`==`custom-ipsec`"
          },
          "version": {
            "type": "string",
            "description": "Only if `provider`==`custom-gre` or `provider`==`custom-ipsec`. enum: `1`, `2`"
          }
        }
      },
      "description": "Property key is the tunnel name"
    },
    "tunnel_provider_options": {
      "title": "tunnel_provider_options",
      "type": "object",
      "properties": {
        "jse": {
          "type": "object",
          "properties": {
            "num_users": {
              "type": "integer",
              "contentEncoding": "int32",
              "examples": [
                5
              ]
            },
            "org_name": {
              "type": "string",
              "description": "JSE Organization name. The list of available organizations can be retrieved with the [Get Org JSE Info]($e/Orgs%20JSE/getOrgJseInfo) API Call",
              "examples": [
                "JSE_ORG1"
              ]
            }
          },
          "description": "For jse-ipsec, this allows provisioning of adequate resource on JSE. Make sure adequate licenses are added"
        },
        "prisma": {
          "title": "tunnel_provider_options_prisma",
          "type": "object",
          "properties": {
            "service_account_name": {
              "type": "string",
              "description": "For prisma-ipsec, service account name to used for tunnel auto provisioning",
              "examples": [
                "sa1@1823425211"
              ]
            }
          }
        },
        "zscaler": {
          "type": "object",
          "properties": {
            "aup_block_internet_until_accepted": {
              "type": "boolean",
              "default": false
            },
            "aup_enabled": {
              "type": "boolean",
              "description": "Can only be `true` when `auth_required`==`false`, display Acceptable Use Policy (AUP)",
              "default": false
            },
            "aup_force_ssl_inspection": {
              "type": "boolean",
              "description": "Proxy HTTPs traffic, requiring Zscaler cert to be installed in browser",
              "default": false
            },
            "aup_timeout_in_days": {
              "maximum": 180.0,
              "minimum": 1.0,
              "type": "integer",
              "description": "Required if `aup_enabled`==`true`. Days before AUP is requested again",
              "contentEncoding": "int32"
            },
            "auth_required": {
              "type": "boolean",
              "description": "Enable this option to enforce user authentication",
              "default": false
            },
            "caution_enabled": {
              "type": "boolean",
              "description": "Can only be `true` when `auth_required`==`false`, display caution notification for non-authenticated users",
              "default": false
            },
            "dn_bandwidth": {
              "maximum": 99999.0,
              "minimum": 0.1,
              "type": [
                "number",
                "null"
              ],
              "description": "Download bandwidth cap of the link, in Mbps. Disabled if not set",
              "examples": [
                200
              ]
            },
            "idle_time_in_minutes": {
              "maximum": 43200.0,
              "minimum": 0.0,
              "type": "integer",
              "description": "Required if `surrogate_IP`==`true`, idle Time to Disassociation",
              "contentEncoding": "int32"
            },
            "ofw_enabled": {
              "type": "boolean",
              "description": "If `true`, enable the firewall control option",
              "default": false
            },
            "sub_locations": {
              "type": "array",
              "items": {
                "title": "tunnel_provider_options_zscaler_sub_location",
                "type": "object",
                "properties": {
                  "aup_block_internet_until_accepted": {
                    "type": "boolean",
                    "default": false
                  },
                  "aup_enabled": {
                    "type": "boolean",
                    "description": "Can only be `true` when `auth_required`==`false`, display Acceptable Use Policy (AUP)",
                    "default": false
                  },
                  "aup_force_ssl_inspection": {
                    "type": "boolean",
                    "description": "Proxy HTTPs traffic, requiring Zscaler cert to be installed in browser",
                    "default": false
                  },
                  "aup_timeout_in_days": {
                    "maximum": 180.0,
                    "minimum": 1.0,
                    "type": "integer",
                    "description": "Required if `aup_enabled`==`true`. Days before AUP is requested again",
                    "contentEncoding": "int32"
                  },
                  "auth_required": {
                    "type": "boolean",
                    "description": "Enable this option to authenticate users",
                    "default": false
                  },
                  "caution_enabled": {
                    "type": "boolean",
                    "description": "Can only be `true` when `auth_required`==`false`, display caution notification for non-authenticated users",
                    "default": false
                  },
                  "dn_bandwidth": {
                    "maximum": 99999.0,
                    "minimum": 0.1,
                    "type": [
                      "number",
                      "null"
                    ],
                    "description": "Download bandwidth cap of the link, in Mbps. Disabled if not set",
                    "examples": [
                      200
                    ]
                  },
                  "idle_time_in_minutes": {
                    "maximum": 43200.0,
                    "minimum": 0.0,
                    "type": "integer",
                    "description": "Required if `surrogate_IP`==`true`, idle Time to Disassociation",
                    "contentEncoding": "int32"
                  },
                  "name": {
                    "type": "string",
                    "description": "[network]($h/Orgs%20Networks/_overview) name"
                  },
                  "ofw_enabled": {
                    "type": "boolean",
                    "description": "If `true`, enable the firewall control option",
                    "default": false
                  },
                  "surrogate_IP": {
                    "type": "boolean",
                    "description": "Can only be `true` when `auth_required`==`true`. Map a user to a private IP address so it applies the user's policies, instead of the location's policies",
                    "default": false
                  },
                  "surrogate_IP_enforced_for_known_browsers": {
                    "type": "boolean",
                    "description": "Can only be `true` when `surrogate_IP`==`true`, enforce surrogate IP for known browsers"
                  },
                  "surrogate_refresh_time_in_minutes": {
                    "maximum": 43200.0,
                    "minimum": 1.0,
                    "type": "integer",
                    "description": "Required if `surrogate_IP_enforced_for_known_browsers`==`true`, must be lower or equal than `idle_time_in_minutes`, refresh Time for re-validation of Surrogacy",
                    "contentEncoding": "int32"
                  },
                  "up_bandwidth": {
                    "maximum": 99999.0,
                    "minimum": 0.1,
                    "type": [
                      "number",
                      "null"
                    ],
                    "description": "Download bandwidth cap of the link, in Mbps. Disabled if not set",
                    "examples": [
                      200
                    ]
                  }
                }
              },
              "description": "`sub-locations` can be used for specific uses cases to define different configuration based on the user network"
            },
            "surrogate_IP": {
              "type": "boolean",
              "description": "Can only be `true` when `auth_required`==`true`. Map a user to a private IP address so it applies the user's policies, instead of the location's policies",
              "default": false
            },
            "surrogate_IP_enforced_for_known_browsers": {
              "type": "boolean",
              "description": "Can only be `true` when `surrogate_IP`==`true`, enforce surrogate IP for known browsers"
            },
            "surrogate_refresh_time_in_minutes": {
              "maximum": 43200.0,
              "minimum": 1.0,
              "type": "integer",
              "description": "Required if `surrogate_IP_enforced_for_known_browsers`==`true`, must be lower or equal than `idle_time_in_minutes`, refresh Time for re-validation of Surrogacy",
              "contentEncoding": "int32"
            },
            "up_bandwidth": {
              "maximum": 99999.0,
              "minimum": 0.1,
              "type": [
                "number",
                "null"
              ],
              "description": "Download bandwidth cap of the link, in Mbps. Disabled if not set",
              "examples": [
                200
              ]
            },
            "xff_forward_enabled": {
              "type": "boolean",
              "description": "Location uses proxy chaining to forward traffic",
              "default": false
            }
          },
          "description": "For zscaler-ipsec and zscaler-gre"
        }
      }
    },
    "type": {
      "type": "string",
      "description": "enum: `spoke`, `standalone`"
    },
    "url_filtering_deny_msg": {
      "type": "string",
      "description": "When a service policy denies a app_category, what message to show in user's browser",
      "default": "Access to this URL Category has been blocked",
      "examples": [
        "Access to this URL Category has been blocked"
      ]
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
        "title": "gateway_vrf_instance",
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
        },
        "examples": [
          {
            "networks": [
              "CORP_NET",
              "MGMT_NET"
            ]
          }
        ]
      },
      "description": "Property key is the network name",
      "examples": [
        {
          "CORP_VRF": {
            "networks": [
              "CORP_NET",
              "MGMT_NET"
            ]
          }
        }
      ]
    }
  },
  "required": [
    "name"
  ],
  "description": "Gateway Template is applied to a site for gateway(s) in a site."
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

`mistapi.api.v1.orgs.gateway_templates.getOrgGatewayTemplate()`

## Usage Context

Retrieves a specific gateway template by ID.

## Gotchas

- Gateway templates define WAN, LAN, and routing configurations for SRX/SSR devices.

## Related Endpoints

- [GET_orgs_org_id_gatewaytemplates.md](GET_orgs_org_id_gatewaytemplates.md) — List templates
- [PUT_orgs_org_id_gatewaytemplates_gatewaytemplate_id.md](PUT_orgs_org_id_gatewaytemplates_gatewaytemplate_id.md) — Update template

## MistHelper Notes

Used by MistHelper via `listOrgGatewayTemplates` in Menus 4, 26, 28, 35, 111.
