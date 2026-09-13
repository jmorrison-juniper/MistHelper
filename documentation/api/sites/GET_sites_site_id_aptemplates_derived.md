# listSiteApTemplatesDerived

> listSiteApTemplatesDerived

## HTTP

`GET /api/v1/sites/{site_id}/aptemplates/derived`

## Description

Get the list of derived AP Templates for a site

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
| resolve | boolean | No |  |  | Whether resolve the site variables |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "array",
  "items": {
    "title": "ap_template",
    "required": [
      "ap_matching"
    ],
    "type": "object",
    "properties": {
      "ap_matching": {
        "title": "ap_template_matching",
        "type": "object",
        "properties": {
          "enabled": {
            "type": "boolean"
          },
          "rules": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "title": "ap_template_matching_rule",
              "type": "object",
              "properties": {
                "match_model": {
                  "minLength": 1,
                  "type": "string"
                },
                "name": {
                  "minLength": 1,
                  "type": "string"
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
                  "description": "Property key is the interface(s) name (e.g. \"eth1,eth2\")"
                }
              }
            },
            "description": ""
          }
        }
      },
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
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "org_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
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
      "wifi": {
        "title": "ap_template_wifi",
        "type": "object",
        "properties": {
          "cisco_enabled": {
            "type": "boolean"
          },
          "disable_11k": {
            "type": "boolean",
            "default": false
          },
          "disable_radios_when_power_constrained": {
            "type": "boolean"
          },
          "enable_arp_spoof": {
            "type": "boolean"
          },
          "enable_shared_radio_scanning": {
            "type": "boolean",
            "default": false
          },
          "enabled": {
            "type": "boolean",
            "default": true
          },
          "locate_connected": {
            "type": "boolean",
            "default": false
          },
          "locate_unconnected": {
            "type": "boolean",
            "default": false
          },
          "mesh_allow_dfs": {
            "type": "boolean",
            "default": false
          },
          "mesh_enable_crm": {
            "type": "boolean"
          },
          "mesh_enabled": {
            "type": "boolean"
          },
          "proxy_arp": {
            "type": "boolean",
            "default": false
          }
        }
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "ap_matching": {
          "enabled": true,
          "rules": [
            {
              "match_model": "string",
              "name": "string",
              "port_config": {
                "eth1,eth2": {
                  "disabled": true,
                  "dynamic_vlan": {
                    "default_vlan_id": 999,
                    "enabled": true
                  },
                  "port_vlan_id": 1,
                  "vlan_id": 9,
                  "vlan_ids": "1, 10, 50"
                }
              }
            }
          ]
        },
        "created_time": 0,
        "for_site": true,
        "id": "497f6eca-6276-4993-bfeb-53cbbbba9f08",
        "modified_time": 0,
        "org_id": "a40f5d1f-d889-42e9-94ea-b9b33585fc6b",
        "site_id": "72771e6a-6f5e-4de4-a5b9-1266c4197811",
        "wifi": {
          "cisco_enabled": true,
          "disable_11k": false,
          "disable_radios_when_power_constrained": true,
          "enable_arp_spoof": true,
          "enable_shared_radio_scanning": false,
          "enabled": true,
          "locate_connected": false,
          "locate_unconnected": false,
          "mesh_allow_dfs": false,
          "mesh_enable_crm": true,
          "mesh_enabled": true,
          "proxy_arp": false
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.ap_templates.listSiteApTemplatesDerived()`

## Usage Context

Retrieves the effective (derived/resolved) AP template for a site, merging org and site-group templates with site-level overrides.

## Gotchas

- Shows the final computed template, not the raw definition.

## Related Endpoints

- [../orgs/GET_orgs_org_id_aptemplates.md](../orgs/GET_orgs_org_id_aptemplates.md) — Org AP templates
- [GET_sites_site_id_setting.md](GET_sites_site_id_setting.md) — Site settings

## MistHelper Notes

Not currently used by MistHelper directly. Menu **42** uses `listOrgApTemplates` at org level.
