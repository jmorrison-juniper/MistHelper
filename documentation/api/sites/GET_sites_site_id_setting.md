# getSiteSetting

> getSiteSetting

## HTTP

`GET /api/v1/sites/{site_id}/setting`

## Description

Get the Site Settings

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

None.

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
    "allow_mist": {
      "type": "boolean",
      "description": "whether to allow Mist to look at this org",
      "default": false
    },
    "analytic": {
      "title": "site_setting_analytic",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "Enable Advanced Analytic feature (using SUB-ANA license)",
          "default": false
        }
      }
    },
    "ap_matching": {
      "title": "site_setting_ap_matching",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean"
        },
        "rules": {
          "type": "array",
          "items": {
            "title": "site_setting_ap_matching_rule",
            "type": "object",
            "properties": {
              "match_model": {
                "type": "string",
                "examples": [
                  "AP12"
                ]
              },
              "name": {
                "type": "string",
                "examples": [
                  "AP12"
                ]
              },
              "port_config": {
                "type": "object",
                "additionalProperties": {
                  "title": "ap_port_config",
                  "type": "object",
                  "properties": {
                    "disabled": {
                      "type": "boolean",
                      "default": false
                    },
                    "dynamic_vlan": {
                      "type": "object",
                      "properties": {
                        "default_vlan_id": {
                          "maximum": 4094.0,
                          "minimum": 1.0,
                          "type": "integer",
                          "contentEncoding": "int32",
                          "examples": [
                            999
                          ]
                        },
                        "enabled": {
                          "type": "boolean"
                        },
                        "type": {
                          "type": "string"
                        },
                        "vlans": {
                          "type": "object",
                          "additionalProperties": {
                            "type": "string",
                            "nullable": true
                          },
                          "examples": [
                            {
                              "1-10": null,
                              "user": null
                            }
                          ]
                        }
                      },
                      "description": "Optional dynamic vlan"
                    },
                    "enable_mac_auth": {
                      "type": "boolean",
                      "default": false
                    },
                    "forwarding": {
                      "type": "string",
                      "description": "enum: \n  * `all`: local breakout, All VLANs\n  * `limited`: local breakout, only the VLANs configured in `port_vlan_id` and `vlan_ids`\n  * `mxtunnel`: central breakout to an Org Mist Edge (requires `mxtunnel_id`)\n  * `site_mxedge`: central breakout to a Site Mist Edge (requires `mxtunnel_name`)\n  * `wxtunnel`': central breakout to an Org WxTunnel (requires `wxtunnel_id`)"
                    },
                    "mac_auth_preferred": {
                      "type": "boolean",
                      "description": "When `true`, we'll do dot1x then mac_auth. enable this to prefer mac_auth",
                      "default": false
                    },
                    "mac_auth_protocol": {
                      "type": "string",
                      "description": "if `enable_mac_auth`==`true`, allows user to select an authentication protocol. enum: `eap-md5`, `eap-peap`, `pap`"
                    },
                    "mist_nac": {
                      "title": "wlan_mist_nac",
                      "type": "object",
                      "properties": {
                        "acct_interim_interval": {
                          "maximum": 65535.0,
                          "minimum": 0.0,
                          "type": "integer",
                          "description": "How frequently should interim accounting be reported, 60-65535. default is 0 (use one specified in Access-Accept request from Server). Very frequent messages can affect the performance of the radius server, 600 and up is recommended when enabled.",
                          "contentEncoding": "int32",
                          "default": 0,
                          "examples": [
                            60
                          ]
                        },
                        "auth_servers_retries": {
                          "maximum": 10.0,
                          "minimum": 1.0,
                          "type": "integer",
                          "description": "Radius auth session retries. Following fast timers are set if `fast_dot1x_timers` knob is enabled. \"retries\" are set to value of `auth_servers_timeout`. \"max-requests\" is also set when setting `auth_servers_retries` is set to default value to 3.",
                          "contentEncoding": "int32",
                          "default": 2,
                          "examples": [
                            3
                          ]
                        },
                        "auth_servers_timeout": {
                          "maximum": 30.0,
                          "minimum": 1.0,
                          "type": "integer",
                          "description": "Radius auth session timeout. Following fast timers are set if `fast_dot1x_timers` knob is enabled. \"quite-period\" and \"transmit-period\" are set to half the value of `auth_servers_timeout`. \"supplicant-timeout\" is also set when setting `auth_servers_timeout` is set to default value of 10.",
                          "contentEncoding": "int32",
                          "default": 5,
                          "examples": [
                            5
                          ]
                        },
                        "coa_enabled": {
                          "type": "boolean",
                          "description": "Allows a RADIUS server to dynamically modify the authorization status of a user session.",
                          "default": false
                        },
                        "coa_port": {
                          "maximum": 65535.0,
                          "minimum": 1.0,
                          "type": "integer",
                          "description": "the communication port used for \u201cChange of Authorization\u201d (CoA) messages",
                          "contentEncoding": "int32",
                          "examples": [
                            3799
                          ]
                        },
                        "enabled": {
                          "type": "boolean",
                          "description": "When enabled:\n  * `auth_servers` is ignored\n  * `acct_servers` is ignored\n  * `auth_servers_*` are ignored\n  * `coa_servers` is ignored\n  * `radsec` is ignored\n  * `coa_enabled` is assumed",
                          "default": false
                        },
                        "fast_dot1x_timers": {
                          "type": "boolean",
                          "description": "If set to true, sets default fast-timers with values calculated from `auth_servers_timeout` and `auth_server_retries`.",
                          "default": false
                        },
                        "network": {
                          "type": [
                            "string",
                            "null"
                          ],
                          "description": "Which network the mist nac server resides in",
                          "examples": [
                            "default"
                          ]
                        },
                        "source_ip": {
                          "type": [
                            "string",
                            "null"
                          ],
                          "description": "In case there is a static IP for this network, we can specify it using source ip",
                          "examples": [
                            "1.2.3.4"
                          ]
                        }
                      }
                    },
                    "mx_tunnel_id": {
                      "type": "string",
                      "description": "If `forwarding`==`mxtunnel`, vlan_ids comes from mxtunnel",
                      "contentEncoding": "uuid",
                      "examples": [
                        "08cd7499-5841-51c8-e663-fb16b6f3b45e"
                      ]
                    },
                    "mxtunnel_name": {
                      "type": "string",
                      "description": "If `forwarding`==`site_mxedge`, vlan_ids comes from site_mxedge (`mxtunnels` under site setting)"
                    },
                    "port_auth": {
                      "type": "string",
                      "description": "When doing port auth. enum: `dot1x`, `none`"
                    },
                    "port_vlan_id": {
                      "maximum": 4094.0,
                      "minimum": 1.0,
                      "type": "integer",
                      "description": "If `forwarding`==`limited`",
                      "contentEncoding": "int32",
                      "examples": [
                        1
                      ]
                    },
                    "radius_config": {
                      "type": "object",
                      "properties": {
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
                          "description": "radius auth session retries",
                          "contentEncoding": "int32",
                          "default": 3
                        },
                        "auth_servers_timeout": {
                          "type": "integer",
                          "description": "radius auth session timeout",
                          "contentEncoding": "int32",
                          "default": 5
                        },
                        "coa_enabled": {
                          "type": "boolean",
                          "default": false
                        },
                        "coa_port": {
                          "maximum": 65535.0,
                          "minimum": 1.0,
                          "type": "integer",
                          "contentEncoding": "int32",
                          "default": 3799
                        },
                        "network": {
                          "type": "string",
                          "description": "use `network`or `source_ip`, which network the RADIUS server resides, if there's static IP for this network, we'd use it as source-ip"
                        },
                        "source_ip": {
                          "type": "string",
                          "description": "use `network`or `source_ip`"
                        }
                      },
                      "description": "Junos Radius config"
                    },
                    "radsec": {
                      "type": "object",
                      "properties": {
                        "coa_enabled": {
                          "type": "boolean",
                          "default": false
                        },
                        "enabled": {
                          "type": "boolean"
                        },
                        "idle_timeout": {
                          "type": "object",
                          "description": "Radsec Idle Timeout in seconds. Default is 60"
                        },
                        "mxcluster_ids": {
                          "type": "array",
                          "items": {
                            "type": "string",
                            "contentEncoding": "uuid"
                          },
                          "description": "To use Org mxedges when this WLAN does not use mxtunnel, specify their mxcluster_ids. Org mxedge(s) identified by mxcluster_ids"
                        },
                        "proxy_hosts": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "description": "Default is site.mxedge.radsec.proxy_hosts which must be a superset of all `wlans[*].radsec.proxy_hosts`. When `radsec.proxy_hosts` are not used, tunnel peers (org or site mxedges) are used irrespective of `use_site_mxedge`"
                        },
                        "server_name": {
                          "type": "string",
                          "description": "Name of the server to verify (against the cacerts in Org Setting). Only if not Mist Edge.",
                          "examples": [
                            "radsec.abc.com"
                          ]
                        },
                        "servers": {
                          "uniqueItems": true,
                          "type": "array",
                          "items": {
                            "title": "radsec_server",
                            "type": "object",
                            "properties": {
                              "host": {
                                "type": "string",
                                "examples": [
                                  "1.1.1.1"
                                ]
                              },
                              "port": {
                                "maximum": 65535.0,
                                "minimum": 1.0,
                                "type": "integer",
                                "contentEncoding": "int32",
                                "examples": [
                                  1812
                                ]
                              }
                            }
                          },
                          "description": "List of RadSec Servers. Only if not Mist Edge."
                        },
                        "use_mxedge": {
                          "type": "boolean",
                          "description": "use mxedge(s) as RadSec Proxy"
                        },
                        "use_site_mxedge": {
                          "type": "boolean",
                          "description": "To use Site mxedges when this WLAN does not use mxtunnel",
                          "default": false
                        }
                      },
                      "description": "RadSec settings"
                    },
                    "vlan_id": {
                      "maximum": 4094.0,
                      "minimum": 1.0,
                      "type": "integer",
                      "description": "Optional to specify the vlan id for a tunnel if forwarding is for `wxtunnel`, `mxtunnel` or `site_mxedge`.\n  * if vlan_id is not specified then it will use first one in vlan_ids[] of the mxtunnel.\n  * if forwarding == site_mxedge, vlan_ids comes from site_mxedge (`mxtunnels` under site setting)",
                      "contentEncoding": "int32",
                      "examples": [
                        9
                      ]
                    },
                    "vlan_ids": {
                      "type": "string",
                      "description": "If `forwarding`==`limited`, comma separated list of additional vlan ids allowed on this port",
                      "examples": [
                        "10,20,30"
                      ]
                    },
                    "wxtunnel_id": {
                      "type": "string",
                      "description": "If `forwarding`==`wxtunnel`, the port is bridged to the vlan of the session",
                      "contentEncoding": "uuid",
                      "examples": [
                        "7dae216d-7c98-a51b-e068-dd7d477b7216"
                      ]
                    },
                    "wxtunnel_remote_id": {
                      "type": "string",
                      "description": "If `forwarding`==`wxtunnel`, the port is bridged to the vlan of the session",
                      "examples": [
                        "wifiguest"
                      ]
                    }
                  }
                },
                "description": "Property key is the interface(s) (e.g. \"eth1,eth2\")"
              }
            }
          },
          "description": ""
        }
      }
    },
    "ap_port_config": {
      "title": "site_setting_ap_port_config",
      "type": "object",
      "properties": {
        "model_specific": {
          "type": "object",
          "additionalProperties": {
            "title": "ap_port_config",
            "type": "object",
            "properties": {
              "disabled": {
                "type": "boolean",
                "default": false
              },
              "dynamic_vlan": {
                "type": "object",
                "properties": {
                  "default_vlan_id": {
                    "maximum": 4094.0,
                    "minimum": 1.0,
                    "type": "integer",
                    "contentEncoding": "int32",
                    "examples": [
                      999
                    ]
                  },
                  "enabled": {
                    "type": "boolean"
                  },
                  "type": {
                    "type": "string"
                  },
                  "vlans": {
                    "type": "object",
                    "additionalProperties": {
                      "type": "string",
                      "nullable": true
                    },
                    "examples": [
                      {
                        "1-10": null,
                        "user": null
                      }
                    ]
                  }
                },
                "description": "Optional dynamic vlan"
              },
              "enable_mac_auth": {
                "type": "boolean",
                "default": false
              },
              "forwarding": {
                "type": "string",
                "description": "enum: \n  * `all`: local breakout, All VLANs\n  * `limited`: local breakout, only the VLANs configured in `port_vlan_id` and `vlan_ids`\n  * `mxtunnel`: central breakout to an Org Mist Edge (requires `mxtunnel_id`)\n  * `site_mxedge`: central breakout to a Site Mist Edge (requires `mxtunnel_name`)\n  * `wxtunnel`': central breakout to an Org WxTunnel (requires `wxtunnel_id`)"
              },
              "mac_auth_preferred": {
                "type": "boolean",
                "description": "When `true`, we'll do dot1x then mac_auth. enable this to prefer mac_auth",
                "default": false
              },
              "mac_auth_protocol": {
                "type": "string",
                "description": "if `enable_mac_auth`==`true`, allows user to select an authentication protocol. enum: `eap-md5`, `eap-peap`, `pap`"
              },
              "mist_nac": {
                "title": "wlan_mist_nac",
                "type": "object",
                "properties": {
                  "acct_interim_interval": {
                    "maximum": 65535.0,
                    "minimum": 0.0,
                    "type": "integer",
                    "description": "How frequently should interim accounting be reported, 60-65535. default is 0 (use one specified in Access-Accept request from Server). Very frequent messages can affect the performance of the radius server, 600 and up is recommended when enabled.",
                    "contentEncoding": "int32",
                    "default": 0,
                    "examples": [
                      60
                    ]
                  },
                  "auth_servers_retries": {
                    "maximum": 10.0,
                    "minimum": 1.0,
                    "type": "integer",
                    "description": "Radius auth session retries. Following fast timers are set if `fast_dot1x_timers` knob is enabled. \"retries\" are set to value of `auth_servers_timeout`. \"max-requests\" is also set when setting `auth_servers_retries` is set to default value to 3.",
                    "contentEncoding": "int32",
                    "default": 2,
                    "examples": [
                      3
                    ]
                  },
                  "auth_servers_timeout": {
                    "maximum": 30.0,
                    "minimum": 1.0,
                    "type": "integer",
                    "description": "Radius auth session timeout. Following fast timers are set if `fast_dot1x_timers` knob is enabled. \"quite-period\" and \"transmit-period\" are set to half the value of `auth_servers_timeout`. \"supplicant-timeout\" is also set when setting `auth_servers_timeout` is set to default value of 10.",
                    "contentEncoding": "int32",
                    "default": 5,
                    "examples": [
                      5
                    ]
                  },
                  "coa_enabled": {
                    "type": "boolean",
                    "description": "Allows a RADIUS server to dynamically modify the authorization status of a user session.",
                    "default": false
                  },
                  "coa_port": {
                    "maximum": 65535.0,
                    "minimum": 1.0,
                    "type": "integer",
                    "description": "the communication port used for \u201cChange of Authorization\u201d (CoA) messages",
                    "contentEncoding": "int32",
                    "examples": [
                      3799
                    ]
                  },
                  "enabled": {
                    "type": "boolean",
                    "description": "When enabled:\n  * `auth_servers` is ignored\n  * `acct_servers` is ignored\n  * `auth_servers_*` are ignored\n  * `coa_servers` is ignored\n  * `radsec` is ignored\n  * `coa_enabled` is assumed",
                    "default": false
                  },
                  "fast_dot1x_timers": {
                    "type": "boolean",
                    "description": "If set to true, sets default fast-timers with values calculated from `auth_servers_timeout` and `auth_server_retries`.",
                    "default": false
                  },
                  "network": {
                    "type": [
                      "string",
                      "null"
                    ],
                    "description": "Which network the mist nac server resides in",
                    "examples": [
                      "default"
                    ]
                  },
                  "source_ip": {
                    "type": [
                      "string",
                      "null"
                    ],
                    "description": "In case there is a static IP for this network, we can specify it using source ip",
                    "examples": [
                      "1.2.3.4"
                    ]
                  }
                }
              },
              "mx_tunnel_id": {
                "type": "string",
                "description": "If `forwarding`==`mxtunnel`, vlan_ids comes from mxtunnel",
                "contentEncoding": "uuid",
                "examples": [
                  "08cd7499-5841-51c8-e663-fb16b6f3b45e"
                ]
              },
              "mxtunnel_name": {
                "type": "string",
                "description": "If `forwarding`==`site_mxedge`, vlan_ids comes from site_mxedge (`mxtunnels` under site setting)"
              },
              "port_auth": {
                "type": "string",
                "description": "When doing port auth. enum: `dot1x`, `none`"
              },
              "port_vlan_id": {
                "maximum": 4094.0,
                "minimum": 1.0,
                "type": "integer",
                "description": "If `forwarding`==`limited`",
                "contentEncoding": "int32",
                "examples": [
                  1
                ]
              },
              "radius_config": {
                "type": "object",
                "properties": {
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
                    "description": "radius auth session retries",
                    "contentEncoding": "int32",
                    "default": 3
                  },
                  "auth_servers_timeout": {
                    "type": "integer",
                    "description": "radius auth session timeout",
                    "contentEncoding": "int32",
                    "default": 5
                  },
                  "coa_enabled": {
                    "type": "boolean",
                    "default": false
                  },
                  "coa_port": {
                    "maximum": 65535.0,
                    "minimum": 1.0,
                    "type": "integer",
                    "contentEncoding": "int32",
                    "default": 3799
                  },
                  "network": {
                    "type": "string",
                    "description": "use `network`or `source_ip`, which network the RADIUS server resides, if there's static IP for this network, we'd use it as source-ip"
                  },
                  "source_ip": {
                    "type": "string",
                    "description": "use `network`or `source_ip`"
                  }
                },
                "description": "Junos Radius config"
              },
              "radsec": {
                "type": "object",
                "properties": {
                  "coa_enabled": {
                    "type": "boolean",
                    "default": false
                  },
                  "enabled": {
                    "type": "boolean"
                  },
                  "idle_timeout": {
                    "type": "object",
                    "description": "Radsec Idle Timeout in seconds. Default is 60"
                  },
                  "mxcluster_ids": {
                    "type": "array",
                    "items": {
                      "type": "string",
                      "contentEncoding": "uuid"
                    },
                    "description": "To use Org mxedges when this WLAN does not use mxtunnel, specify their mxcluster_ids. Org mxedge(s) identified by mxcluster_ids"
                  },
                  "proxy_hosts": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "Default is site.mxedge.radsec.proxy_hosts which must be a superset of all `wlans[*].radsec.proxy_hosts`. When `radsec.proxy_hosts` are not used, tunnel peers (org or site mxedges) are used irrespective of `use_site_mxedge`"
                  },
                  "server_name": {
                    "type": "string",
                    "description": "Name of the server to verify (against the cacerts in Org Setting). Only if not Mist Edge.",
                    "examples": [
                      "radsec.abc.com"
                    ]
                  },
                  "servers": {
                    "uniqueItems": true,
                    "type": "array",
                    "items": {
                      "title": "radsec_server",
                      "type": "object",
                      "properties": {
                        "host": {
                          "type": "string",
                          "examples": [
                            "1.1.1.1"
                          ]
                        },
                        "port": {
                          "maximum": 65535.0,
                          "minimum": 1.0,
                          "type": "integer",
                          "contentEncoding": "int32",
                          "examples": [
                            1812
                          ]
                        }
                      }
                    },
                    "description": "List of RadSec Servers. Only if not Mist Edge."
                  },
                  "use_mxedge": {
                    "type": "boolean",
                    "description": "use mxedge(s) as RadSec Proxy"
                  },
                  "use_site_mxedge": {
                    "type": "boolean",
                    "description": "To use Site mxedges when this WLAN does not use mxtunnel",
                    "default": false
                  }
                },
                "description": "RadSec settings"
              },
              "vlan_id": {
                "maximum": 4094.0,
                "minimum": 1.0,
                "type": "integer",
                "description": "Optional to specify the vlan id for a tunnel if forwarding is for `wxtunnel`, `mxtunnel` or `site_mxedge`.\n  * if vlan_id is not specified then it will use first one in vlan_ids[] of the mxtunnel.\n  * if forwarding == site_mxedge, vlan_ids comes from site_mxedge (`mxtunnels` under site setting)",
                "contentEncoding": "int32",
                "examples": [
                  9
                ]
              },
              "vlan_ids": {
                "type": "string",
                "description": "If `forwarding`==`limited`, comma separated list of additional vlan ids allowed on this port",
                "examples": [
                  "10,20,30"
                ]
              },
              "wxtunnel_id": {
                "type": "string",
                "description": "If `forwarding`==`wxtunnel`, the port is bridged to the vlan of the session",
                "contentEncoding": "uuid",
                "examples": [
                  "7dae216d-7c98-a51b-e068-dd7d477b7216"
                ]
              },
              "wxtunnel_remote_id": {
                "type": "string",
                "description": "If `forwarding`==`wxtunnel`, the port is bridged to the vlan of the session",
                "examples": [
                  "wifiguest"
                ]
              }
            }
          },
          "description": "Property key is the AP model (e.g. \"AP32\")"
        }
      }
    },
    "ap_synthetic_test": {
      "type": "object",
      "properties": {
        "additional_vlan_ids": {
          "type": "object",
          "description": "List or Comma separated list of additional VLAN IDs (on the LAN side or from other WLANs) should we be forwarding bonjour queries/responses"
        }
      },
      "description": "AP Synthetic Test configuration"
    },
    "ap_updown_threshold": {
      "maximum": 240.0,
      "minimum": 0.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "Enable threshold-based device down delivery for AP devices only. When configured it takes effect for AP devices and `device_updown_threshold` is ignored.",
      "contentEncoding": "int32",
      "default": 0
    },
    "auto_placement": {
      "type": "object",
      "properties": {
        "orientation": {
          "type": "integer",
          "contentEncoding": "int32",
          "examples": [
            45
          ]
        },
        "x": {
          "type": "number",
          "examples": [
            30
          ]
        },
        "y": {
          "type": "number",
          "examples": [
            60
          ]
        }
      },
      "description": "If we're able to determine its x/y/orientation, this will be populated"
    },
    "auto_upgrade": {
      "type": "object",
      "properties": {
        "custom_versions": {
          "type": "object",
          "additionalProperties": {
            "type": "string"
          },
          "description": "Custom versions for different models. Property key is the model name (e.g. \"AP41\")",
          "examples": [
            {
              "AP21": "stable",
              "AP41": "0.1.5135",
              "AP61": "0.1.7215"
            }
          ]
        },
        "day_of_week": {
          "type": "string",
          "description": "enum: `any`, `fri`, `mon`, `sat`, `sun`, `thu`, `tue`, `wed`"
        },
        "enabled": {
          "type": "boolean",
          "description": "Whether auto upgrade should happen (Note that Mist may auto-upgrade if the version is not supported)",
          "default": false
        },
        "time_of_day": {
          "type": "string",
          "description": "`any` / HH:MM (24-hour format), upgrade will happen within up to 1-hour from this time",
          "examples": [
            "12:00"
          ]
        },
        "version": {
          "type": "string",
          "description": "desired version. enum: `beta`, `custom`, `stable`"
        }
      },
      "description": "Auto Upgrade Settings"
    },
    "auto_upgrade_esl": {
      "type": "object",
      "properties": {
        "allow_downgrade": {
          "type": "boolean",
          "description": "If true, it will allow downgrade to a lower version",
          "default": false
        },
        "custom_versions": {
          "type": "object",
          "additionalProperties": {
            "type": "string"
          },
          "description": "Custom versions for different models. Property key is the model name (e.g. \"AP41\")",
          "examples": [
            {
              "AP41": "2.4.6",
              "AP61": "2.5.0"
            }
          ]
        },
        "day_of_week": {
          "type": "string",
          "description": "enum: `any`, `fri`, `mon`, `sat`, `sun`, `thu`, `tue`, `wed`"
        },
        "enabled": {
          "type": "boolean",
          "description": "Whether auto upgrade should happen (Note that Mist may auto-upgrade if the version is not supported)",
          "default": false
        },
        "time_of_day": {
          "type": "string",
          "description": "`any` / HH:MM (24-hour format), upgrade will happen within up to 1-hour from this time",
          "examples": [
            "12:00"
          ]
        },
        "version": {
          "type": "string",
          "examples": [
            "2.5.0"
          ]
        }
      },
      "description": "auto upgrade AP ESL. When both firmware and ESL auto-upgrade are enabled, ESL upgrade will be done only after firmware upgrade"
    },
    "auto_upgrade_linecard": {
      "type": "boolean",
      "default": true
    },
    "bgp_neighbor_updown_threshold": {
      "minimum": 0.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "enable threshold-based bgp neighbor down delivery.",
      "contentEncoding": "int32"
    },
    "blacklist_url": {
      "type": "string",
      "readOnly": true,
      "examples": [
        "https://papi.s3.amazonaws.com/blacklist/xxx..."
      ]
    },
    "ble_config": {
      "type": "object",
      "properties": {
        "beacon_enabled": {
          "type": "boolean",
          "description": "Whether Mist beacons is enabled",
          "default": true
        },
        "beacon_rate": {
          "type": "integer",
          "description": "Required if `beacon_rate_mode`==`custom`, 1-10, in number-beacons-per-second",
          "contentEncoding": "int32",
          "examples": [
            3
          ]
        },
        "beacon_rate_mode": {
          "type": "string",
          "description": "enum: `custom`, `default`"
        },
        "beam_disabled": {
          "type": "array",
          "items": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "description": "List of AP BLE location beam numbers (1-8) which should be disabled at the AP and not transmit location information (where beam 1 is oriented at the top the AP, growing counter-clock-wise, with 9 being the omni BLE beam)",
          "examples": [
            [
              1,
              3,
              6
            ]
          ]
        },
        "custom_ble_packet_enabled": {
          "type": "boolean",
          "description": "Can be enabled if `beacon_enabled`==`true`, whether to send custom packet",
          "default": false
        },
        "custom_ble_packet_frame": {
          "type": "string",
          "description": "The custom frame to be sent out in this beacon. The frame must be a hexstring",
          "examples": [
            "0x........"
          ]
        },
        "custom_ble_packet_freq_msec": {
          "minimum": 0.0,
          "type": "integer",
          "description": "Frequency (msec) of data emitted by custom ble beacon",
          "contentEncoding": "int32",
          "default": 0,
          "examples": [
            300
          ]
        },
        "eddystone_uid_adv_power": {
          "maximum": 20.0,
          "minimum": -100.0,
          "type": "integer",
          "description": "Advertised TX Power, -100 to 20 (dBm), omit this attribute to use default",
          "contentEncoding": "int32",
          "default": 0,
          "examples": [
            -65
          ]
        },
        "eddystone_uid_beams": {
          "type": "string",
          "examples": [
            "2-4,7"
          ]
        },
        "eddystone_uid_enabled": {
          "type": "boolean",
          "description": "Only if `beacon_enabled`==`false`, Whether Eddystone-UID beacon is enabled",
          "default": false
        },
        "eddystone_uid_freq_msec": {
          "type": "integer",
          "description": "Frequency (msec) of data emit by Eddystone-UID beacon",
          "contentEncoding": "int32",
          "default": 0,
          "examples": [
            200
          ]
        },
        "eddystone_uid_instance": {
          "type": "string",
          "description": "Eddystone-UID instance for the device",
          "examples": [
            "5c5b35000001"
          ]
        },
        "eddystone_uid_namespace": {
          "type": "string",
          "description": "Eddystone-UID namespace",
          "examples": [
            "2818e3868dec25629ede"
          ]
        },
        "eddystone_url_adv_power": {
          "maximum": 20.0,
          "minimum": -100.0,
          "type": "integer",
          "description": "Advertised TX Power, -100 to 20 (dBm), omit this attribute to use default",
          "contentEncoding": "int32",
          "default": 0,
          "examples": [
            -65
          ]
        },
        "eddystone_url_beams": {
          "type": "string",
          "examples": [
            "2-4,7"
          ]
        },
        "eddystone_url_enabled": {
          "type": "boolean",
          "description": "Only if `beacon_enabled`==`false`, Whether Eddystone-URL beacon is enabled",
          "default": false
        },
        "eddystone_url_freq_msec": {
          "type": "integer",
          "description": "Frequency (msec) of data emit by Eddystone-UID beacon",
          "contentEncoding": "int32",
          "default": 0,
          "examples": [
            1000
          ]
        },
        "eddystone_url_url": {
          "type": "string",
          "description": "URL pointed by Eddystone-URL beacon",
          "examples": [
            "https://www.abc.com"
          ]
        },
        "ibeacon_adv_power": {
          "maximum": 20.0,
          "minimum": -100.0,
          "type": "integer",
          "description": "Advertised TX Power, -100 to 20 (dBm), omit this attribute to use default",
          "contentEncoding": "int32",
          "default": 0,
          "examples": [
            -65
          ]
        },
        "ibeacon_beams": {
          "type": "string",
          "examples": [
            "2-4,7"
          ]
        },
        "ibeacon_enabled": {
          "type": "boolean",
          "description": "Can be enabled if `beacon_enabled`==`true`, whether to send iBeacon",
          "default": false
        },
        "ibeacon_freq_msec": {
          "type": "integer",
          "description": "Frequency (msec) of data emit for iBeacon",
          "contentEncoding": "int32",
          "default": 0
        },
        "ibeacon_major": {
          "maximum": 65535.0,
          "minimum": 1.0,
          "type": [
            "integer",
            "null"
          ],
          "description": "Major number for iBeacon",
          "contentEncoding": "int32",
          "examples": [
            1234
          ]
        },
        "ibeacon_minor": {
          "maximum": 65535.0,
          "minimum": 1.0,
          "type": [
            "integer",
            "null"
          ],
          "description": "Minor number for iBeacon",
          "contentEncoding": "int32",
          "examples": [
            1234
          ]
        },
        "ibeacon_uuid": {
          "type": "string",
          "description": "Optional, if not specified, the same UUID as the beacon will be used",
          "contentEncoding": "uuid",
          "examples": [
            "f3f17139-704a-f03a-2786-0400279e37c3"
          ]
        },
        "power": {
          "maximum": 10.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "Required if `power_mode`==`custom`; else use `power_mode` as default",
          "contentEncoding": "int32",
          "default": 9,
          "examples": [
            6
          ]
        },
        "power_mode": {
          "type": "string",
          "description": "enum: `custom`, `default`"
        }
      },
      "description": "BLE AP settings"
    },
    "config_auto_revert": {
      "type": "boolean",
      "description": "Whether to enable ap auto config revert",
      "default": false
    },
    "config_push_policy": {
      "type": "object",
      "properties": {
        "no_push": {
          "type": "boolean",
          "description": "Stop any new config from being pushed to the device",
          "default": false
        },
        "push_window": {
          "type": "object",
          "properties": {
            "enabled": {
              "type": "boolean",
              "default": false
            },
            "hours": {
              "type": "object",
              "properties": {
                "fri": {
                  "type": "string",
                  "description": "Hour range of the day (e.g. `09:00-17:00`). If the hour is not defined then it's treated as 00:00-23:59.",
                  "examples": [
                    "09:00-17:00"
                  ]
                },
                "mon": {
                  "type": "string",
                  "description": "Hour range of the day (e.g. `09:00-17:00`). If the hour is not defined then it's treated as 00:00-23:59.",
                  "examples": [
                    "09:00-17:00"
                  ]
                },
                "sat": {
                  "type": "string",
                  "description": "Hour range of the day (e.g. `09:00-17:00`). If the hour is not defined then it's treated as 00:00-23:59.",
                  "examples": [
                    "09:00-17:00"
                  ]
                },
                "sun": {
                  "type": "string",
                  "description": "Hour range of the day (e.g. `09:00-17:00`). If the hour is not defined then it's treated as 00:00-23:59.",
                  "examples": [
                    "09:00-17:00"
                  ]
                },
                "thu": {
                  "type": "string",
                  "description": "Hour range of the day (e.g. `09:00-17:00`). If the hour is not defined then it's treated as 00:00-23:59.",
                  "examples": [
                    "09:00-17:00"
                  ]
                },
                "tue": {
                  "type": "string",
                  "description": "Hour range of the day (e.g. `09:00-17:00`). If the hour is not defined then it's treated as 00:00-23:59.",
                  "examples": [
                    "09:00-17:00"
                  ]
                },
                "wed": {
                  "type": "string",
                  "description": "Hour range of the day (e.g. `09:00-17:00`). If the hour is not defined then it's treated as 00:00-23:59.",
                  "examples": [
                    "09:00-17:00"
                  ]
                }
              },
              "description": "Days/Hours of operation filter, the available days (mon, tue, wed, thu, fri, sat, sun)"
            }
          },
          "description": "If enabled, new config will only be pushed to device within the specified time window"
        }
      },
      "description": "Mist also uses some heuristic rules to prevent destructive configs from being pushed"
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "critical_url_monitoring": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": true
        },
        "monitors": {
          "type": "array",
          "items": {
            "title": "site_setting_critical_url_monitoring_monitor",
            "type": "object",
            "properties": {
              "url": {
                "type": "string",
                "examples": [
                  "http://50.1.3.5:8080"
                ]
              },
              "vlan_id": {
                "type": "object"
              }
            }
          },
          "description": ""
        }
      },
      "description": "You can define some URLs that's critical to site operations the latency will be captured and considered for site health"
    },
    "device_updown_threshold": {
      "maximum": 240.0,
      "minimum": 0.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "By default, device_updown_threshold, if set, will apply to all devices types if different values for specific device type is desired, use the following",
      "contentEncoding": "int32",
      "default": 0
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
    "disabled_system_defined_port_usages": {
      "type": "array",
      "items": {
        "title": "system_defined_port_usages",
        "enum": [
          "ap",
          "iot",
          "uplink"
        ],
        "type": "string",
        "description": "system-default port usages. enum: `ap`, `iot`, `uplink``"
      },
      "description": "If some system-default port usages are not desired - namely, ap / iot / uplink"
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
    "enable_unii_4": {
      "type": "boolean",
      "default": false
    },
    "engagement": {
      "type": "object",
      "properties": {
        "dwell_tag_names": {
          "type": "object",
          "properties": {
            "bounce": {
              "type": "string",
              "default": "Visitor",
              "examples": [
                "Bounce"
              ]
            },
            "engaged": {
              "type": "string",
              "default": "Associates",
              "examples": [
                "Engaged"
              ]
            },
            "passerby": {
              "type": "string",
              "default": "Passerby",
              "examples": [
                "Passer By"
              ]
            },
            "stationed": {
              "type": "string",
              "default": "Assets",
              "examples": [
                "Stationed"
              ]
            }
          },
          "description": "Name associated to each tag"
        },
        "dwell_tags": {
          "type": "object",
          "properties": {
            "bounce": {
              "type": [
                "string",
                "null"
              ],
              "default": "301-14400"
            },
            "engaged": {
              "type": [
                "string",
                "null"
              ],
              "default": "14401-28800"
            },
            "passerby": {
              "type": [
                "string",
                "null"
              ],
              "default": "1-300"
            },
            "stationed": {
              "type": [
                "string",
                "null"
              ],
              "default": "28801-42000"
            }
          },
          "description": "add tags to visits within the duration (in seconds)"
        },
        "hours": {
          "type": "object",
          "properties": {
            "fri": {
              "type": "string",
              "description": "Hour range of the day (e.g. `09:00-17:00`). If the hour is not defined then it's treated as 00:00-23:59.",
              "examples": [
                "09:00-17:00"
              ]
            },
            "mon": {
              "type": "string",
              "description": "Hour range of the day (e.g. `09:00-17:00`). If the hour is not defined then it's treated as 00:00-23:59.",
              "examples": [
                "09:00-17:00"
              ]
            },
            "sat": {
              "type": "string",
              "description": "Hour range of the day (e.g. `09:00-17:00`). If the hour is not defined then it's treated as 00:00-23:59.",
              "examples": [
                "09:00-17:00"
              ]
            },
            "sun": {
              "type": "string",
              "description": "Hour range of the day (e.g. `09:00-17:00`). If the hour is not defined then it's treated as 00:00-23:59.",
              "examples": [
                "09:00-17:00"
              ]
            },
            "thu": {
              "type": "string",
              "description": "Hour range of the day (e.g. `09:00-17:00`). If the hour is not defined then it's treated as 00:00-23:59.",
              "examples": [
                "09:00-17:00"
              ]
            },
            "tue": {
              "type": "string",
              "description": "Hour range of the day (e.g. `09:00-17:00`). If the hour is not defined then it's treated as 00:00-23:59.",
              "examples": [
                "09:00-17:00"
              ]
            },
            "wed": {
              "type": "string",
              "description": "Hour range of the day (e.g. `09:00-17:00`). If the hour is not defined then it's treated as 00:00-23:59.",
              "examples": [
                "09:00-17:00"
              ]
            }
          },
          "description": "Days/Hours of operation filter, the available days (mon, tue, wed, thu, fri, sat, sun)"
        },
        "max_dwell": {
          "maximum": 68400.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "Max time, default is 43200(12h), max is 68400 (18h)",
          "contentEncoding": "int32",
          "default": 43200,
          "examples": [
            43200
          ]
        },
        "min_dwell": {
          "minimum": 0.0,
          "type": "integer",
          "description": "min time",
          "contentEncoding": "int32"
        }
      },
      "description": "**Note**: if hours does not exist, it's treated as everyday of the week, 00:00-23:59. Currently, we don't allow multiple ranges for the same day"
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
    "flags": {
      "type": "object",
      "additionalProperties": {
        "type": "string"
      },
      "description": "Name/val pair objects for location engine to use"
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "gateway": {
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
    },
    "gateway_additional_config_cmds": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "additional CLI commands to append to the generated Junos config. **Note**: no check is done"
    },
    "gateway_mgmt": {
      "type": "object",
      "properties": {
        "admin_sshkeys": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "For SSR only, as direct root access is not allowed",
          "examples": [
            [
              "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAA...Wxa6p6UW0ZbcP john@host"
            ]
          ]
        },
        "app_probing": {
          "title": "app_probing",
          "type": "object",
          "properties": {
            "apps": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": "APp-keys from [List Applications]($e/Constants%20Definitions/listApplications)",
              "examples": [
                [
                  "facebook"
                ]
              ]
            },
            "custom_apps": {
              "type": "array",
              "items": {
                "title": "app_probing_custom_app",
                "type": "object",
                "properties": {
                  "address": {
                    "type": "string",
                    "description": "Required if `protocol`==`icmp`",
                    "examples": [
                      "192.168.1.1"
                    ]
                  },
                  "app_type": {
                    "type": "string"
                  },
                  "hostnames": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "If `protocol`==`http`",
                    "examples": [
                      [
                        "https://www.abc.com"
                      ]
                    ]
                  },
                  "key": {
                    "type": "string"
                  },
                  "name": {
                    "type": "string",
                    "examples": [
                      "pos_app"
                    ]
                  },
                  "network": {
                    "type": "string",
                    "examples": [
                      "lan"
                    ]
                  },
                  "packetSize": {
                    "maximum": 65400.0,
                    "minimum": 0.0,
                    "type": "integer",
                    "description": "If `protocol`==`icmp`",
                    "contentEncoding": "int32"
                  },
                  "protocol": {
                    "type": "string",
                    "description": "enum: `http`, `icmp`"
                  },
                  "url": {
                    "type": "string",
                    "description": "If `protocol`==`http`",
                    "examples": [
                      "www.abc.com"
                    ]
                  },
                  "vrf": {
                    "type": "string",
                    "examples": [
                      "lan"
                    ]
                  }
                }
              },
              "description": ""
            },
            "enabled": {
              "type": "boolean"
            }
          }
        },
        "app_usage": {
          "type": "boolean",
          "description": "Consumes uplink bandwidth, requires WA license"
        },
        "auto_signature_update": {
          "title": "site_setting_gateway_mgmt_auto_signature_update",
          "type": "object",
          "properties": {
            "day_of_week": {
              "type": "string",
              "description": "enum: `any`, `fri`, `mon`, `sat`, `sun`, `thu`, `tue`, `wed`"
            },
            "enable": {
              "type": "boolean",
              "default": true
            },
            "time_of_day": {
              "type": "string",
              "description": "Optional, Mist will decide the timing"
            }
          }
        },
        "config_revert_timer": {
          "maximum": 30.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "Rollback timer for commit confirmed",
          "contentEncoding": "int32",
          "default": 10
        },
        "disable_console": {
          "type": "boolean",
          "description": "For SSR and SRX, disable console port",
          "default": false
        },
        "disable_oob": {
          "type": "boolean",
          "description": "For SSR and SRX, disable management interface",
          "default": false
        },
        "disable_usb": {
          "type": "boolean",
          "description": "For SSR and SRX, disable usb interface",
          "default": false
        },
        "fips_enabled": {
          "type": "boolean",
          "default": false
        },
        "probe_hosts": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "",
          "examples": [
            [
              "8.8.8.8"
            ]
          ]
        },
        "probe_hostsv6": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "",
          "examples": [
            [
              "2001:4860:4860::8888"
            ]
          ]
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
        "root_password": {
          "type": "string",
          "description": "SRX only"
        },
        "security_log_source_address": {
          "type": "string",
          "examples": [
            "192.168.1.1"
          ]
        },
        "security_log_source_interface": {
          "type": "string",
          "examples": [
            "ge-0/0/1.0"
          ]
        }
      },
      "description": "Gateway Site settings"
    },
    "gateway_tunnel_updown_threshold": {
      "minimum": 0.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "enable threshold-based gateway tunnel (secure edge tunnels) up-down delivery.",
      "contentEncoding": "int32"
    },
    "gateway_updown_threshold": {
      "maximum": 240.0,
      "minimum": 0.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "Enable threshold-based device down delivery for Gateway devices only. When configured it takes effect for GW devices and `device_updown_threshold` is ignored.",
      "contentEncoding": "int32",
      "default": 0
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
    "juniper_srx": {
      "title": "site_setting_juniper_srx",
      "type": "object",
      "properties": {
        "auto_upgrade": {
          "type": "object",
          "properties": {
            "custom_versions": {
              "type": "object",
              "additionalProperties": {
                "type": "string"
              },
              "description": "Property key is the SRX Hardware model (e.g. \"SRX4600\")"
            },
            "enabled": {
              "type": "boolean",
              "default": false
            },
            "snapshot": {
              "type": "boolean",
              "default": false
            },
            "version": {
              "type": "string",
              "description": "Firmware version to deploy (e.g. 23.4R2-S5.5). Optional, used when custom_versions not specified",
              "examples": [
                "23.4R2-S5.5"
              ]
            }
          },
          "description": "auto_upgrade device first time it is onboarded"
        },
        "gateways": {
          "type": "array",
          "items": {
            "title": "site_setting_juniper_srx_gateway",
            "type": "object",
            "properties": {
              "api_key": {
                "type": "string",
                "examples": [
                  "5abf7c8a-1a1c-4398-ba2d-b0c297094d1a"
                ]
              },
              "api_password": {
                "type": "string",
                "examples": [
                  "abc@123"
                ]
              },
              "api_url": {
                "type": "string",
                "examples": [
                  "https://23.43.12.78:8443"
                ]
              }
            }
          },
          "description": ""
        },
        "send_mist_nac_user_info": {
          "type": "boolean"
        }
      }
    },
    "led": {
      "type": "object",
      "properties": {
        "brightness": {
          "maximum": 255.0,
          "minimum": 0.0,
          "type": "integer",
          "contentEncoding": "int32",
          "default": 255,
          "examples": [
            255
          ]
        },
        "enabled": {
          "type": "boolean",
          "default": true
        }
      },
      "description": "LED AP settings"
    },
    "marvis": {
      "title": "marvis",
      "type": "object",
      "properties": {
        "auto_operations": {
          "title": "marvis_auto_operations",
          "type": "object",
          "properties": {
            "ap_insufficient_capacity": {
              "type": "boolean",
              "default": false
            },
            "ap_loop": {
              "type": "boolean",
              "default": false
            },
            "ap_non_compliant": {
              "type": "boolean",
              "default": false
            },
            "bounce_port_for_abnormal_poe_client": {
              "type": "boolean",
              "default": false
            },
            "disable_port_when_ddos_protocol_violation": {
              "type": "boolean",
              "default": false
            },
            "disable_port_when_rogue_dhcp_server_detected": {
              "type": "boolean",
              "default": false
            },
            "gateway_non_compliant": {
              "type": "boolean",
              "default": false
            },
            "switch_misconfigured_port": {
              "type": "boolean",
              "default": false
            },
            "switch_port_stuck": {
              "type": "boolean",
              "default": false
            }
          }
        }
      }
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
    "mxedge": {
      "type": "object",
      "properties": {
        "mist_das": {
          "type": "object",
          "properties": {
            "coa_servers": {
              "type": "array",
              "items": {
                "title": "mxedge_das_coa_server",
                "type": "object",
                "properties": {
                  "disable_event_timestamp_check": {
                    "type": "boolean",
                    "description": "Whether to disable Event-Timestamp Check",
                    "default": false
                  },
                  "enabled": {
                    "type": "boolean"
                  },
                  "host": {
                    "type": "string",
                    "description": "This server configured to send CoA|DM to mist edges"
                  },
                  "port": {
                    "type": "integer",
                    "description": "Mist edges will allow this host on this port",
                    "contentEncoding": "int32",
                    "default": 3799
                  },
                  "require_message_authenticator": {
                    "type": "boolean",
                    "description": "Whether to require Message-Authenticator in requests",
                    "default": false
                  },
                  "secret": {
                    "type": "string"
                  }
                }
              },
              "description": "Dynamic authorization clients configured to send CoA|DM to mist edges on port 3799"
            },
            "enabled": {
              "type": "boolean",
              "default": false
            }
          },
          "description": "Configure cloud-assisted dynamic authorization service on this cluster of mist edges"
        },
        "mist_nac": {
          "title": "mxcluster_nac",
          "type": "object",
          "properties": {
            "acct_server_port": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 1813
            },
            "auth_server_port": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 1812
            },
            "client_ips": {
              "type": "object",
              "additionalProperties": {
                "title": "mxcluster_nac_client_ip",
                "type": "object",
                "properties": {
                  "require_message_authenticator": {
                    "type": "boolean",
                    "description": "Whether to require Message-Authenticator in requests",
                    "default": false
                  },
                  "secret": {
                    "type": "string",
                    "description": "If different from above"
                  },
                  "site_id": {
                    "type": "string",
                    "description": "Present only for 3rd party clients",
                    "contentEncoding": "uuid",
                    "examples": [
                      "00000000-0000-0000-1234-000000000000"
                    ]
                  },
                  "vendor": {
                    "type": "string",
                    "description": "convention to be followed is : \"<vendor>-<variant>\", <variant> could be an os/platform/model/company. For ex: for cisco vendor, there could variants wrt os (such as ios, nxos etc), platforms (asa etc), or acquired companies (such as meraki, aironet) etc. enum: `aruba`, `cisco-aironet`, `cisco-dnac`, `cisco-ios`, `cisco-meraki`, `brocade`, `generic`, `juniper`, `paloalto`"
                  }
                }
              },
              "description": "Property key is the RADIUS Client IP/Subnet."
            },
            "enabled": {
              "type": "boolean",
              "default": false
            },
            "secret": {
              "type": "string",
              "examples": [
                "testing123"
              ]
            }
          }
        },
        "mist_nacedge": {
          "title": "mist_nacedge",
          "type": "object",
          "properties": {
            "auth_ttl": {
              "maximum": 2592000.0,
              "minimum": 60.0,
              "type": "integer",
              "description": "Cache of last auth result; in seconds",
              "contentEncoding": "int32",
              "default": 604800
            },
            "default_dot1x_vlan": {
              "type": "string",
              "description": "Default vlan for all dot1x devices, if different from default_vlan",
              "examples": [
                "20"
              ]
            },
            "default_vlan": {
              "type": "string",
              "description": "Default vlan to assign for devices not in the cache",
              "examples": [
                "test_vlan"
              ]
            },
            "enabled": {
              "type": "boolean"
            },
            "mxedge_hosts": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": "List of NAC Edges in this site",
              "examples": [
                [
                  "mxedge1.local"
                ]
              ]
            }
          }
        },
        "radsec": {
          "type": "object",
          "properties": {
            "acct_servers": {
              "uniqueItems": true,
              "type": "array",
              "items": {
                "title": "mxcluster_radsec_acct_server",
                "type": "object",
                "properties": {
                  "host": {
                    "type": "string",
                    "description": "IP / hostname of RADIUS server"
                  },
                  "port": {
                    "type": "integer",
                    "description": "Acct port of RADIUS server",
                    "contentEncoding": "int32",
                    "default": 1813
                  },
                  "secret": {
                    "type": "string",
                    "description": "Secret of RADIUS server"
                  },
                  "ssids": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "List of ssids that will use this server if match_ssid is true and match is found"
                  }
                }
              },
              "description": "List of RADIUS accounting servers, optional, order matters where the first one is treated as primary"
            },
            "auth_servers": {
              "uniqueItems": true,
              "type": "array",
              "items": {
                "title": "mxcluster_radsec_auth_server",
                "type": "object",
                "properties": {
                  "host": {
                    "type": "string",
                    "description": "IP / hostname of RADIUS server"
                  },
                  "inband_status_check": {
                    "type": "boolean",
                    "description": "Whether to enable inband status check",
                    "default": false
                  },
                  "inband_status_interval": {
                    "minimum": 0.0,
                    "type": "integer",
                    "description": "Inband status interval, in seconds",
                    "contentEncoding": "int32",
                    "default": 300
                  },
                  "keywrap_enabled": {
                    "type": "boolean",
                    "description": "If used for Mist APs, enable keywrap algorithm. Default is false"
                  },
                  "keywrap_format": {
                    "type": "object",
                    "description": "if used for Mist APs. enum: `ascii`, `hex`"
                  },
                  "keywrap_kek": {
                    "type": "string",
                    "description": "If used for Mist APs, encryption key"
                  },
                  "keywrap_mack": {
                    "type": "string",
                    "description": "If used for Mist APs, Message Authentication Code Key"
                  },
                  "port": {
                    "type": "integer",
                    "description": "Auth port of RADIUS server",
                    "contentEncoding": "int32",
                    "default": 1812
                  },
                  "retry": {
                    "type": "integer",
                    "description": "Authentication request retry",
                    "contentEncoding": "int32",
                    "default": 2
                  },
                  "secret": {
                    "type": "string",
                    "description": "Secret of RADIUS server"
                  },
                  "ssids": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": "List of ssids that will use this server if match_ssid is true and match is found"
                  },
                  "timeout": {
                    "type": "integer",
                    "description": "Authentication request timeout, in seconds",
                    "contentEncoding": "int32",
                    "default": 5
                  }
                }
              },
              "description": "List of RADIUS authentication servers, order matters where the first one is treated as primary"
            },
            "enabled": {
              "type": "boolean",
              "description": "Whether to enable service on Mist Edge i.e. RADIUS proxy over TLS"
            },
            "match_ssid": {
              "type": "boolean",
              "description": "Whether to match ssid in request message to select from a subset of RADIUS servers"
            },
            "nas_ip_source": {
              "type": "string",
              "description": "SSpecify NAS-IP-ADDRESS, NAS-IPv6-ADDRESS to use with auth_servers. enum: `any`, `oob`, `oob6`, `tunnel`, `tunnel6`"
            },
            "proxy_hosts": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": "Hostnames or IPs for Mist AP to use as the TLS Server (i.e. they are reachable from AP) in addition to `tunterm_hosts`"
            },
            "server_selection": {
              "type": "string",
              "description": "When ordered, Mist Edge will prefer and go back to the first radius server if possible. enum: `ordered`, `unordered`"
            },
            "src_ip_source": {
              "type": "string",
              "description": "Specify IP address to connect to auth_servers and acct_servers. enum: `any`, `oob`, `oob6`, `tunnel`, `tunnel6`"
            }
          },
          "description": "MxEdge RadSec Configuration"
        }
      },
      "description": "Site Mist Edges form a cluster of RadSec Proxy servers"
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
    "mxtunnels": {
      "type": "object",
      "properties": {
        "additional_mxtunnels": {
          "type": "object",
          "additionalProperties": {
            "title": "site_mxtunnel_additional_mxtunnel",
            "type": "object",
            "properties": {
              "clusters": {
                "type": "array",
                "items": {
                  "title": "site_mxtunnel_cluster",
                  "type": "object",
                  "properties": {
                    "name": {
                      "type": "string",
                      "examples": [
                        "primary"
                      ]
                    },
                    "tunterm_hosts": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "",
                      "examples": [
                        [
                          "mxedge1",
                          "mxedge2.local"
                        ]
                      ]
                    }
                  }
                },
                "description": "For AP, how to connect to tunterm or RadSec Proxy"
              },
              "hello_interval": {
                "maximum": 300.0,
                "minimum": 1.0,
                "type": "integer",
                "description": "In seconds, used as heartbeat to detect if a tunnel is alive. AP will try another peer after missing N hellos specified by hello_retries",
                "contentEncoding": "int32",
                "default": 60,
                "examples": [
                  60
                ]
              },
              "hello_retries": {
                "maximum": 30.0,
                "minimum": 2.0,
                "type": "integer",
                "contentEncoding": "int32",
                "default": 7,
                "examples": [
                  3
                ]
              },
              "protocol": {
                "type": "string",
                "description": "enum: `ip`, `udp`"
              },
              "vlan_ids": {
                "type": "array",
                "items": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "description": "",
                "examples": [
                  [
                    300,
                    310,
                    320
                  ]
                ]
              }
            }
          }
        },
        "ap_subnets": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of subnets where we allow AP to establish Mist Tunnels from"
        },
        "auto_preemption": {
          "type": "object",
          "properties": {
            "day_of_week": {
              "type": "string",
              "description": "enum: `any`, `fri`, `mon`, `sat`, `sun`, `thu`, `tue`, `wed`"
            },
            "enabled": {
              "type": "boolean",
              "description": "Whether auto preemption should happen",
              "default": false
            },
            "time_of_day": {
              "type": "string",
              "description": "`any` / HH:MM (24-hour format)",
              "default": "any",
              "examples": [
                "12:00"
              ]
            }
          },
          "description": "Schedule to preempt ap\u2019s which are not connected to preferred peer"
        },
        "clusters": {
          "type": "array",
          "items": {
            "title": "site_mxtunnel_cluster",
            "type": "object",
            "properties": {
              "name": {
                "type": "string",
                "examples": [
                  "primary"
                ]
              },
              "tunterm_hosts": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "",
                "examples": [
                  [
                    "mxedge1",
                    "mxedge2.local"
                  ]
                ]
              }
            }
          },
          "description": "For AP, how to connect to tunterm or RadSec Proxy"
        },
        "created_time": {
          "type": "number",
          "description": "When the object has been created, in epoch",
          "readOnly": true
        },
        "enabled": {
          "type": "boolean"
        },
        "for_site": {
          "type": "boolean",
          "readOnly": true
        },
        "hello_interval": {
          "maximum": 300.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "In seconds, used as heartbeat to detect if a tunnel is alive. AP will try another peer after missing N hellos specified by hello_retries",
          "contentEncoding": "int32",
          "default": 60,
          "examples": [
            60
          ]
        },
        "hello_retries": {
          "maximum": 30.0,
          "minimum": 2.0,
          "type": "integer",
          "contentEncoding": "int32",
          "default": 7,
          "examples": [
            3
          ]
        },
        "hosts": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Hostnames or IPs where a Mist Tunnel will use as the Peer (i.e. they are reachable from AP)"
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
        "mtu": {
          "maximum": 1500.0,
          "minimum": 0.0,
          "type": "integer",
          "description": "0 to enable MTU, 552-1500 to start MTU with a lower MTU",
          "contentEncoding": "int32",
          "default": 0,
          "examples": [
            1100
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
        "protocol": {
          "type": "string",
          "description": "enum: `ip`, `udp`"
        },
        "radsec": {
          "title": "site_mxtunnel_radsec",
          "type": "object",
          "properties": {
            "acct_servers": {
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
            "auth_servers": {
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
            "enabled": {
              "type": "boolean",
              "default": false
            },
            "use_mxedge": {
              "type": "boolean"
            }
          }
        },
        "site_id": {
          "type": "string",
          "contentEncoding": "uuid",
          "readOnly": true,
          "examples": [
            "441a1214-6928-442a-8e92-e1d34b8ec6a6"
          ]
        },
        "vlan_ids": {
          "type": "array",
          "items": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "description": "List of vlan_ids that will be used"
        }
      },
      "description": "Site MxTunnel"
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
      "description": "List of NTP servers"
    },
    "occupancy": {
      "type": "object",
      "properties": {
        "assets_enabled": {
          "type": "boolean",
          "description": "Indicate whether named BLE assets should be included in the zone occupancy calculation",
          "default": false
        },
        "clients_enabled": {
          "type": "boolean",
          "description": "Indicate whether connected Wi-Fi clients should be included in the zone occupancy calculation",
          "default": true
        },
        "min_duration": {
          "type": "integer",
          "description": "Minimum duration",
          "contentEncoding": "int32",
          "default": 3000,
          "examples": [
            3000
          ]
        },
        "sdkclients_enabled": {
          "type": "boolean",
          "description": "Indicate whether SDK clients should be included in the zone occupancy calculation",
          "default": false
        },
        "unconnected_clients_enabled": {
          "type": "boolean",
          "description": "Indicate whether unconnected Wi-Fi clients should be included in the zone occupancy calculation",
          "default": false
        }
      },
      "description": "Occupancy Analytics settings"
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
    "paloalto_networks": {
      "title": "site_setting_paloalto_networks",
      "type": "object",
      "properties": {
        "gateways": {
          "type": "array",
          "items": {
            "title": "site_setting_paloalto_network_gateway",
            "type": "object",
            "properties": {
              "api_key": {
                "type": "string",
                "examples": [
                  "5abf7c8a-1a1c-4398-ba2d-b0c297094d1a"
                ]
              },
              "api_url": {
                "type": "string",
                "examples": [
                  "https://23.43.12.78:8443"
                ]
              }
            }
          },
          "description": ""
        },
        "send_mist_nac_user_info": {
          "type": "boolean",
          "default": false
        }
      }
    },
    "persist_config_on_device": {
      "type": "boolean",
      "description": "Whether to store the config on AP",
      "default": false
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
    "radio_config": {
      "type": "object",
      "properties": {
        "allow_rrm_disable": {
          "type": "boolean",
          "default": false
        },
        "ant_gain_24": {
          "minimum": 0.0,
          "type": "integer",
          "description": "Antenna gain for 2.4G - for models with external antenna only",
          "contentEncoding": "int32",
          "examples": [
            4
          ]
        },
        "ant_gain_5": {
          "minimum": 0.0,
          "type": "integer",
          "description": "Antenna gain for 5G - for models with external antenna only",
          "contentEncoding": "int32",
          "examples": [
            5
          ]
        },
        "ant_gain_6": {
          "minimum": 0.0,
          "type": "integer",
          "description": "Antenna gain for 6G - for models with external antenna only",
          "contentEncoding": "int32",
          "examples": [
            5
          ]
        },
        "antenna_mode": {
          "type": "string",
          "description": "enum: `1x1`, `2x2`, `3x3`, `4x4`, `default`"
        },
        "antenna_select": {
          "type": "string",
          "description": "Antenna Mode for AP which supports selectable antennas. enum: `\"\"` (default), `external`, `internal`"
        },
        "band_24": {
          "type": "object",
          "properties": {
            "allow_rrm_disable": {
              "type": "boolean",
              "default": false
            },
            "ant_gain": {
              "maximum": 10.0,
              "minimum": 0.0,
              "type": [
                "integer",
                "null"
              ],
              "contentEncoding": "int32",
              "default": 0
            },
            "antenna_mode": {
              "type": "string",
              "description": "enum: `1x1`, `2x2`, `3x3`, `4x4`, `default`"
            },
            "bandwidth": {
              "type": "integer",
              "description": "channel width for the 2.4GHz band. enum: `0`(disabled, response only), `20`, `40`"
            },
            "channel": {
              "maximum": 13.0,
              "minimum": 1.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "For Device. (primary) channel for the band, 0 means using the Site Setting",
              "contentEncoding": "int32",
              "examples": [
                6
              ]
            },
            "channels": {
              "type": [
                "array",
                "null"
              ],
              "items": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "description": "For RFTemplates. List of channels, null or empty array means auto",
              "default": []
            },
            "disabled": {
              "type": "boolean",
              "description": "Whether to disable the radio",
              "default": false
            },
            "power": {
              "maximum": 25.0,
              "minimum": 3.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "TX power of the radio. For Devices, 0 means auto. -1 / -2 / -3 / \u2026: treated as 0 / -1 / -2 / \u2026",
              "contentEncoding": "int32",
              "examples": [
                3
              ]
            },
            "power_max": {
              "maximum": 18.0,
              "minimum": 3.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "When power=0, max tx power to use, HW-specific values will be used if not set",
              "contentEncoding": "int32",
              "default": 17
            },
            "power_min": {
              "maximum": 18.0,
              "minimum": 3.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "When power=0, min tx power to use, HW-specific values will be used if not set",
              "contentEncoding": "int32",
              "default": 8
            },
            "preamble": {
              "type": "string",
              "description": "enum: `auto`, `long`, `short`"
            }
          },
          "description": "Radio Band AP settings"
        },
        "band_24_usage": {
          "type": "string",
          "description": "enum: `24`, `5`, `6`, `auto`"
        },
        "band_5": {
          "type": "object",
          "properties": {
            "allow_rrm_disable": {
              "type": "boolean",
              "default": false
            },
            "ant_gain": {
              "maximum": 10.0,
              "minimum": 0.0,
              "type": [
                "integer",
                "null"
              ],
              "contentEncoding": "int32",
              "default": 0
            },
            "antenna_beam_pattern": {
              "type": "string",
              "description": "enum: `narrow`, `medium`, `wide`"
            },
            "antenna_mode": {
              "type": "string",
              "description": "enum: `1x1`, `2x2`, `3x3`, `4x4`, `default`"
            },
            "bandwidth": {
              "type": "integer",
              "description": "channel width for the 5GHz band. enum: `0`(disabled, response only), `20`, `40`, `80`"
            },
            "channel": {
              "type": [
                "integer",
                "null"
              ],
              "description": "For Device. (primary) channel for the band, 0 means using the Site Setting",
              "contentEncoding": "int32",
              "examples": [
                100
              ]
            },
            "channels": {
              "type": [
                "array",
                "null"
              ],
              "items": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "description": "For RFTemplates. List of channels, null or empty array means auto",
              "default": []
            },
            "disabled": {
              "type": "boolean",
              "description": "Whether to disable the radio",
              "default": false
            },
            "power": {
              "maximum": 25.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "TX power of the radio. For Devices, 0 means auto. -1 / -2 / -3 / \u2026: treated as 0 / -1 / -2 / \u2026",
              "contentEncoding": "int32",
              "examples": [
                6
              ]
            },
            "power_max": {
              "maximum": 17.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "When power=0, max tx power to use, HW-specific values will be used if not set",
              "contentEncoding": "int32",
              "default": 17
            },
            "power_min": {
              "maximum": 17.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "When power=0, min tx power to use, HW-specific values will be used if not set",
              "contentEncoding": "int32",
              "default": 8
            },
            "preamble": {
              "type": "string",
              "description": "enum: `auto`, `long`, `short`"
            }
          },
          "description": "Radio Band AP settings"
        },
        "band_5_on_24_radio": {
          "type": "object",
          "properties": {
            "allow_rrm_disable": {
              "type": "boolean",
              "default": false
            },
            "ant_gain": {
              "maximum": 10.0,
              "minimum": 0.0,
              "type": [
                "integer",
                "null"
              ],
              "contentEncoding": "int32",
              "default": 0
            },
            "antenna_beam_pattern": {
              "type": "string",
              "description": "enum: `narrow`, `medium`, `wide`"
            },
            "antenna_mode": {
              "type": "string",
              "description": "enum: `1x1`, `2x2`, `3x3`, `4x4`, `default`"
            },
            "bandwidth": {
              "type": "integer",
              "description": "channel width for the 5GHz band. enum: `0`(disabled, response only), `20`, `40`, `80`"
            },
            "channel": {
              "type": [
                "integer",
                "null"
              ],
              "description": "For Device. (primary) channel for the band, 0 means using the Site Setting",
              "contentEncoding": "int32",
              "examples": [
                100
              ]
            },
            "channels": {
              "type": [
                "array",
                "null"
              ],
              "items": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "description": "For RFTemplates. List of channels, null or empty array means auto",
              "default": []
            },
            "disabled": {
              "type": "boolean",
              "description": "Whether to disable the radio",
              "default": false
            },
            "power": {
              "maximum": 25.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "TX power of the radio. For Devices, 0 means auto. -1 / -2 / -3 / \u2026: treated as 0 / -1 / -2 / \u2026",
              "contentEncoding": "int32",
              "examples": [
                6
              ]
            },
            "power_max": {
              "maximum": 17.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "When power=0, max tx power to use, HW-specific values will be used if not set",
              "contentEncoding": "int32",
              "default": 17
            },
            "power_min": {
              "maximum": 17.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "When power=0, min tx power to use, HW-specific values will be used if not set",
              "contentEncoding": "int32",
              "default": 8
            },
            "preamble": {
              "type": "string",
              "description": "enum: `auto`, `long`, `short`"
            }
          },
          "description": "Radio Band AP settings"
        },
        "band_6": {
          "type": "object",
          "properties": {
            "allow_rrm_disable": {
              "type": "boolean",
              "default": false
            },
            "ant_gain": {
              "maximum": 10.0,
              "minimum": 0.0,
              "type": [
                "integer",
                "null"
              ],
              "contentEncoding": "int32",
              "default": 0
            },
            "antenna_beam_pattern": {
              "type": "string",
              "description": "enum: `narrow`, `medium`, `wide`"
            },
            "antenna_mode": {
              "type": "string",
              "description": "enum: `1x1`, `2x2`, `3x3`, `4x4`, `default`"
            },
            "bandwidth": {
              "type": "integer",
              "description": "channel width for the 6GHz band. enum: `0`(disabled, response only), `20`, `40`, `80`, `160`"
            },
            "channel": {
              "type": [
                "integer",
                "null"
              ],
              "description": "For Device. (primary) channel for the band, 0 means using the Site Setting",
              "contentEncoding": "int32",
              "examples": [
                0
              ]
            },
            "channels": {
              "type": [
                "array",
                "null"
              ],
              "items": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "description": "For RFTemplates. List of channels, null or empty array means auto",
              "default": []
            },
            "disabled": {
              "type": "boolean",
              "description": "Whether to disable the radio",
              "default": false
            },
            "power": {
              "maximum": 25.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "TX power of the radio. For Devices, 0 means auto. -1 / -2 / -3 / \u2026: treated as 0 / -1 / -2 / \u2026",
              "contentEncoding": "int32",
              "examples": [
                7
              ]
            },
            "power_max": {
              "maximum": 18.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "When power=0, max tx power to use, HW-specific values will be used if not set",
              "contentEncoding": "int32",
              "default": 18
            },
            "power_min": {
              "maximum": 18.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "When power=0, min tx power to use, HW-specific values will be used if not set",
              "contentEncoding": "int32",
              "default": 8
            },
            "preamble": {
              "type": "string",
              "description": "enum: `auto`, `long`, `short`"
            },
            "standard_power": {
              "type": "boolean",
              "description": "For 6GHz Only, standard-power operation, AFC (Automatic Frequency Coordination) will be performed, and we'll fall back to Low Power Indoor if AFC failed",
              "default": false
            }
          },
          "description": "Radio Band AP settings"
        },
        "full_automatic_rrm": {
          "type": "boolean",
          "description": "Let RRM control everything, only the `channels` and `ant_gain` will be honored (i.e. disabled/bandwidth/power/band_24_usage are all controlled by RRM)",
          "default": false
        },
        "indoor_use": {
          "type": "boolean",
          "description": "To make an outdoor operate indoor. For an outdoor-ap, some channels are disallowed by default, this allows the user to use it as an indoor-ap",
          "default": false
        },
        "rrm_managed": {
          "type": "boolean",
          "description": "Enable RRM to manage all radio settings (ignores all band_xxx configs)"
        },
        "scanning_enabled": {
          "type": "boolean",
          "description": "Whether scanning radio is enabled",
          "examples": [
            true
          ]
        }
      },
      "description": "Radio AP settings"
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
    "report_gatt": {
      "type": "boolean",
      "description": "Whether AP should periodically connect to BLE devices and report GATT device info (device name, manufacturer name, serial number, battery %, temperature, humidity)",
      "default": false
    },
    "rogue": {
      "type": "object",
      "properties": {
        "allowed_vlan_ids": {
          "type": "array",
          "items": {
            "maximum": 4096.0,
            "minimum": 0.0,
            "type": "integer",
            "contentEncoding": "int32"
          },
          "description": "list of VLAN IDs on which rogue APs are ignored"
        },
        "enabled": {
          "type": "boolean",
          "description": "Whether rogue detection is enabled",
          "default": false
        },
        "honeypot_enabled": {
          "type": "boolean",
          "description": "Whether honeypot detection is enabled",
          "default": false
        },
        "min_duration": {
          "maximum": 59.0,
          "type": "integer",
          "description": "Minimum duration for a bssid to be considered neighbor",
          "contentEncoding": "int32",
          "default": 10,
          "examples": [
            10
          ]
        },
        "min_rogue_duration": {
          "maximum": 59.0,
          "type": "integer",
          "description": "Minimum duration for a bssid to be considered rogue",
          "contentEncoding": "int32",
          "default": 10,
          "examples": [
            10
          ]
        },
        "min_rogue_rssi": {
          "minimum": -85.0,
          "type": "integer",
          "description": "Minimum RSSI for an AP to be considered rogue",
          "contentEncoding": "int32",
          "default": -80,
          "examples": [
            -80
          ]
        },
        "min_rssi": {
          "minimum": -85.0,
          "type": "integer",
          "description": "Minimum RSSI for an AP to be considered neighbor (ignoring APs that\u2019s far away)",
          "contentEncoding": "int32",
          "default": -80,
          "examples": [
            -80
          ]
        },
        "whitelisted_bssids": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "list of BSSIDs to whitelist. Ex: \"cc-:8e-:6f-:d4-:bf-:16\", \"cc-8e-6f-d4-bf-16\", \"cc-73-*\", \"cc:82:*\"",
          "examples": [
            [
              "NeighborSSID"
            ]
          ]
        },
        "whitelisted_ssids": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of SSIDs to whitelist",
          "examples": [
            [
              "cc:8e:6f:d4:bf:16",
              "cc-8e-6f-d4-bf-16",
              "cc-73-*",
              "cc:82:*"
            ]
          ]
        }
      },
      "description": "Rogue site settings"
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
    "rtsa": {
      "type": "object",
      "properties": {
        "app_waking": {
          "type": "boolean",
          "default": false
        },
        "disable_dead_reckoning": {
          "type": "boolean"
        },
        "disable_pressure_sensor": {
          "type": "boolean",
          "default": false
        },
        "enabled": {
          "type": "boolean"
        },
        "track_asset": {
          "type": "boolean",
          "description": "Asset tracking related",
          "default": false
        }
      },
      "description": "Managed mobility"
    },
    "simple_alert": {
      "type": "object",
      "properties": {
        "arp_failure": {
          "title": "simple_alert_arp_failure",
          "type": "object",
          "properties": {
            "client_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 10
            },
            "duration": {
              "maximum": 60.0,
              "minimum": 5.0,
              "type": "integer",
              "description": "failing within minutes",
              "contentEncoding": "int32",
              "default": 20
            },
            "incident_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 10
            }
          }
        },
        "dhcp_failure": {
          "title": "simple_alert_dhcp_failure",
          "type": "object",
          "properties": {
            "client_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 10
            },
            "duration": {
              "maximum": 60.0,
              "minimum": 5.0,
              "type": "integer",
              "description": "failing within minutes",
              "contentEncoding": "int32",
              "default": 10
            },
            "incident_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 20
            }
          }
        },
        "dns_failure": {
          "title": "simple_alert_dns_failure",
          "type": "object",
          "properties": {
            "client_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 20
            },
            "duration": {
              "maximum": 60.0,
              "minimum": 5.0,
              "type": "integer",
              "description": "failing within minutes",
              "contentEncoding": "int32",
              "default": 10
            },
            "incident_count": {
              "type": "integer",
              "contentEncoding": "int32",
              "default": 30
            }
          }
        }
      },
      "description": "Set of heuristic rules will be enabled when marvis subscription is not available. It triggers when, in a Z minute window, there are more than Y distinct client encountering over X failures"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "skyatp": {
      "title": "site_setting_skyatp",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean"
        },
        "send_ip_mac_mapping": {
          "type": "boolean",
          "description": "Whether to send IP-MAC mapping to SkyATP",
          "default": false
        }
      }
    },
    "sle_thresholds": {
      "title": "sle_thresholds",
      "type": "object",
      "properties": {
        "capacity": {
          "maximum": 50.0,
          "minimum": 5.0,
          "type": "integer",
          "description": "Capacity, in %",
          "contentEncoding": "int32",
          "default": 20
        },
        "coverage": {
          "maximum": -60.0,
          "minimum": -90.0,
          "type": "integer",
          "description": "Coverage, in dBm",
          "contentEncoding": "int32",
          "default": -72
        },
        "throughput": {
          "maximum": 100.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "Throughput, in Mbps",
          "contentEncoding": "int32",
          "default": 10
        },
        "time-to-connect": {
          "maximum": 10.0,
          "minimum": 2.0,
          "type": "integer",
          "description": "Time to connect, in seconds",
          "contentEncoding": "int32",
          "default": 4
        }
      }
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
    "srx_app": {
      "title": "site_setting_srx_app",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        }
      }
    },
    "ssh_keys": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "When limit_ssh_access = true in Org Setting, list of SSH public keys provided by Mist Support to install onto APs (see Org:Setting)"
    },
    "ssr": {
      "title": "setting_ssr",
      "type": "object",
      "properties": {
        "auto_upgrade": {
          "type": "object",
          "properties": {
            "channel": {
              "type": "string",
              "description": "upgrade channel to follow. enum: `alpha`, `beta`, `stable`"
            },
            "custom_versions": {
              "type": "object",
              "additionalProperties": {
                "type": "string"
              },
              "description": "Property key is the SSR model (e.g. \"SSR130\")."
            },
            "enabled": {
              "type": "boolean",
              "default": false
            },
            "version": {
              "type": "string",
              "description": "Firmware version to deploy (e.g. 6.3.0-107.r1). Optional, used when custom_versions not specified",
              "examples": [
                "6.3.0-107.r1"
              ]
            }
          },
          "description": "auto_upgrade device first time it is onboarded"
        },
        "conductor_hosts": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of Conductor IP Addresses or Hosts to be used by the SSR Devices"
        },
        "conductor_token": {
          "type": "string",
          "description": "Token to be used by the SSR Devices to connect to the Conductor"
        },
        "disable_stats": {
          "type": "boolean",
          "description": "Disable stats collection on SSR devices"
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
          "description": "SSR proxy configuration to talk to Mist"
        }
      }
    },
    "status_portal": {
      "title": "site_setting_status_portal",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "hostnames": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": ""
        }
      }
    },
    "switch": {
      "title": "site_setting_switch",
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
        },
        "auto_upgrade": {
          "title": "switch_auto_upgrade",
          "type": "object",
          "properties": {
            "custom_versions": {
              "type": "object",
              "additionalProperties": {
                "type": "string"
              },
              "description": "Custom version to be used. The Property Key is the switch hardware and the property value is the firmware version",
              "examples": [
                {
                  "QFX5120-32C": "23.4R2-S2.1",
                  "QFX5130-32CD": "23.4R2-S2.3"
                }
              ]
            },
            "enabled": {
              "type": "boolean",
              "description": "Enable auto upgrade for the switch"
            },
            "snapshot": {
              "type": "boolean",
              "description": "Enable snapshot during the upgrade process",
              "default": false
            }
          }
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
    "switch_updown_threshold": {
      "maximum": 240.0,
      "minimum": 0.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "Enable threshold-based device down delivery for Switch devices only. When configured it takes effect for SW devices and `device_updown_threshold` is ignored.",
      "contentEncoding": "int32",
      "default": 0
    },
    "synthetic_test": {
      "title": "synthetictest_config",
      "type": "object",
      "properties": {
        "aggressiveness": {
          "type": "string",
          "description": "enum: `auto`, `high`, `low`"
        },
        "custom_probes": {
          "type": "object",
          "additionalProperties": {
            "title": "synthetictest_config_custom_probe",
            "type": "object",
            "properties": {
              "aggressiveness": {
                "type": "string",
                "description": "enum: `auto`, `high`, `low`"
              },
              "target": {
                "type": "string",
                "description": "Can be URL (e.g. http://x.com, https://x.com:8080/path/to/resource), IP address, or IP:port combination",
                "examples": [
                  "10.3.5.3:8080"
                ]
              },
              "threshold": {
                "type": "integer",
                "description": "In milliseconds",
                "contentEncoding": "int32",
                "examples": [
                  100
                ]
              },
              "type": {
                "type": "string",
                "description": "enum: `application`, `curl`, `icmp`, `reachability`, `tcp`"
              }
            }
          },
          "description": "Custom probes to be used for synthetic tests"
        },
        "disabled": {
          "type": "boolean",
          "default": false
        },
        "lan_networks": {
          "type": "array",
          "items": {
            "title": "synthetictest_config_lan_network",
            "type": "object",
            "properties": {
              "networks": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "List of networks to be used for synthetic tests",
                "examples": [
                  [
                    "pos-stations",
                    "pos-machines"
                  ]
                ]
              },
              "probes": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "app name comes from `custom_probes` above or /const/synthetic_test_probes"
              }
            },
            "description": "configure minis probes to be tested on lan networks of gateways"
          },
          "description": "List of networks to be used for synthetic tests"
        },
        "vlans": {
          "type": "array",
          "items": {
            "title": "synthetictest_config_vlan",
            "type": "object",
            "properties": {
              "custom_test_urls": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "",
                "examples": [
                  [
                    "https://www.abc.com/",
                    "https://10.3.5.1:8080/about"
                  ]
                ],
                "deprecated": true
              },
              "disabled": {
                "type": "boolean",
                "description": "For some vlans where we don't want this to run",
                "default": false
              },
              "probes": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "app name comes from `custom_probes` above or /const/synthetic_test_probes"
              },
              "vlan_ids": {
                "type": "array",
                "items": {
                  "oneOf": [
                    {
                      "type": "string"
                    },
                    {
                      "maximum": 4094.0,
                      "minimum": 1.0,
                      "type": "integer",
                      "contentEncoding": "int32"
                    }
                  ]
                },
                "description": "",
                "examples": [
                  [
                    10,
                    20,
                    "{{vlan}}"
                  ]
                ]
              }
            }
          },
          "description": "",
          "deprecated": true
        },
        "wan_speedtest": {
          "title": "synthetictest_config_wan_speedtest",
          "type": "object",
          "properties": {
            "enabled": {
              "type": "boolean"
            },
            "time_of_day": {
              "type": "string",
              "description": "`any` / HH:MM (24-hour format)",
              "default": "any",
              "examples": [
                "12:00"
              ]
            }
          }
        }
      }
    },
    "track_anonymous_devices": {
      "type": "boolean",
      "description": "Whether to track anonymous BLE assets (requires \u2018track_asset\u2019  enabled)",
      "default": false
    },
    "tunterm_monitoring": {
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
      },
      "description": ""
    },
    "tunterm_monitoring_disabled": {
      "type": "boolean",
      "default": false
    },
    "tunterm_multicast_config": {
      "title": "site_setting_tunterm_multicast_config",
      "type": "object",
      "properties": {
        "mdns": {
          "title": "site_setting_tunterm_multicast_config_mdns",
          "type": "object",
          "properties": {
            "enabled": {
              "type": "boolean",
              "default": false
            },
            "vlan_ids": {
              "type": "array",
              "items": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "description": "",
              "examples": [
                [
                  2,
                  3,
                  5
                ]
              ]
            }
          }
        },
        "multicast_all": {
          "type": "boolean",
          "default": false
        },
        "ssdp": {
          "title": "site_setting_tunterm_multicast_config_ssdp",
          "type": "object",
          "properties": {
            "enabled": {
              "type": "boolean",
              "default": false
            },
            "vlan_ids": {
              "type": "array",
              "items": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "description": "",
              "examples": [
                [
                  2,
                  3,
                  5
                ]
              ]
            }
          }
        }
      }
    },
    "uplink_port_config": {
      "type": "object",
      "properties": {
        "dot1x": {
          "type": "boolean",
          "description": "Whether to do 802.1x against uplink switch. When enabled, AP cert will be used to do EAP-TLS and the Org's CA Cert has to be provisioned at the switch",
          "default": false
        },
        "keep_wlans_up_if_down": {
          "type": "boolean",
          "description": "By default, WLANs are disabled when uplink is down. In some scenario, like SiteSurvey, one would want the AP to keep sending beacons.",
          "default": false
        }
      },
      "description": "AP Uplink port configuration"
    },
    "uses_description_from_port_usage": {
      "type": "boolean",
      "description": "by default, we only honor description provided in port_config. This allows fallback to those defined in port_usages",
      "default": false
    },
    "vars": {
      "type": "object",
      "additionalProperties": {
        "type": "string"
      },
      "description": "Dictionary of name->value, the vars can then be used in Wlans. This can overwrite those from Site Vars",
      "examples": [
        {
          "RADIUS_IP1": "172.31.2.5",
          "RADIUS_SECRET": "11s64632d"
        }
      ]
    },
    "vna": {
      "title": "site_setting_vna",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "Enable Virtual Network Assistant (using SUB-VNA license). This applied to AP / Switch / Gateway",
          "default": false
        }
      }
    },
    "vpn_path_updown_threshold": {
      "minimum": 0.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "enable threshold-based vpn path down delivery.",
      "contentEncoding": "int32"
    },
    "vpn_peer_updown_threshold": {
      "minimum": 0.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "enable threshold-based vpn peer down delivery.",
      "contentEncoding": "int32"
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
    },
    "vrrp_groups": {
      "type": "object",
      "additionalProperties": {
        "title": "vrrp_group",
        "type": "object",
        "properties": {
          "auth_key": {
            "type": "string",
            "description": "If `auth_type`==`md5`",
            "examples": [
              "auth-key-1"
            ]
          },
          "auth_password": {
            "type": "string",
            "description": "If `auth_type`==`simple`"
          },
          "auth_type": {
            "type": "string",
            "description": "enum: `md5`, `simple`"
          },
          "networks": {
            "type": "object",
            "additionalProperties": {
              "title": "vrrp_group_network",
              "type": "object",
              "properties": {
                "ip": {
                  "type": "string"
                }
              }
            },
            "description": "Property key is the network name",
            "examples": [
              {
                "data": {
                  "ip": "10.182.96.1"
                },
                "mgmt": {
                  "ip": "10.182.104.1"
                },
                "v10": {
                  "ip": "10.182.104.129"
                },
                "wap": {
                  "ip": "10.182.102.1"
                }
              }
            ]
          }
        },
        "description": "Junos VRRP group"
      },
      "description": "Property key is the vrrp group"
    },
    "vs_instance": {
      "type": "object",
      "additionalProperties": {
        "title": "vs_instance_property",
        "type": "object",
        "properties": {
          "networks": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          }
        }
      },
      "description": "Optional, for EX9200 only to segregate virtual-switches. Property key is the instance name"
    },
    "wan_vna": {
      "title": "site_setting_wan_vna",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        }
      }
    },
    "watched_station_url": {
      "type": "string",
      "readOnly": true,
      "examples": [
        "https://papi.s3.amazonaws.com/watched_station/xxx..."
      ]
    },
    "whitelist_url": {
      "type": "string",
      "readOnly": true,
      "examples": [
        "https://papi.s3.amazonaws.com/whitelist/xxx..."
      ]
    },
    "wids": {
      "type": "object",
      "properties": {
        "repeated_auth_failures": {
          "title": "site_wids_repeated_auth_failures",
          "type": "object",
          "properties": {
            "duration": {
              "type": "integer",
              "description": "Window where a trigger will be detected and action to be taken (in seconds)",
              "contentEncoding": "int32",
              "examples": [
                60
              ]
            },
            "threshold": {
              "type": "integer",
              "description": "Count of events to trigger",
              "contentEncoding": "int32"
            }
          }
        }
      },
      "description": "WIDS site settings"
    },
    "wifi": {
      "type": "object",
      "properties": {
        "cisco_enabled": {
          "type": "boolean",
          "default": true
        },
        "disable_11k": {
          "type": "boolean",
          "description": "Whether to disable 11k",
          "default": false
        },
        "disable_radios_when_power_constrained": {
          "type": "boolean",
          "default": false
        },
        "enable_arp_spoof_check": {
          "type": "boolean",
          "description": "When proxy_arp is enabled, check for arp spoofing.",
          "default": false
        },
        "enable_shared_radio_scanning": {
          "type": "boolean",
          "default": true
        },
        "enabled": {
          "type": "boolean",
          "description": "Enable Wi-Fi feature (using SUB-MAN license)",
          "default": true
        },
        "locate_connected": {
          "type": "boolean",
          "description": "Whether to locate connected clients",
          "default": true
        },
        "locate_unconnected": {
          "type": "boolean",
          "description": "Whether to locate unconnected clients",
          "default": false
        },
        "mesh_allow_dfs": {
          "type": "boolean",
          "description": "Whether to allow Mesh to use DFS channels. For DFS channels, Remote Mesh AP would have to do CAC when scanning for new Base AP, which is slow and will disrupt the connection. If roaming is desired, keep it disabled.",
          "default": false
        },
        "mesh_enable_crm": {
          "type": "boolean",
          "description": "Used to enable/disable CRM",
          "default": false
        },
        "mesh_enabled": {
          "type": "boolean",
          "description": "Whether to enable Mesh feature for the site",
          "default": false
        },
        "mesh_psk": {
          "type": [
            "string",
            "null"
          ],
          "description": "Optional passphrase of mesh networking, default is generated randomly"
        },
        "mesh_ssid": {
          "type": [
            "string",
            "null"
          ],
          "description": "Optional ssid of mesh networking, default is based on site_id"
        },
        "proxy_arp": {
          "type": "object",
          "description": "enum: `default`, `disabled`, `enabled`"
        }
      },
      "description": "Wi-Fi site settings"
    },
    "wired_vna": {
      "title": "site_setting_wired_vna",
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        }
      }
    },
    "zone_occupancy_alert": {
      "type": "object",
      "properties": {
        "email_notifiers": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of email addresses to send email notifications when the alert threshold is reached",
          "examples": [
            [
              "foo@juniper.net",
              "bar@juniper.net"
            ]
          ]
        },
        "enabled": {
          "type": "boolean",
          "description": "Indicate whether zone occupancy alert is enabled for the site",
          "default": false
        },
        "threshold": {
          "maximum": 30.0,
          "minimum": 0.0,
          "type": "integer",
          "description": "Sending zone-occupancy-alert webhook message only if a zone stays non-compliant (i.e. actual occupancy > occupancy_limit) for a minimum duration specified in the threshold, in minutes",
          "contentEncoding": "int32",
          "default": 5,
          "examples": [
            5
          ]
        }
      },
      "description": "Zone Occupancy alert site settings"
    }
  },
  "description": "Site Settings"
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

`mistapi.api.v1.sites.setting.getSiteSetting()`

## Usage Context

Retrieves the site settings (raw overrides, not derived). Includes auto-upgrade config, engagement settings, RTLS, gateway management, and feature flags.

## Gotchas

- This returns site-level overrides only. For the fully merged/derived config, use `GET_sites_site_id_setting_derived`.
- Extensive settings object — many optional fields.

## Related Endpoints

- [PUT_sites_site_id_setting.md](PUT_sites_site_id_setting.md) — Update site settings
- [GET_sites_site_id_setting_derived.md](GET_sites_site_id_setting_derived.md) — Fully derived settings

## MistHelper Notes

Used by Menus **4, 18, 103, 118, 119, 120** via `getSiteSetting` for configuration retrieval and auto-upgrade management.
