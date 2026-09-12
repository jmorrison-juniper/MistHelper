# updateSiteWlan

> updateSiteWlan

## HTTP

`PUT /api/v1/sites/{site_id}/wlans/{wlan_id}`

## Description

Update Site WLAN

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| wlan_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "acct_immediate_update": {
      "type": "boolean",
      "description": "Enable coa-immediate-update and address-change-immediate-update on the access profile.",
      "default": false
    },
    "acct_interim_interval": {
      "maximum": 65535.0,
      "minimum": 0.0,
      "type": "integer",
      "description": "How frequently should interim accounting be reported, 60-65535. default is 0 (use one specified in Access-Accept request from RADIUS Server). Very frequent messages can affect the performance of the radius server, 600 and up is recommended when enabled",
      "contentEncoding": "int32",
      "default": 0,
      "examples": [
        0
      ]
    },
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
      "description": "List of RADIUS accounting servers, optional, order matters where the first one is treated as primary"
    },
    "airwatch": {
      "type": "object",
      "properties": {
        "api_key": {
          "type": "string",
          "description": "API Key",
          "examples": [
            "aHhlbGxvYXNkZmFzZGZhc2Rmc2RmCg==\""
          ]
        },
        "console_url": {
          "type": "string",
          "description": "Console URL",
          "examples": [
            "https://hs1.airwatchportals.com"
          ]
        },
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "password": {
          "type": "string",
          "description": "Password",
          "examples": [
            "user1"
          ]
        },
        "username": {
          "type": "string",
          "description": "Username",
          "examples": [
            "test123"
          ]
        }
      },
      "description": "Airwatch wlan settings"
    },
    "allow_ipv6_ndp": {
      "type": "boolean",
      "description": "Only applicable when `limit_bcast`==`true`, which allows or disallows ipv6 Neighbor Discovery packets to go through",
      "default": true
    },
    "allow_mdns": {
      "type": "boolean",
      "description": "Only applicable when `limit_bcast`==`true`, which allows mDNS / Bonjour packets to go through",
      "default": false
    },
    "allow_ssdp": {
      "type": "boolean",
      "description": "Only applicable when `limit_bcast`==`true`, which allows SSDP",
      "default": false
    },
    "ap_ids": {
      "type": [
        "array",
        "null"
      ],
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "List of device ids"
    },
    "app_limit": {
      "type": "object",
      "properties": {
        "apps": {
          "type": "object",
          "additionalProperties": {
            "type": "integer",
            "format": "int32"
          },
          "description": "Map from app key to bandwidth in kbps. \nProperty key is the app key, defined in Get Application List",
          "default": {},
          "examples": [
            {
              "dropbox": 300,
              "netflix": 60
            }
          ]
        },
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "wxtag_ids": {
          "type": "object",
          "additionalProperties": {
            "type": "integer",
            "format": "int32"
          },
          "description": "Map from wxtag_id of Hostname Wxlan Tags to bandwidth in kbps. Property key is the `wxtag_id`",
          "default": {},
          "examples": [
            {
              "f99862d9-2726-931f-7559-3dfdf5d070d3": 30
            }
          ]
        }
      },
      "description": "Bandwidth limiting for apps (applies to up/down)"
    },
    "app_qos": {
      "type": "object",
      "properties": {
        "apps": {
          "type": "object",
          "additionalProperties": {
            "title": "wlan_app_qos_apps_properties",
            "type": "object",
            "properties": {
              "dscp": {
                "type": "object",
                "description": "DSCP value range between 0 and 63"
              },
              "dst_subnet": {
                "type": "string",
                "description": "Subnet filter is not required but helps AP to only inspect certain traffic (thus reducing AP load)"
              },
              "src_subnet": {
                "type": "string",
                "description": "Subnet filter is not required but helps AP to only inspect certain traffic (thus reducing AP load)"
              }
            }
          },
          "examples": [
            {
              "skype-business-video": {
                "dscp": 32,
                "dst_subnet": "10.2.0.0/16",
                "src_subnet": "10.2.0.0/16"
              }
            }
          ]
        },
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "others": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "title": "wlan_app_qos_others_item",
            "type": "object",
            "properties": {
              "dscp": {
                "type": "object",
                "description": "DSCP value range between 0 and 63"
              },
              "dst_subnet": {
                "type": "string",
                "examples": [
                  "10.2.0.0/16"
                ]
              },
              "port_ranges": {
                "type": "string",
                "examples": [
                  "80,1024-6553"
                ]
              },
              "protocol": {
                "type": "string",
                "examples": [
                  "udp"
                ]
              },
              "src_subnet": {
                "type": "string",
                "examples": [
                  "10.2.0.0/16"
                ]
              }
            }
          },
          "description": ""
        }
      },
      "description": "APP qos wlan settings"
    },
    "apply_to": {
      "type": "string",
      "description": "enum: `aps`, `site`, `wxtags`"
    },
    "arp_filter": {
      "type": "boolean",
      "description": "Whether to enable smart arp filter",
      "default": false
    },
    "auth": {
      "type": "object",
      "properties": {
        "anticlog_threshold": {
          "maximum": 32.0,
          "minimum": 16.0,
          "type": "integer",
          "description": "SAE anti-clogging token threshold",
          "contentEncoding": "int32",
          "default": 16,
          "examples": [
            16
          ]
        },
        "eap_reauth": {
          "type": "boolean",
          "description": "Whether to trigger EAP reauth when the session ends",
          "default": false
        },
        "enable_mac_auth": {
          "type": "boolean",
          "description": "Whether to enable MAC Auth, uses the same auth_servers",
          "default": false
        },
        "key_idx": {
          "maximum": 4.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "When `type`==`wep`",
          "contentEncoding": "int32",
          "default": 1
        },
        "keys": {
          "type": "array",
          "items": {
            "type": [
              "string",
              "null"
            ]
          },
          "description": "When type=wep, four 10-character or 26-character hex string, null can be used. All keys, if provided, have to be in the same length",
          "default": []
        },
        "multi_psk_only": {
          "type": "boolean",
          "description": "When `type`==`psk`, whether to only use multi_psk",
          "default": false
        },
        "owe": {
          "type": "string",
          "description": "if `type`==`open`. enum: `disabled`, `enabled` (means transition mode), `required`"
        },
        "pairwise": {
          "type": "array",
          "items": {
            "oneOf": [
              {},
              {
                "title": "wlan_auth_pairwise_item",
                "enum": [
                  "wpa1-ccmp",
                  "wpa1-tkip",
                  "wpa2-ccmp",
                  "wpa2-tkip",
                  "wpa3"
                ],
                "type": "string",
                "description": "enum: `wpa1-ccmp`, `wpa1-tkip`, `wpa2-ccmp`, `wpa2-tkip`, `wpa3`",
                "examples": [
                  "wpa3"
                ]
              }
            ]
          },
          "description": "When `type`=`psk` or `type`=`eap`, one or more of `wpa1-ccmp`, `wpa1-tkip`, `wpa2-ccmp`, `wpa2-tkip`, `wpa3`"
        },
        "private_wlan": {
          "type": "boolean",
          "description": "When `multi_psk_only`==`true`, whether private wlan is enabled",
          "default": false
        },
        "psk": {
          "maxLength": 64,
          "minLength": 8,
          "type": [
            "string",
            "null"
          ],
          "description": "When `type`==`psk`, 8-64 characters, or 64 hex characters",
          "examples": [
            "foryoureyesonly"
          ]
        },
        "type": {
          "type": "string",
          "description": "enum: `eap`, `eap192`, `open`, `psk`, `psk-tkip`, `psk-wpa2-tkip`, `wep`"
        },
        "wep_as_secondary_auth": {
          "type": "boolean",
          "description": "Enable WEP as secondary auth",
          "default": false
        }
      },
      "required": [
        "type"
      ],
      "description": "Authentication wlan settings"
    },
    "auth_server_selection": {
      "type": "string",
      "description": "When ordered, AP will prefer and go back to the first server if possible. enum: `ordered`, `unordered`"
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
      "description": "List of RADIUS authentication servers, at least one is needed if `auth type`==`eap`, order matters where the first one is treated as primary"
    },
    "auth_servers_nas_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "Optional, up to 48 bytes, will be dynamically generated if not provided. used only for authentication servers",
      "examples": [
        "5c5b350e0101-nas"
      ]
    },
    "auth_servers_nas_ip": {
      "type": [
        "string",
        "null"
      ],
      "description": "Optional, NAS-IP-ADDRESS to use",
      "examples": [
        "15.3.1.5"
      ]
    },
    "auth_servers_retries": {
      "type": "integer",
      "description": "Radius auth session retries. Following fast timers are set if \"fast_dot1x_timers\" knob is enabled. \u2018retries\u2019  are set to value of auth_servers_retries. \u2018max-requests\u2019 is also set when setting auth_servers_retries and is set to default value to 3.",
      "contentEncoding": "int32",
      "default": 2,
      "examples": [
        5
      ]
    },
    "auth_servers_timeout": {
      "type": "integer",
      "description": "Radius auth session timeout. Following fast timers are set if \"fast_dot1x_timers\" knob is enabled. \u2018quite-period\u2019  and \u2018transmit-period\u2019 are set to half the value of auth_servers_timeout. \u2018supplicant-timeout\u2019 is also set when setting auth_servers_timeout and is set to default value of 10.",
      "contentEncoding": "int32",
      "default": 5
    },
    "band": {
      "type": "string",
      "description": "`band` is deprecated and kept for backward compatibility. Use bands instead",
      "deprecated": true
    },
    "band_steer": {
      "type": "boolean",
      "description": "Whether to enable band_steering, this works only when band==both",
      "default": false
    },
    "band_steer_force_band5": {
      "type": "boolean",
      "description": "Force dual_band capable client to connect to 5G",
      "default": false
    },
    "bands": {
      "type": "array",
      "items": {
        "title": "dot11_band",
        "enum": [
          "24",
          "5",
          "6"
        ],
        "type": "string",
        "description": "enum: `24`, `5`, `6`"
      },
      "description": "List of radios that the wlan should apply to."
    },
    "block_blacklist_clients": {
      "type": "boolean",
      "description": "Whether to block the clients in the blacklist (up to first 256 macs)",
      "default": false
    },
    "bonjour": {
      "type": "object",
      "properties": {
        "additional_vlan_ids": {
          "type": "object",
          "description": "List or Comma separated list of additional VLAN IDs (on the LAN side or from other WLANs) should we be forwarding bonjour queries/responses"
        },
        "enabled": {
          "type": "boolean",
          "description": "Whether to enable bonjour for this WLAN. Once enabled, limit_bcast is assumed true, allow_mdns is assumed false",
          "default": false
        },
        "services": {
          "type": "object",
          "additionalProperties": {
            "title": "wlan_bonjour_service_properties",
            "type": "object",
            "properties": {
              "disable_local": {
                "type": "boolean",
                "description": "Whether to prevent wireless clients to discover bonjour devices on the same WLAN",
                "default": false
              },
              "radius_groups": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "Optional, if the service is further restricted for certain RADIUS groups"
              },
              "scope": {
                "type": "string",
                "description": "how bonjour services should be discovered for the same WLAN. enum: `same_ap`, `same_map`, `same_site`"
              }
            }
          },
          "description": "What services are allowed. \nProperty key is the service name",
          "examples": [
            {
              "airplay": {
                "radius_groups": [
                  "teachers"
                ],
                "scope": "same_ap"
              }
            }
          ]
        }
      },
      "description": "Bonjour gateway wlan settings"
    },
    "cisco_cwa": {
      "type": "object",
      "properties": {
        "allowed_hostnames": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of hostnames without http(s):// (matched by substring)"
        },
        "allowed_subnets": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of CIDRs"
        },
        "blocked_subnets": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of blocked CIDRs"
        },
        "enabled": {
          "type": "boolean",
          "default": false
        }
      },
      "description": "Cisco CWA (central web authentication) required RADIUS with COA in order to work. See CWA: https://www.cisco.com/c/en/us/support/docs/security/identity-services-engine/115732-central-web-auth-00.html"
    },
    "client_limit_down": {
      "type": "object",
      "description": "In kbps, value from 1 to 999000"
    },
    "client_limit_down_enabled": {
      "type": "boolean",
      "description": "If downlink limiting per-client is enabled",
      "default": false
    },
    "client_limit_up": {
      "type": "object",
      "description": "In kbps, value from 1 to 999000"
    },
    "client_limit_up_enabled": {
      "type": "boolean",
      "description": "If uplink limiting per-client is enabled",
      "default": false
    },
    "coa_servers": {
      "type": "array",
      "items": {
        "title": "coa_server",
        "required": [
          "ip",
          "secret"
        ],
        "type": "object",
        "properties": {
          "disable_event_timestamp_check": {
            "type": "boolean",
            "description": "Whether to disable Event-Timestamp Check",
            "default": false
          },
          "enabled": {
            "type": "boolean",
            "default": false
          },
          "ip": {
            "type": "string",
            "examples": [
              "1.2.3.4"
            ]
          },
          "port": {
            "type": "object",
            "description": "Radius CoA Port, value from 1 to 65535, default is 3799"
          },
          "secret": {
            "type": "string",
            "examples": [
              "testing456"
            ]
          }
        },
        "description": "CoA Server"
      },
      "description": "List of COA (change of authorization) servers, optional"
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "disable_11ax": {
      "type": "boolean",
      "description": "Some old WLAN drivers may not be compatible",
      "default": false
    },
    "disable_11be": {
      "type": "boolean",
      "description": "To disable Wi-Fi 7 EHT IEs",
      "default": false
    },
    "disable_ht_vht_rates": {
      "type": "boolean",
      "description": "To disable ht or vht rates",
      "default": false
    },
    "disable_message_authenticator_check": {
      "type": "boolean",
      "description": "whether to disable Message-Authenticator Check, which is used to verify the integrity of RADIUS messages, default is false (i.e. for better security)",
      "default": false
    },
    "disable_uapsd": {
      "type": "boolean",
      "description": "Whether to disable U-APSD",
      "default": false
    },
    "disable_v1_roam_notify": {
      "type": "boolean",
      "description": "Disable sending v2 roam notification messages",
      "default": false
    },
    "disable_v2_roam_notify": {
      "type": "boolean",
      "description": "Disable sending v2 roam notification messages",
      "default": false
    },
    "disable_when_gateway_unreachable": {
      "type": "boolean",
      "description": "When any of the following is true, this WLAN will be disabled\n   * cannot get IP\n   * cannot obtain default gateway\n   * cannot reach default gateway",
      "default": false
    },
    "disable_when_mxtunnel_down": {
      "type": "boolean",
      "default": false
    },
    "disable_wmm": {
      "type": "boolean",
      "description": "Whether to disable WMM",
      "default": false
    },
    "dns_server_rewrite": {
      "type": "object",
      "description": "For radius_group-based DNS server (rewrite DNS request depending on the Group RADIUS server returns)"
    },
    "dtim": {
      "type": "integer",
      "contentEncoding": "int32",
      "default": 2
    },
    "dynamic_psk": {
      "type": "object",
      "description": "For dynamic PSK where we get per_user PSK from Radius. dynamic_psk allows PSK to be selected at runtime depending on context (wlan/site/user/...) thus following configurations are assumed (currently)\n  * PSK will come from RADIUS server\n  * AP sends client MAC as username and password (i.e. `enable_mac_auth` is assumed)\n  * AP sends BSSID:SSID as Caller-Station-ID\n  * `auth_servers` is required\n  * PSK will come from cloud WLC if source is cloud_psks\n  * default_psk will be used if cloud WLC is not available\n  * `multi_psk_only` and `psk` is ignored\n  * `pairwise` can only be wpa2-ccmp (for now, wpa3 support on the roadmap)"
    },
    "dynamic_vlan": {
      "type": "object",
      "description": "For 802.1x"
    },
    "enable_local_keycaching": {
      "type": "boolean",
      "description": "Enable AP-AP keycaching via multicast",
      "default": false
    },
    "enable_wireless_bridging": {
      "type": "boolean",
      "description": "By default, we'd inspect all DHCP packets and drop those unrelated to the wireless client itself in the case where client is a wireless bridge (DHCP packets for other MACs will need to be forwarded), wireless_bridging can be enabled",
      "default": false
    },
    "enable_wireless_bridging_dhcp_tracking": {
      "type": "boolean",
      "description": "If the client bridge is doing DHCP on behalf of other devices (L2-NAT), enable dhcp_tracking will cut down DHCP response packets to be forwarded to wireless",
      "default": false
    },
    "enabled": {
      "type": "boolean",
      "description": "If this wlan is enabled",
      "default": true
    },
    "fast_dot1x_timers": {
      "type": "boolean",
      "description": "If set to true, sets default fast-timers with values calculated from \u2018auth_servers_timeout\u2019 and \u2018auth_server_retries\u2019 .",
      "default": false
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "hide_ssid": {
      "type": "boolean",
      "description": "Whether to hide SSID in beacon",
      "default": false
    },
    "hostname_ie": {
      "type": "boolean",
      "description": "Include hostname inside IE in AP beacons / probe responses",
      "default": false
    },
    "hotspot20": {
      "type": "object",
      "properties": {
        "domain_name": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "",
          "examples": [
            [
              "mist.com"
            ]
          ]
        },
        "enabled": {
          "type": "boolean",
          "description": "Whether to enable hotspot 2.0 config"
        },
        "nai_realms": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": ""
        },
        "operators": {
          "type": "array",
          "items": {
            "title": "wlan_hotspot20_operators_item",
            "enum": [
              "ameriband",
              "att",
              "boingo",
              "charter",
              "eduroam",
              "global_reach",
              "google",
              "hughes_systique",
              "openroaming_legacy",
              "openroaming_settled",
              "openroaming_settlement_free",
              "single_digits",
              "tmobile",
              "verizon"
            ],
            "type": "string",
            "description": "enum: `ameriband`, `att`, `boingo`, `charter`, `eduroam`, `global_reach`, `google`, `hughes_systique`, `openroaming_legacy`, `openroaming_settled`, `openroaming_settlement_free`, `single_digits`, `tmobile`, `verizon`"
          },
          "description": "List of operators to support",
          "examples": [
            [
              "google",
              "att"
            ]
          ]
        },
        "rcoi": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "",
          "examples": [
            [
              "5A03BA0000"
            ]
          ]
        },
        "venue_name": {
          "type": "string",
          "description": "Venue name, default is site name",
          "examples": [
            "some_name"
          ]
        }
      },
      "description": "Hostspot 2.0 wlan settings"
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
    "inject_dhcp_option_82": {
      "title": "wlan_inject_dhcp_option_82",
      "type": "object",
      "properties": {
        "circuit_id": {
          "type": "string",
          "description": "Information to set in the `circuit_id` field of the DHCP Option 82. It is possible to use static string or the following variables (e.g. `{{SSID}}:{{AP_MAC}}`):\n  * {{AP_MAC}}\n  * {{AP_MAC_DASHED}}\n  * {{AP_MODEL}}\n  * {{AP_NAME}}\n  * {{SITE_NAME}}\n  * {{SSID}}",
          "examples": [
            "{{SSID}}:{{AP_MAC}}"
          ]
        },
        "enabled": {
          "type": "boolean",
          "description": "Whether to inject option 82 when forwarding DHCP packets",
          "default": false
        }
      }
    },
    "interface": {
      "type": "string",
      "description": "where this WLAN will be connected to. enum: `all`, `eth0`, `eth1`, `eth2`, `eth3`, `mxtunnel`, `site_mxedge`, `wxtunnel`"
    },
    "isolation": {
      "type": "boolean",
      "description": "Whether to stop clients to talk to each other",
      "default": false
    },
    "l2_isolation": {
      "type": "boolean",
      "description": "If isolation is enabled, whether to deny clients to talk to L2 on the LAN",
      "default": false
    },
    "legacy_overds": {
      "type": "boolean",
      "description": "Legacy devices requires the Over-DS (for Fast BSS Transition) bit set (while our chip doesn\u2019t support it). Warning! Enabling this will cause problem for iOS devices.",
      "default": false
    },
    "limit_bcast": {
      "type": "boolean",
      "description": "Whether to limit broadcast packets going to wireless (i.e. only allow certain bcast packets to go through)",
      "default": false
    },
    "limit_probe_response": {
      "type": "boolean",
      "description": "Limit probe response base on some heuristic rules",
      "default": false
    },
    "max_idletime": {
      "maximum": 86400.0,
      "minimum": 60.0,
      "type": "integer",
      "description": "Max idle time in seconds",
      "contentEncoding": "int32",
      "default": 1800,
      "examples": [
        1800
      ]
    },
    "max_num_clients": {
      "maximum": 128.0,
      "minimum": 0.0,
      "type": "integer",
      "description": "Maximum number of client connected to the SSID. `0` means unlimited",
      "contentEncoding": "int32",
      "default": 0
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
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "msp_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "b9d42c2e-88ee-41f8-b798-f009ce7fe909"
      ]
    },
    "mxtunnel_id": {
      "type": "string",
      "description": "(deprecated, use mxtunnel_ids instead) when `interface`==`mxtunnel`, id of the Mist Tunnel",
      "contentEncoding": "uuid",
      "deprecated": true
    },
    "mxtunnel_ids": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "When `interface`=`mxtunnel`, id of the Mist Tunnel"
    },
    "mxtunnel_name": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "When `interface`=`site_mxedge`, name of the mxtunnel that in mxtunnels under Site Setting"
    },
    "no_static_dns": {
      "type": "boolean",
      "description": "Whether to only allow client to use DNS that we\u2019ve learned from DHCP response",
      "default": false
    },
    "no_static_ip": {
      "type": "boolean",
      "description": "Whether to only allow client that we\u2019ve learned from DHCP exchange to talk",
      "default": false
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "portal": {
      "type": "object",
      "properties": {
        "allow_wlan_id_roam": {
          "type": "boolean",
          "description": "Optional if `amazon_enabled`==`true`. Whether to allow guest to connect to other Guest WLANs (with different `WLAN.ssid`) of same org without reauthentication (disable random_mac for seamless roaming)",
          "default": false
        },
        "amazon_client_id": {
          "type": [
            "string",
            "null"
          ],
          "description": "Optional if `amazon_enabled`==`true`. Amazon OAuth2 client id. This is optional. If not provided, it will use a default one."
        },
        "amazon_client_secret": {
          "type": [
            "string",
            "null"
          ],
          "description": "Optional if `amazon_enabled`==`true`. Amazon OAuth2 client secret. If amazon_client_id was provided, provide a corresponding value. Else leave blank."
        },
        "amazon_email_domains": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Optional if `amazon_enabled`==`true`. Matches authenticated user email against provided domains. If null or [], all authenticated emails will be allowed.",
          "default": []
        },
        "amazon_enabled": {
          "type": "boolean",
          "description": "Whether amazon is enabled as a login method",
          "default": false
        },
        "amazon_expire": {
          "type": [
            "integer",
            "null"
          ],
          "description": "Optional if `amazon_enabled`==`true`. Interval for which guest remains authorized using amazon auth (in minutes), if not provided, uses expire`",
          "contentEncoding": "int32"
        },
        "auth": {
          "type": "string",
          "description": "authentication scheme. enum: `amazon`, `azure`, `email`, `external`, `facebook`, `google`, `microsoft`, `multi`, `none`, `password`, `sms`, `sponsor`, `sso`"
        },
        "azure_client_id": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `azure_enabled`==`true`. Azure active directory app client id"
        },
        "azure_client_secret": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `azure_enabled`==`true`. Azure active directory app client secret"
        },
        "azure_enabled": {
          "type": "boolean",
          "description": "Whether Azure Active Directory is enabled as a login method",
          "default": false
        },
        "azure_expire": {
          "type": [
            "integer",
            "null"
          ],
          "description": "Interval for which guest remains authorized using azure auth (in minutes), if not provided, uses expire`",
          "contentEncoding": "int32"
        },
        "azure_tenant_id": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `azure_enabled`==`true`. Azure active directory tenant id."
        },
        "broadnet_password": {
          "type": "string",
          "description": "Required if `sms_provider`==`broadnet`",
          "examples": [
            "password"
          ]
        },
        "broadnet_sid": {
          "type": "string",
          "description": "Required if `sms_provider`==`broadnet`",
          "examples": [
            "MIST"
          ]
        },
        "broadnet_user_id": {
          "type": "string",
          "description": "Required if `sms_provider`==`broadnet`",
          "examples": [
            "juniper"
          ]
        },
        "bypass_when_cloud_down": {
          "type": "boolean",
          "description": "Whether to bypass the guest portal when cloud not reachable (and apply the default policies)",
          "default": false
        },
        "clickatell_api_key": {
          "type": "string",
          "description": "Required if `sms_provider`==`clickatell`"
        },
        "cross_site": {
          "type": "boolean",
          "description": "Whether to allow guest to roam between WLANs (with same `WLAN.ssid`, regardless of variables) of different sites of same org without reauthentication (disable random_mac for seamless roaming)",
          "default": false
        },
        "email_enabled": {
          "type": "boolean",
          "description": "Whether email (access code verification) is enabled as a login method",
          "default": false
        },
        "enabled": {
          "type": "boolean",
          "description": "Whether guest portal is enabled",
          "default": false
        },
        "expire": {
          "type": "integer",
          "description": "How long to remain authorized, in minutes",
          "contentEncoding": "int32",
          "default": 1440,
          "examples": [
            1440
          ]
        },
        "external_portal_url": {
          "type": "string",
          "description": "Required if `wlan_portal_auth`==`external`. External portal URL (e.g. https://host/url) where we can append our query parameters to"
        },
        "facebook_client_id": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `facebook_enabled`==`true`. Facebook OAuth2 app id. This is optional. If not provided, it will use a default one."
        },
        "facebook_client_secret": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `facebook_enabled`==`true`. Facebook OAuth2 app secret. If facebook_client_id was provided, provide a corresponding value. Else leave blank."
        },
        "facebook_email_domains": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Optional if `facebook_enabled`==`true`. Matches authenticated user email against provided domains. If null or [], all authenticated emails will be allowed.",
          "default": []
        },
        "facebook_enabled": {
          "type": "boolean",
          "description": "Whether facebook is enabled as a login method",
          "default": false
        },
        "facebook_expire": {
          "type": [
            "integer",
            "null"
          ],
          "description": "Optional if `facebook_enabled`==`true`. Interval for which guest remains authorized using facebook auth (in minutes), if not provided, uses expire`",
          "contentEncoding": "int32"
        },
        "forward": {
          "type": "boolean",
          "description": "Whether to forward the user to another URL after authorized",
          "default": false
        },
        "forward_url": {
          "type": [
            "string",
            "null"
          ],
          "description": "URL to forward the user to",
          "examples": [
            "https://abc.com/promotions"
          ]
        },
        "google_client_id": {
          "type": [
            "string",
            "null"
          ],
          "description": "Google OAuth2 app id. This is optional. If not provided, it will use a default one."
        },
        "google_client_secret": {
          "type": [
            "string",
            "null"
          ],
          "description": "Optional if `google_enabled`==`true`. Google OAuth2 app secret. If google_client_id was provided, provide a corresponding value. Else leave blank."
        },
        "google_email_domains": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Optional if `google_enabled`==`true`. Matches authenticated user email against provided domains. If null or [], all authenticated emails will be allowed.",
          "default": [],
          "examples": [
            [
              "mydomain.edu",
              "mydomain.org"
            ]
          ]
        },
        "google_enabled": {
          "type": "boolean",
          "description": "Whether Google is enabled as login method",
          "default": false
        },
        "google_expire": {
          "type": [
            "integer",
            "null"
          ],
          "description": "Optional if `google_enabled`==`true`. Interval for which guest remains authorized using Google Auth (in minutes), if not provided, uses expire`",
          "contentEncoding": "int32"
        },
        "gupshup_password": {
          "type": "string",
          "description": "Required if `sms_provider`==`gupshup`"
        },
        "gupshup_userid": {
          "type": "string",
          "description": "Required if `sms_provider`==`gupshup`"
        },
        "microsoft_client_id": {
          "type": [
            "string",
            "null"
          ],
          "description": "Optional if `microsoft_enabled`==`true`. Microsoft 365 OAuth2 client id. This is optional. If not provided, it will use a default one."
        },
        "microsoft_client_secret": {
          "type": [
            "string",
            "null"
          ],
          "description": "Optional if `microsoft_enabled`==`true`. Microsoft 365 OAuth2 client secret. If microsoft_client_id was provided, provide a corresponding value. Else leave blank."
        },
        "microsoft_email_domains": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Optional if `microsoft_enabled`==`true`. Matches authenticated user email against provided domains. If null or [], all authenticated emails will be allowed.",
          "default": []
        },
        "microsoft_enabled": {
          "type": "boolean",
          "description": "Whether microsoft 365 is enabled as a login method",
          "default": false
        },
        "microsoft_expire": {
          "type": [
            "integer",
            "null"
          ],
          "description": "Optional if `microsoft_enabled`==`true`. Interval for which guest remains authorized using microsoft auth (in minutes), if not provided, uses expire`",
          "contentEncoding": "int32"
        },
        "passphrase_enabled": {
          "type": "boolean",
          "description": "Whether password is enabled",
          "default": false
        },
        "passphrase_expire": {
          "type": [
            "integer",
            "null"
          ],
          "description": "Optional if `passphrase_enabled`==`true`. Interval for which guest remains authorized using passphrase auth (in minutes), if not provided, uses `expire`",
          "contentEncoding": "int32"
        },
        "password": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `passphrase_enabled`==`true`.",
          "examples": [
            "let me in"
          ]
        },
        "predefined_sponsors_enabled": {
          "type": "boolean",
          "description": "Whether to show list of sponsor emails mentioned in `sponsors` object as a dropdown. If both `sponsor_notify_all` and `predefined_sponsors_enabled` are false, behavior is acc to `sponsor_email_domains`",
          "default": true
        },
        "predefined_sponsors_hide_email": {
          "type": "boolean",
          "description": "Whether to hide sponsor\u2019s email from list of sponsors",
          "default": false
        },
        "privacy": {
          "type": "boolean",
          "default": false
        },
        "puzzel_password": {
          "type": "string",
          "description": "Required if `sms_provider`==`puzzel`"
        },
        "puzzel_service_id": {
          "type": "string",
          "description": "Required if `sms_provider`==`puzzel`"
        },
        "puzzel_username": {
          "type": "string",
          "description": "Required if `sms_provider`==`puzzel`"
        },
        "smsMessageFormat": {
          "type": "string",
          "description": "Optional if `sms_enabled`==`true`. SMS Message format",
          "default": "Code {{code}} expires in {{duration}} minutes."
        },
        "sms_enabled": {
          "type": "boolean",
          "description": "Whether sms is enabled as a login method",
          "default": false
        },
        "sms_expire": {
          "type": [
            "integer",
            "null"
          ],
          "description": "Optional if `sms_enabled`==`true`. Interval for which guest remains authorized using sms auth (in minutes), if not provided, uses expire`",
          "contentEncoding": "int32"
        },
        "sms_provider": {
          "type": "string",
          "description": "Optional if `sms_enabled`==`true`. enum: `broadnet`, `clickatell`, `gupshup`, `manual`, `puzzel`, `smsglobal`, `telstra`, `twilio`"
        },
        "smsglobal_api_key": {
          "type": "string",
          "description": "Required if `sms_provider`==`smsglobal`, Client API Key"
        },
        "smsglobal_api_secret": {
          "type": "string",
          "description": "Required if `sms_provider`==`smsglobal`, Client secret"
        },
        "sponsor_auto_approve": {
          "type": "boolean",
          "description": "Optional if `sponsor_enabled`==`true`. Whether to automatically approve guest and allow sponsor to revoke guest access, needs predefined_sponsors_enabled enabled and sponsor_notify_all disabled",
          "default": false
        },
        "sponsor_email_domains": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of domain allowed for sponsor email. Required if `sponsor_enabled` is `true` and `sponsors` is empty.",
          "examples": [
            [
              "reserved.net",
              "reserved.org"
            ]
          ]
        },
        "sponsor_enabled": {
          "type": "boolean",
          "description": "Whether sponsor is enabled",
          "default": false
        },
        "sponsor_expire": {
          "type": [
            "integer",
            "null"
          ],
          "description": "Optional if `sponsor_enabled`==`true`. Interval for which guest remains authorized using sponsor auth (in minutes), if not provided, uses expire`",
          "contentEncoding": "int32"
        },
        "sponsor_link_validity_duration": {
          "type": "object",
          "description": "Optional if `sponsor_enabled`==`true`. How long to remain valid sponsored guest request approve/deny link received in email, in minutes. Value is between 5 and 60."
        },
        "sponsor_notify_all": {
          "type": "boolean",
          "description": "Optional if `sponsor_enabled`==`true`. whether to notify all sponsors that are mentioned in `sponsors` object. Both `sponsor_notify_all` and `predefined_sponsors_enabled` should be true in order to notify sponsors. If true, email sent to 10 sponsors in no particular order.",
          "default": false
        },
        "sponsor_status_notify": {
          "type": "boolean",
          "description": "Optional if `sponsor_enabled`==`true`. If enabled, guest will get email about sponsor's action (approve/deny)",
          "default": false
        },
        "sponsors": {
          "type": "object",
          "description": "Object of allowed sponsors email with name. Required if `sponsor_enabled` is `true` and `sponsor_email_domains` is empty. Property key is the sponsor email, Property value is the sponsor name. List of email allowed for backward compatibility"
        },
        "sso_default_role": {
          "type": "string",
          "description": "Optional if `wlan_portal_auth`==`sso`, default role to assign if there\u2019s no match. By default, an assertion is treated as invalid when there\u2019s no role matched"
        },
        "sso_forced_role": {
          "type": "string",
          "description": "Optional if `wlan_portal_auth`==`sso`"
        },
        "sso_idp_cert": {
          "type": "string",
          "description": "Required if `wlan_portal_auth`==`sso`. IDP Cert (used to verify the signed response)"
        },
        "sso_idp_sign_algo": {
          "type": "string",
          "description": "Optional if `wlan_portal_auth`==`sso`, Signing algorithm for SAML Assertion. enum: `sha1`, `sha256`, `sha384`, `sha512`"
        },
        "sso_idp_sso_url": {
          "type": "string",
          "description": "Required if `wlan_portal_auth`==`sso`, IDP Single-Sign-On URL"
        },
        "sso_issuer": {
          "type": "string",
          "description": "Required if `wlan_portal_auth`==`sso`, IDP issuer URL"
        },
        "sso_nameid_format": {
          "type": "string",
          "description": "Optional if `wlan_portal_auth`==`sso`. enum: `email`, `unspecified`"
        },
        "telstra_client_id": {
          "type": "string",
          "description": "Required if `sms_provider`==`telstra`, Client ID provided by Telstra"
        },
        "telstra_client_secret": {
          "type": "string",
          "description": "Required if `sms_provider`==`telstra`, Client secret provided by Telstra"
        },
        "twilio_auth_token": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `sms_provider`==`twilio`, Auth token account with twilio account",
          "examples": [
            "af9dac44c344a875ab5d31cb7abcdefg"
          ]
        },
        "twilio_phone_number": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `sms_provider`==`twilio`, Twilio phone number associated with the account. See example for accepted format.",
          "examples": [
            "+18548888888"
          ]
        },
        "twilio_sid": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `sms_provider`==`twilio`, Account SID provided by Twilio",
          "examples": [
            "af9dac44c344a875ab5d31cb7abcdefg"
          ]
        }
      },
      "description": "Portal wlan settings"
    },
    "portal_allowed_hostnames": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of hostnames without http(s):// (matched by substring)",
      "default": [],
      "examples": [
        [
          "snapchat.com",
          "ibm.com"
        ]
      ]
    },
    "portal_allowed_subnets": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of CIDRs",
      "default": [],
      "examples": [
        [
          "63.5.3.0/24"
        ]
      ]
    },
    "portal_api_secret": {
      "type": [
        "string",
        "null"
      ],
      "description": "API secret (auto-generated) that can be used to sign guest authorization requests, only generated when auth is set to `external`",
      "examples": [
        "EIfPMOykI3lMlDdNPub2WcbqT6dNOtWwmYHAd6bY"
      ]
    },
    "portal_denied_hostnames": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of hostnames without http(s):// (matched by substring), this takes precedence over portal_allowed_hostnames",
      "default": [],
      "examples": [
        [
          "msg.snapchat.com"
        ]
      ]
    },
    "portal_image": {
      "type": [
        "string",
        "null"
      ],
      "description": "Url of portal background image",
      "readOnly": true,
      "examples": [
        "https://url/to/image.png"
      ]
    },
    "portal_sso_url": {
      "type": [
        "string",
        "null"
      ],
      "description": "URL used in the SSO process, auto-generated when auth is set to `sso`",
      "readOnly": true
    },
    "portal_template_url": {
      "type": [
        "string",
        "null"
      ],
      "description": "N.B portal_template will be forked out of wlan objects soon. To fetch portal_template, please query portal_template_url. To update portal_template, use Wlan Portal Template.",
      "readOnly": true
    },
    "qos": {
      "title": "wlan_qos",
      "type": "object",
      "properties": {
        "class": {
          "type": "string",
          "description": "enum: `background`, `best_effort`, `video`, `voice`"
        },
        "overwrite": {
          "type": "boolean",
          "description": "Whether to overwrite QoS",
          "default": false
        }
      }
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
    "rateset": {
      "type": "object",
      "additionalProperties": {
        "title": "wlan_datarates",
        "type": "object",
        "properties": {
          "eht": {
            "type": [
              "string",
              "null"
            ],
            "description": "If `template`==`custom`. EHT MCS bitmasks for 4 streams (16-bit for each stream, MCS0 is least significant bit)",
            "examples": [
              "3fff0fff0fff03ff"
            ]
          },
          "he": {
            "type": [
              "string",
              "null"
            ],
            "description": "If `template`==`custom`. HE MCS bitmasks for 4 streams (16-bit for each stream, MCS0 is least significant bit",
            "examples": [
              "0fff0fff0fff0fff"
            ]
          },
          "ht": {
            "type": [
              "string",
              "null"
            ],
            "description": "If `template`==`custom`. MCS bitmasks for 4 streams (16-bit for each stream, MCS0 is least significant bit), e.g. 00ff 00f0 001f limits HT rates to MCS 0-7 for 1 stream, MCS 4-7 for 2 stream (i.e. MCS 12-15), MCS 1-5 for 3 stream (i.e. MCS 16-20)",
            "examples": [
              "00ff00ff00ff"
            ]
          },
          "legacy": {
            "type": "array",
            "items": {
              "title": "wlan_datarates_legacy_item",
              "enum": [
                "1",
                "11",
                "11b",
                "12",
                "12b",
                "18",
                "18b",
                "1b",
                "2",
                "24",
                "24b",
                "2b",
                "36",
                "36b",
                "48",
                "48b",
                "5.5",
                "5.5b",
                "54",
                "54b",
                "6",
                "6b",
                "9",
                "9b"
              ],
              "type": "string",
              "description": "enum: `1`, `11`, `11b`, `12`, `12b`, `18`, `18b`, `1b`, `2`, `24`, `24b`, `2b`, `36`, `36b`, `48`, `48b`, `5.5`, `5.5b`, `54`, `54b`, `6`, `6b`, `9`, `9b`"
            },
            "description": "If `template`==`custom`. List of supported rates (IE=1) and extended supported rates (IE=50) for custom template, append \u2018b\u2019 at the end to indicate a rate being basic/mandatory. If `template`==`custom` is configured and legacy does not define at least one basic rate, it will use `no-legacy` default values",
            "examples": [
              [
                "6",
                "9",
                "12",
                "18",
                "24b",
                "36",
                "48",
                "54"
              ]
            ]
          },
          "min_rssi": {
            "type": "integer",
            "description": "Minimum RSSI for client to connect, 0 means not enforcing",
            "contentEncoding": "int32",
            "default": 0,
            "examples": [
              -70
            ]
          },
          "template": {
            "type": "object",
            "description": "Data Rates template to apply. enum: \n  * `no-legacy`: no 11b\n  * `compatible`: all, like before, default setting that Broadcom/Atheros used\n  * `legacy-only`: disable 802.11n and 802.11ac\n  * `high-density`: no 11b, no low rates\n  * `custom`: user defined"
          },
          "vht": {
            "type": [
              "string",
              "null"
            ],
            "description": "If `template`==`custom`. MCS bitmasks for 4 streams (16-bit for each stream, MCS0 is least significant bit), e.g. 03ff 01ff 00ff limits VHT rates to MCS 0-9 for 1 stream, MCS 0-8 for 2 streams, and MCS 0-7 for 3 streams.",
            "examples": [
              "03ff03ff03ff01ff"
            ]
          }
        },
        "description": "Data rates wlan settings"
      },
      "description": "Property key is the RF band. enum: `24`, `5`, `6`"
    },
    "reconnect_clients_when_roaming_mxcluster": {
      "type": "boolean",
      "description": "When different mxcluster is on different subnet, we'd want to disconnect clients (so they'll reconnect and get new IPs)",
      "default": false
    },
    "roam_mode": {
      "type": "string",
      "description": "enum: `11r`, `OKC`, `NONE`"
    },
    "schedule": {
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
      "description": "WLAN operating schedule, default is disabled"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "sle_excluded": {
      "type": "boolean",
      "description": "Whether to exclude this WLAN from SLE metrics",
      "default": false
    },
    "ssid": {
      "type": "string",
      "description": "Name of the SSID",
      "examples": [
        "corporate"
      ]
    },
    "template_id": {
      "type": [
        "string",
        "null"
      ],
      "contentEncoding": "uuid"
    },
    "thumbnail": {
      "type": [
        "string",
        "null"
      ],
      "description": "Url of portal background image thumbnail",
      "readOnly": true
    },
    "use_eapol_v1": {
      "type": "boolean",
      "description": "If `auth.type`==`eap` or `auth.type`==`psk`, should only be set for legacy client, such as pre-2004, 802.11b devices",
      "default": false
    },
    "vlan_enabled": {
      "type": "boolean",
      "description": "If vlan tagging is enabled",
      "default": false
    },
    "vlan_id": {
      "type": "object"
    },
    "vlan_ids": {
      "type": "object"
    },
    "vlan_pooling": {
      "type": "boolean",
      "description": "Requires `vlan_enabled`==`true` to be set to `true`. Vlan pooling allows AP to place client on different VLAN using a deterministic algorithm",
      "default": false
    },
    "wlan_limit_down": {
      "type": "object",
      "description": "In kbps, value from 1 to 999000"
    },
    "wlan_limit_down_enabled": {
      "type": "boolean",
      "description": "If downlink limiting for whole wlan is enabled",
      "default": false
    },
    "wlan_limit_up": {
      "type": "object",
      "description": "In kbps, value from 1 to 999000"
    },
    "wlan_limit_up_enabled": {
      "type": "boolean",
      "description": "If uplink limiting for whole wlan is enabled",
      "default": false
    },
    "wxtag_ids": {
      "type": [
        "array",
        "null"
      ],
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "List of wxtag_ids"
    },
    "wxtunnel_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "When `interface`=`wxtunnel`, id of the WXLAN Tunnel"
    },
    "wxtunnel_remote_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "When `interface`=`wxtunnel`, remote tunnel identifier"
    }
  },
  "required": [
    "ssid"
  ],
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
    "acct_immediate_update": {
      "type": "boolean",
      "description": "Enable coa-immediate-update and address-change-immediate-update on the access profile.",
      "default": false
    },
    "acct_interim_interval": {
      "maximum": 65535.0,
      "minimum": 0.0,
      "type": "integer",
      "description": "How frequently should interim accounting be reported, 60-65535. default is 0 (use one specified in Access-Accept request from RADIUS Server). Very frequent messages can affect the performance of the radius server, 600 and up is recommended when enabled",
      "contentEncoding": "int32",
      "default": 0,
      "examples": [
        0
      ]
    },
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
      "description": "List of RADIUS accounting servers, optional, order matters where the first one is treated as primary"
    },
    "airwatch": {
      "type": "object",
      "properties": {
        "api_key": {
          "type": "string",
          "description": "API Key",
          "examples": [
            "aHhlbGxvYXNkZmFzZGZhc2Rmc2RmCg==\""
          ]
        },
        "console_url": {
          "type": "string",
          "description": "Console URL",
          "examples": [
            "https://hs1.airwatchportals.com"
          ]
        },
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "password": {
          "type": "string",
          "description": "Password",
          "examples": [
            "user1"
          ]
        },
        "username": {
          "type": "string",
          "description": "Username",
          "examples": [
            "test123"
          ]
        }
      },
      "description": "Airwatch wlan settings"
    },
    "allow_ipv6_ndp": {
      "type": "boolean",
      "description": "Only applicable when `limit_bcast`==`true`, which allows or disallows ipv6 Neighbor Discovery packets to go through",
      "default": true
    },
    "allow_mdns": {
      "type": "boolean",
      "description": "Only applicable when `limit_bcast`==`true`, which allows mDNS / Bonjour packets to go through",
      "default": false
    },
    "allow_ssdp": {
      "type": "boolean",
      "description": "Only applicable when `limit_bcast`==`true`, which allows SSDP",
      "default": false
    },
    "ap_ids": {
      "type": [
        "array",
        "null"
      ],
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "List of device ids"
    },
    "app_limit": {
      "type": "object",
      "properties": {
        "apps": {
          "type": "object",
          "additionalProperties": {
            "type": "integer",
            "format": "int32"
          },
          "description": "Map from app key to bandwidth in kbps. \nProperty key is the app key, defined in Get Application List",
          "default": {},
          "examples": [
            {
              "dropbox": 300,
              "netflix": 60
            }
          ]
        },
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "wxtag_ids": {
          "type": "object",
          "additionalProperties": {
            "type": "integer",
            "format": "int32"
          },
          "description": "Map from wxtag_id of Hostname Wxlan Tags to bandwidth in kbps. Property key is the `wxtag_id`",
          "default": {},
          "examples": [
            {
              "f99862d9-2726-931f-7559-3dfdf5d070d3": 30
            }
          ]
        }
      },
      "description": "Bandwidth limiting for apps (applies to up/down)"
    },
    "app_qos": {
      "type": "object",
      "properties": {
        "apps": {
          "type": "object",
          "additionalProperties": {
            "title": "wlan_app_qos_apps_properties",
            "type": "object",
            "properties": {
              "dscp": {
                "type": "object",
                "description": "DSCP value range between 0 and 63"
              },
              "dst_subnet": {
                "type": "string",
                "description": "Subnet filter is not required but helps AP to only inspect certain traffic (thus reducing AP load)"
              },
              "src_subnet": {
                "type": "string",
                "description": "Subnet filter is not required but helps AP to only inspect certain traffic (thus reducing AP load)"
              }
            }
          },
          "examples": [
            {
              "skype-business-video": {
                "dscp": 32,
                "dst_subnet": "10.2.0.0/16",
                "src_subnet": "10.2.0.0/16"
              }
            }
          ]
        },
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "others": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "title": "wlan_app_qos_others_item",
            "type": "object",
            "properties": {
              "dscp": {
                "type": "object",
                "description": "DSCP value range between 0 and 63"
              },
              "dst_subnet": {
                "type": "string",
                "examples": [
                  "10.2.0.0/16"
                ]
              },
              "port_ranges": {
                "type": "string",
                "examples": [
                  "80,1024-6553"
                ]
              },
              "protocol": {
                "type": "string",
                "examples": [
                  "udp"
                ]
              },
              "src_subnet": {
                "type": "string",
                "examples": [
                  "10.2.0.0/16"
                ]
              }
            }
          },
          "description": ""
        }
      },
      "description": "APP qos wlan settings"
    },
    "apply_to": {
      "type": "string",
      "description": "enum: `aps`, `site`, `wxtags`"
    },
    "arp_filter": {
      "type": "boolean",
      "description": "Whether to enable smart arp filter",
      "default": false
    },
    "auth": {
      "type": "object",
      "properties": {
        "anticlog_threshold": {
          "maximum": 32.0,
          "minimum": 16.0,
          "type": "integer",
          "description": "SAE anti-clogging token threshold",
          "contentEncoding": "int32",
          "default": 16,
          "examples": [
            16
          ]
        },
        "eap_reauth": {
          "type": "boolean",
          "description": "Whether to trigger EAP reauth when the session ends",
          "default": false
        },
        "enable_mac_auth": {
          "type": "boolean",
          "description": "Whether to enable MAC Auth, uses the same auth_servers",
          "default": false
        },
        "key_idx": {
          "maximum": 4.0,
          "minimum": 1.0,
          "type": "integer",
          "description": "When `type`==`wep`",
          "contentEncoding": "int32",
          "default": 1
        },
        "keys": {
          "type": "array",
          "items": {
            "type": [
              "string",
              "null"
            ]
          },
          "description": "When type=wep, four 10-character or 26-character hex string, null can be used. All keys, if provided, have to be in the same length",
          "default": []
        },
        "multi_psk_only": {
          "type": "boolean",
          "description": "When `type`==`psk`, whether to only use multi_psk",
          "default": false
        },
        "owe": {
          "type": "string",
          "description": "if `type`==`open`. enum: `disabled`, `enabled` (means transition mode), `required`"
        },
        "pairwise": {
          "type": "array",
          "items": {
            "oneOf": [
              {},
              {
                "title": "wlan_auth_pairwise_item",
                "enum": [
                  "wpa1-ccmp",
                  "wpa1-tkip",
                  "wpa2-ccmp",
                  "wpa2-tkip",
                  "wpa3"
                ],
                "type": "string",
                "description": "enum: `wpa1-ccmp`, `wpa1-tkip`, `wpa2-ccmp`, `wpa2-tkip`, `wpa3`",
                "examples": [
                  "wpa3"
                ]
              }
            ]
          },
          "description": "When `type`=`psk` or `type`=`eap`, one or more of `wpa1-ccmp`, `wpa1-tkip`, `wpa2-ccmp`, `wpa2-tkip`, `wpa3`"
        },
        "private_wlan": {
          "type": "boolean",
          "description": "When `multi_psk_only`==`true`, whether private wlan is enabled",
          "default": false
        },
        "psk": {
          "maxLength": 64,
          "minLength": 8,
          "type": [
            "string",
            "null"
          ],
          "description": "When `type`==`psk`, 8-64 characters, or 64 hex characters",
          "examples": [
            "foryoureyesonly"
          ]
        },
        "type": {
          "type": "string",
          "description": "enum: `eap`, `eap192`, `open`, `psk`, `psk-tkip`, `psk-wpa2-tkip`, `wep`"
        },
        "wep_as_secondary_auth": {
          "type": "boolean",
          "description": "Enable WEP as secondary auth",
          "default": false
        }
      },
      "required": [
        "type"
      ],
      "description": "Authentication wlan settings"
    },
    "auth_server_selection": {
      "type": "string",
      "description": "When ordered, AP will prefer and go back to the first server if possible. enum: `ordered`, `unordered`"
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
      "description": "List of RADIUS authentication servers, at least one is needed if `auth type`==`eap`, order matters where the first one is treated as primary"
    },
    "auth_servers_nas_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "Optional, up to 48 bytes, will be dynamically generated if not provided. used only for authentication servers",
      "examples": [
        "5c5b350e0101-nas"
      ]
    },
    "auth_servers_nas_ip": {
      "type": [
        "string",
        "null"
      ],
      "description": "Optional, NAS-IP-ADDRESS to use",
      "examples": [
        "15.3.1.5"
      ]
    },
    "auth_servers_retries": {
      "type": "integer",
      "description": "Radius auth session retries. Following fast timers are set if \"fast_dot1x_timers\" knob is enabled. \u2018retries\u2019  are set to value of auth_servers_retries. \u2018max-requests\u2019 is also set when setting auth_servers_retries and is set to default value to 3.",
      "contentEncoding": "int32",
      "default": 2,
      "examples": [
        5
      ]
    },
    "auth_servers_timeout": {
      "type": "integer",
      "description": "Radius auth session timeout. Following fast timers are set if \"fast_dot1x_timers\" knob is enabled. \u2018quite-period\u2019  and \u2018transmit-period\u2019 are set to half the value of auth_servers_timeout. \u2018supplicant-timeout\u2019 is also set when setting auth_servers_timeout and is set to default value of 10.",
      "contentEncoding": "int32",
      "default": 5
    },
    "band": {
      "type": "string",
      "description": "`band` is deprecated and kept for backward compatibility. Use bands instead",
      "deprecated": true
    },
    "band_steer": {
      "type": "boolean",
      "description": "Whether to enable band_steering, this works only when band==both",
      "default": false
    },
    "band_steer_force_band5": {
      "type": "boolean",
      "description": "Force dual_band capable client to connect to 5G",
      "default": false
    },
    "bands": {
      "type": "array",
      "items": {
        "title": "dot11_band",
        "enum": [
          "24",
          "5",
          "6"
        ],
        "type": "string",
        "description": "enum: `24`, `5`, `6`"
      },
      "description": "List of radios that the wlan should apply to."
    },
    "block_blacklist_clients": {
      "type": "boolean",
      "description": "Whether to block the clients in the blacklist (up to first 256 macs)",
      "default": false
    },
    "bonjour": {
      "type": "object",
      "properties": {
        "additional_vlan_ids": {
          "type": "object",
          "description": "List or Comma separated list of additional VLAN IDs (on the LAN side or from other WLANs) should we be forwarding bonjour queries/responses"
        },
        "enabled": {
          "type": "boolean",
          "description": "Whether to enable bonjour for this WLAN. Once enabled, limit_bcast is assumed true, allow_mdns is assumed false",
          "default": false
        },
        "services": {
          "type": "object",
          "additionalProperties": {
            "title": "wlan_bonjour_service_properties",
            "type": "object",
            "properties": {
              "disable_local": {
                "type": "boolean",
                "description": "Whether to prevent wireless clients to discover bonjour devices on the same WLAN",
                "default": false
              },
              "radius_groups": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "Optional, if the service is further restricted for certain RADIUS groups"
              },
              "scope": {
                "type": "string",
                "description": "how bonjour services should be discovered for the same WLAN. enum: `same_ap`, `same_map`, `same_site`"
              }
            }
          },
          "description": "What services are allowed. \nProperty key is the service name",
          "examples": [
            {
              "airplay": {
                "radius_groups": [
                  "teachers"
                ],
                "scope": "same_ap"
              }
            }
          ]
        }
      },
      "description": "Bonjour gateway wlan settings"
    },
    "cisco_cwa": {
      "type": "object",
      "properties": {
        "allowed_hostnames": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of hostnames without http(s):// (matched by substring)"
        },
        "allowed_subnets": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of CIDRs"
        },
        "blocked_subnets": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of blocked CIDRs"
        },
        "enabled": {
          "type": "boolean",
          "default": false
        }
      },
      "description": "Cisco CWA (central web authentication) required RADIUS with COA in order to work. See CWA: https://www.cisco.com/c/en/us/support/docs/security/identity-services-engine/115732-central-web-auth-00.html"
    },
    "client_limit_down": {
      "type": "object",
      "description": "In kbps, value from 1 to 999000"
    },
    "client_limit_down_enabled": {
      "type": "boolean",
      "description": "If downlink limiting per-client is enabled",
      "default": false
    },
    "client_limit_up": {
      "type": "object",
      "description": "In kbps, value from 1 to 999000"
    },
    "client_limit_up_enabled": {
      "type": "boolean",
      "description": "If uplink limiting per-client is enabled",
      "default": false
    },
    "coa_servers": {
      "type": "array",
      "items": {
        "title": "coa_server",
        "required": [
          "ip",
          "secret"
        ],
        "type": "object",
        "properties": {
          "disable_event_timestamp_check": {
            "type": "boolean",
            "description": "Whether to disable Event-Timestamp Check",
            "default": false
          },
          "enabled": {
            "type": "boolean",
            "default": false
          },
          "ip": {
            "type": "string",
            "examples": [
              "1.2.3.4"
            ]
          },
          "port": {
            "type": "object",
            "description": "Radius CoA Port, value from 1 to 65535, default is 3799"
          },
          "secret": {
            "type": "string",
            "examples": [
              "testing456"
            ]
          }
        },
        "description": "CoA Server"
      },
      "description": "List of COA (change of authorization) servers, optional"
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "disable_11ax": {
      "type": "boolean",
      "description": "Some old WLAN drivers may not be compatible",
      "default": false
    },
    "disable_11be": {
      "type": "boolean",
      "description": "To disable Wi-Fi 7 EHT IEs",
      "default": false
    },
    "disable_ht_vht_rates": {
      "type": "boolean",
      "description": "To disable ht or vht rates",
      "default": false
    },
    "disable_message_authenticator_check": {
      "type": "boolean",
      "description": "whether to disable Message-Authenticator Check, which is used to verify the integrity of RADIUS messages, default is false (i.e. for better security)",
      "default": false
    },
    "disable_uapsd": {
      "type": "boolean",
      "description": "Whether to disable U-APSD",
      "default": false
    },
    "disable_v1_roam_notify": {
      "type": "boolean",
      "description": "Disable sending v2 roam notification messages",
      "default": false
    },
    "disable_v2_roam_notify": {
      "type": "boolean",
      "description": "Disable sending v2 roam notification messages",
      "default": false
    },
    "disable_when_gateway_unreachable": {
      "type": "boolean",
      "description": "When any of the following is true, this WLAN will be disabled\n   * cannot get IP\n   * cannot obtain default gateway\n   * cannot reach default gateway",
      "default": false
    },
    "disable_when_mxtunnel_down": {
      "type": "boolean",
      "default": false
    },
    "disable_wmm": {
      "type": "boolean",
      "description": "Whether to disable WMM",
      "default": false
    },
    "dns_server_rewrite": {
      "type": "object",
      "description": "For radius_group-based DNS server (rewrite DNS request depending on the Group RADIUS server returns)"
    },
    "dtim": {
      "type": "integer",
      "contentEncoding": "int32",
      "default": 2
    },
    "dynamic_psk": {
      "type": "object",
      "description": "For dynamic PSK where we get per_user PSK from Radius. dynamic_psk allows PSK to be selected at runtime depending on context (wlan/site/user/...) thus following configurations are assumed (currently)\n  * PSK will come from RADIUS server\n  * AP sends client MAC as username and password (i.e. `enable_mac_auth` is assumed)\n  * AP sends BSSID:SSID as Caller-Station-ID\n  * `auth_servers` is required\n  * PSK will come from cloud WLC if source is cloud_psks\n  * default_psk will be used if cloud WLC is not available\n  * `multi_psk_only` and `psk` is ignored\n  * `pairwise` can only be wpa2-ccmp (for now, wpa3 support on the roadmap)"
    },
    "dynamic_vlan": {
      "type": "object",
      "description": "For 802.1x"
    },
    "enable_local_keycaching": {
      "type": "boolean",
      "description": "Enable AP-AP keycaching via multicast",
      "default": false
    },
    "enable_wireless_bridging": {
      "type": "boolean",
      "description": "By default, we'd inspect all DHCP packets and drop those unrelated to the wireless client itself in the case where client is a wireless bridge (DHCP packets for other MACs will need to be forwarded), wireless_bridging can be enabled",
      "default": false
    },
    "enable_wireless_bridging_dhcp_tracking": {
      "type": "boolean",
      "description": "If the client bridge is doing DHCP on behalf of other devices (L2-NAT), enable dhcp_tracking will cut down DHCP response packets to be forwarded to wireless",
      "default": false
    },
    "enabled": {
      "type": "boolean",
      "description": "If this wlan is enabled",
      "default": true
    },
    "fast_dot1x_timers": {
      "type": "boolean",
      "description": "If set to true, sets default fast-timers with values calculated from \u2018auth_servers_timeout\u2019 and \u2018auth_server_retries\u2019 .",
      "default": false
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "hide_ssid": {
      "type": "boolean",
      "description": "Whether to hide SSID in beacon",
      "default": false
    },
    "hostname_ie": {
      "type": "boolean",
      "description": "Include hostname inside IE in AP beacons / probe responses",
      "default": false
    },
    "hotspot20": {
      "type": "object",
      "properties": {
        "domain_name": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "",
          "examples": [
            [
              "mist.com"
            ]
          ]
        },
        "enabled": {
          "type": "boolean",
          "description": "Whether to enable hotspot 2.0 config"
        },
        "nai_realms": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": ""
        },
        "operators": {
          "type": "array",
          "items": {
            "title": "wlan_hotspot20_operators_item",
            "enum": [
              "ameriband",
              "att",
              "boingo",
              "charter",
              "eduroam",
              "global_reach",
              "google",
              "hughes_systique",
              "openroaming_legacy",
              "openroaming_settled",
              "openroaming_settlement_free",
              "single_digits",
              "tmobile",
              "verizon"
            ],
            "type": "string",
            "description": "enum: `ameriband`, `att`, `boingo`, `charter`, `eduroam`, `global_reach`, `google`, `hughes_systique`, `openroaming_legacy`, `openroaming_settled`, `openroaming_settlement_free`, `single_digits`, `tmobile`, `verizon`"
          },
          "description": "List of operators to support",
          "examples": [
            [
              "google",
              "att"
            ]
          ]
        },
        "rcoi": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "",
          "examples": [
            [
              "5A03BA0000"
            ]
          ]
        },
        "venue_name": {
          "type": "string",
          "description": "Venue name, default is site name",
          "examples": [
            "some_name"
          ]
        }
      },
      "description": "Hostspot 2.0 wlan settings"
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
    "inject_dhcp_option_82": {
      "title": "wlan_inject_dhcp_option_82",
      "type": "object",
      "properties": {
        "circuit_id": {
          "type": "string",
          "description": "Information to set in the `circuit_id` field of the DHCP Option 82. It is possible to use static string or the following variables (e.g. `{{SSID}}:{{AP_MAC}}`):\n  * {{AP_MAC}}\n  * {{AP_MAC_DASHED}}\n  * {{AP_MODEL}}\n  * {{AP_NAME}}\n  * {{SITE_NAME}}\n  * {{SSID}}",
          "examples": [
            "{{SSID}}:{{AP_MAC}}"
          ]
        },
        "enabled": {
          "type": "boolean",
          "description": "Whether to inject option 82 when forwarding DHCP packets",
          "default": false
        }
      }
    },
    "interface": {
      "type": "string",
      "description": "where this WLAN will be connected to. enum: `all`, `eth0`, `eth1`, `eth2`, `eth3`, `mxtunnel`, `site_mxedge`, `wxtunnel`"
    },
    "isolation": {
      "type": "boolean",
      "description": "Whether to stop clients to talk to each other",
      "default": false
    },
    "l2_isolation": {
      "type": "boolean",
      "description": "If isolation is enabled, whether to deny clients to talk to L2 on the LAN",
      "default": false
    },
    "legacy_overds": {
      "type": "boolean",
      "description": "Legacy devices requires the Over-DS (for Fast BSS Transition) bit set (while our chip doesn\u2019t support it). Warning! Enabling this will cause problem for iOS devices.",
      "default": false
    },
    "limit_bcast": {
      "type": "boolean",
      "description": "Whether to limit broadcast packets going to wireless (i.e. only allow certain bcast packets to go through)",
      "default": false
    },
    "limit_probe_response": {
      "type": "boolean",
      "description": "Limit probe response base on some heuristic rules",
      "default": false
    },
    "max_idletime": {
      "maximum": 86400.0,
      "minimum": 60.0,
      "type": "integer",
      "description": "Max idle time in seconds",
      "contentEncoding": "int32",
      "default": 1800,
      "examples": [
        1800
      ]
    },
    "max_num_clients": {
      "maximum": 128.0,
      "minimum": 0.0,
      "type": "integer",
      "description": "Maximum number of client connected to the SSID. `0` means unlimited",
      "contentEncoding": "int32",
      "default": 0
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
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "msp_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "b9d42c2e-88ee-41f8-b798-f009ce7fe909"
      ]
    },
    "mxtunnel_id": {
      "type": "string",
      "description": "(deprecated, use mxtunnel_ids instead) when `interface`==`mxtunnel`, id of the Mist Tunnel",
      "contentEncoding": "uuid",
      "deprecated": true
    },
    "mxtunnel_ids": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "When `interface`=`mxtunnel`, id of the Mist Tunnel"
    },
    "mxtunnel_name": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "When `interface`=`site_mxedge`, name of the mxtunnel that in mxtunnels under Site Setting"
    },
    "no_static_dns": {
      "type": "boolean",
      "description": "Whether to only allow client to use DNS that we\u2019ve learned from DHCP response",
      "default": false
    },
    "no_static_ip": {
      "type": "boolean",
      "description": "Whether to only allow client that we\u2019ve learned from DHCP exchange to talk",
      "default": false
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "portal": {
      "type": "object",
      "properties": {
        "allow_wlan_id_roam": {
          "type": "boolean",
          "description": "Optional if `amazon_enabled`==`true`. Whether to allow guest to connect to other Guest WLANs (with different `WLAN.ssid`) of same org without reauthentication (disable random_mac for seamless roaming)",
          "default": false
        },
        "amazon_client_id": {
          "type": [
            "string",
            "null"
          ],
          "description": "Optional if `amazon_enabled`==`true`. Amazon OAuth2 client id. This is optional. If not provided, it will use a default one."
        },
        "amazon_client_secret": {
          "type": [
            "string",
            "null"
          ],
          "description": "Optional if `amazon_enabled`==`true`. Amazon OAuth2 client secret. If amazon_client_id was provided, provide a corresponding value. Else leave blank."
        },
        "amazon_email_domains": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Optional if `amazon_enabled`==`true`. Matches authenticated user email against provided domains. If null or [], all authenticated emails will be allowed.",
          "default": []
        },
        "amazon_enabled": {
          "type": "boolean",
          "description": "Whether amazon is enabled as a login method",
          "default": false
        },
        "amazon_expire": {
          "type": [
            "integer",
            "null"
          ],
          "description": "Optional if `amazon_enabled`==`true`. Interval for which guest remains authorized using amazon auth (in minutes), if not provided, uses expire`",
          "contentEncoding": "int32"
        },
        "auth": {
          "type": "string",
          "description": "authentication scheme. enum: `amazon`, `azure`, `email`, `external`, `facebook`, `google`, `microsoft`, `multi`, `none`, `password`, `sms`, `sponsor`, `sso`"
        },
        "azure_client_id": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `azure_enabled`==`true`. Azure active directory app client id"
        },
        "azure_client_secret": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `azure_enabled`==`true`. Azure active directory app client secret"
        },
        "azure_enabled": {
          "type": "boolean",
          "description": "Whether Azure Active Directory is enabled as a login method",
          "default": false
        },
        "azure_expire": {
          "type": [
            "integer",
            "null"
          ],
          "description": "Interval for which guest remains authorized using azure auth (in minutes), if not provided, uses expire`",
          "contentEncoding": "int32"
        },
        "azure_tenant_id": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `azure_enabled`==`true`. Azure active directory tenant id."
        },
        "broadnet_password": {
          "type": "string",
          "description": "Required if `sms_provider`==`broadnet`",
          "examples": [
            "password"
          ]
        },
        "broadnet_sid": {
          "type": "string",
          "description": "Required if `sms_provider`==`broadnet`",
          "examples": [
            "MIST"
          ]
        },
        "broadnet_user_id": {
          "type": "string",
          "description": "Required if `sms_provider`==`broadnet`",
          "examples": [
            "juniper"
          ]
        },
        "bypass_when_cloud_down": {
          "type": "boolean",
          "description": "Whether to bypass the guest portal when cloud not reachable (and apply the default policies)",
          "default": false
        },
        "clickatell_api_key": {
          "type": "string",
          "description": "Required if `sms_provider`==`clickatell`"
        },
        "cross_site": {
          "type": "boolean",
          "description": "Whether to allow guest to roam between WLANs (with same `WLAN.ssid`, regardless of variables) of different sites of same org without reauthentication (disable random_mac for seamless roaming)",
          "default": false
        },
        "email_enabled": {
          "type": "boolean",
          "description": "Whether email (access code verification) is enabled as a login method",
          "default": false
        },
        "enabled": {
          "type": "boolean",
          "description": "Whether guest portal is enabled",
          "default": false
        },
        "expire": {
          "type": "integer",
          "description": "How long to remain authorized, in minutes",
          "contentEncoding": "int32",
          "default": 1440,
          "examples": [
            1440
          ]
        },
        "external_portal_url": {
          "type": "string",
          "description": "Required if `wlan_portal_auth`==`external`. External portal URL (e.g. https://host/url) where we can append our query parameters to"
        },
        "facebook_client_id": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `facebook_enabled`==`true`. Facebook OAuth2 app id. This is optional. If not provided, it will use a default one."
        },
        "facebook_client_secret": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `facebook_enabled`==`true`. Facebook OAuth2 app secret. If facebook_client_id was provided, provide a corresponding value. Else leave blank."
        },
        "facebook_email_domains": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Optional if `facebook_enabled`==`true`. Matches authenticated user email against provided domains. If null or [], all authenticated emails will be allowed.",
          "default": []
        },
        "facebook_enabled": {
          "type": "boolean",
          "description": "Whether facebook is enabled as a login method",
          "default": false
        },
        "facebook_expire": {
          "type": [
            "integer",
            "null"
          ],
          "description": "Optional if `facebook_enabled`==`true`. Interval for which guest remains authorized using facebook auth (in minutes), if not provided, uses expire`",
          "contentEncoding": "int32"
        },
        "forward": {
          "type": "boolean",
          "description": "Whether to forward the user to another URL after authorized",
          "default": false
        },
        "forward_url": {
          "type": [
            "string",
            "null"
          ],
          "description": "URL to forward the user to",
          "examples": [
            "https://abc.com/promotions"
          ]
        },
        "google_client_id": {
          "type": [
            "string",
            "null"
          ],
          "description": "Google OAuth2 app id. This is optional. If not provided, it will use a default one."
        },
        "google_client_secret": {
          "type": [
            "string",
            "null"
          ],
          "description": "Optional if `google_enabled`==`true`. Google OAuth2 app secret. If google_client_id was provided, provide a corresponding value. Else leave blank."
        },
        "google_email_domains": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Optional if `google_enabled`==`true`. Matches authenticated user email against provided domains. If null or [], all authenticated emails will be allowed.",
          "default": [],
          "examples": [
            [
              "mydomain.edu",
              "mydomain.org"
            ]
          ]
        },
        "google_enabled": {
          "type": "boolean",
          "description": "Whether Google is enabled as login method",
          "default": false
        },
        "google_expire": {
          "type": [
            "integer",
            "null"
          ],
          "description": "Optional if `google_enabled`==`true`. Interval for which guest remains authorized using Google Auth (in minutes), if not provided, uses expire`",
          "contentEncoding": "int32"
        },
        "gupshup_password": {
          "type": "string",
          "description": "Required if `sms_provider`==`gupshup`"
        },
        "gupshup_userid": {
          "type": "string",
          "description": "Required if `sms_provider`==`gupshup`"
        },
        "microsoft_client_id": {
          "type": [
            "string",
            "null"
          ],
          "description": "Optional if `microsoft_enabled`==`true`. Microsoft 365 OAuth2 client id. This is optional. If not provided, it will use a default one."
        },
        "microsoft_client_secret": {
          "type": [
            "string",
            "null"
          ],
          "description": "Optional if `microsoft_enabled`==`true`. Microsoft 365 OAuth2 client secret. If microsoft_client_id was provided, provide a corresponding value. Else leave blank."
        },
        "microsoft_email_domains": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Optional if `microsoft_enabled`==`true`. Matches authenticated user email against provided domains. If null or [], all authenticated emails will be allowed.",
          "default": []
        },
        "microsoft_enabled": {
          "type": "boolean",
          "description": "Whether microsoft 365 is enabled as a login method",
          "default": false
        },
        "microsoft_expire": {
          "type": [
            "integer",
            "null"
          ],
          "description": "Optional if `microsoft_enabled`==`true`. Interval for which guest remains authorized using microsoft auth (in minutes), if not provided, uses expire`",
          "contentEncoding": "int32"
        },
        "passphrase_enabled": {
          "type": "boolean",
          "description": "Whether password is enabled",
          "default": false
        },
        "passphrase_expire": {
          "type": [
            "integer",
            "null"
          ],
          "description": "Optional if `passphrase_enabled`==`true`. Interval for which guest remains authorized using passphrase auth (in minutes), if not provided, uses `expire`",
          "contentEncoding": "int32"
        },
        "password": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `passphrase_enabled`==`true`.",
          "examples": [
            "let me in"
          ]
        },
        "predefined_sponsors_enabled": {
          "type": "boolean",
          "description": "Whether to show list of sponsor emails mentioned in `sponsors` object as a dropdown. If both `sponsor_notify_all` and `predefined_sponsors_enabled` are false, behavior is acc to `sponsor_email_domains`",
          "default": true
        },
        "predefined_sponsors_hide_email": {
          "type": "boolean",
          "description": "Whether to hide sponsor\u2019s email from list of sponsors",
          "default": false
        },
        "privacy": {
          "type": "boolean",
          "default": false
        },
        "puzzel_password": {
          "type": "string",
          "description": "Required if `sms_provider`==`puzzel`"
        },
        "puzzel_service_id": {
          "type": "string",
          "description": "Required if `sms_provider`==`puzzel`"
        },
        "puzzel_username": {
          "type": "string",
          "description": "Required if `sms_provider`==`puzzel`"
        },
        "smsMessageFormat": {
          "type": "string",
          "description": "Optional if `sms_enabled`==`true`. SMS Message format",
          "default": "Code {{code}} expires in {{duration}} minutes."
        },
        "sms_enabled": {
          "type": "boolean",
          "description": "Whether sms is enabled as a login method",
          "default": false
        },
        "sms_expire": {
          "type": [
            "integer",
            "null"
          ],
          "description": "Optional if `sms_enabled`==`true`. Interval for which guest remains authorized using sms auth (in minutes), if not provided, uses expire`",
          "contentEncoding": "int32"
        },
        "sms_provider": {
          "type": "string",
          "description": "Optional if `sms_enabled`==`true`. enum: `broadnet`, `clickatell`, `gupshup`, `manual`, `puzzel`, `smsglobal`, `telstra`, `twilio`"
        },
        "smsglobal_api_key": {
          "type": "string",
          "description": "Required if `sms_provider`==`smsglobal`, Client API Key"
        },
        "smsglobal_api_secret": {
          "type": "string",
          "description": "Required if `sms_provider`==`smsglobal`, Client secret"
        },
        "sponsor_auto_approve": {
          "type": "boolean",
          "description": "Optional if `sponsor_enabled`==`true`. Whether to automatically approve guest and allow sponsor to revoke guest access, needs predefined_sponsors_enabled enabled and sponsor_notify_all disabled",
          "default": false
        },
        "sponsor_email_domains": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of domain allowed for sponsor email. Required if `sponsor_enabled` is `true` and `sponsors` is empty.",
          "examples": [
            [
              "reserved.net",
              "reserved.org"
            ]
          ]
        },
        "sponsor_enabled": {
          "type": "boolean",
          "description": "Whether sponsor is enabled",
          "default": false
        },
        "sponsor_expire": {
          "type": [
            "integer",
            "null"
          ],
          "description": "Optional if `sponsor_enabled`==`true`. Interval for which guest remains authorized using sponsor auth (in minutes), if not provided, uses expire`",
          "contentEncoding": "int32"
        },
        "sponsor_link_validity_duration": {
          "type": "object",
          "description": "Optional if `sponsor_enabled`==`true`. How long to remain valid sponsored guest request approve/deny link received in email, in minutes. Value is between 5 and 60."
        },
        "sponsor_notify_all": {
          "type": "boolean",
          "description": "Optional if `sponsor_enabled`==`true`. whether to notify all sponsors that are mentioned in `sponsors` object. Both `sponsor_notify_all` and `predefined_sponsors_enabled` should be true in order to notify sponsors. If true, email sent to 10 sponsors in no particular order.",
          "default": false
        },
        "sponsor_status_notify": {
          "type": "boolean",
          "description": "Optional if `sponsor_enabled`==`true`. If enabled, guest will get email about sponsor's action (approve/deny)",
          "default": false
        },
        "sponsors": {
          "type": "object",
          "description": "Object of allowed sponsors email with name. Required if `sponsor_enabled` is `true` and `sponsor_email_domains` is empty. Property key is the sponsor email, Property value is the sponsor name. List of email allowed for backward compatibility"
        },
        "sso_default_role": {
          "type": "string",
          "description": "Optional if `wlan_portal_auth`==`sso`, default role to assign if there\u2019s no match. By default, an assertion is treated as invalid when there\u2019s no role matched"
        },
        "sso_forced_role": {
          "type": "string",
          "description": "Optional if `wlan_portal_auth`==`sso`"
        },
        "sso_idp_cert": {
          "type": "string",
          "description": "Required if `wlan_portal_auth`==`sso`. IDP Cert (used to verify the signed response)"
        },
        "sso_idp_sign_algo": {
          "type": "string",
          "description": "Optional if `wlan_portal_auth`==`sso`, Signing algorithm for SAML Assertion. enum: `sha1`, `sha256`, `sha384`, `sha512`"
        },
        "sso_idp_sso_url": {
          "type": "string",
          "description": "Required if `wlan_portal_auth`==`sso`, IDP Single-Sign-On URL"
        },
        "sso_issuer": {
          "type": "string",
          "description": "Required if `wlan_portal_auth`==`sso`, IDP issuer URL"
        },
        "sso_nameid_format": {
          "type": "string",
          "description": "Optional if `wlan_portal_auth`==`sso`. enum: `email`, `unspecified`"
        },
        "telstra_client_id": {
          "type": "string",
          "description": "Required if `sms_provider`==`telstra`, Client ID provided by Telstra"
        },
        "telstra_client_secret": {
          "type": "string",
          "description": "Required if `sms_provider`==`telstra`, Client secret provided by Telstra"
        },
        "twilio_auth_token": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `sms_provider`==`twilio`, Auth token account with twilio account",
          "examples": [
            "af9dac44c344a875ab5d31cb7abcdefg"
          ]
        },
        "twilio_phone_number": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `sms_provider`==`twilio`, Twilio phone number associated with the account. See example for accepted format.",
          "examples": [
            "+18548888888"
          ]
        },
        "twilio_sid": {
          "type": [
            "string",
            "null"
          ],
          "description": "Required if `sms_provider`==`twilio`, Account SID provided by Twilio",
          "examples": [
            "af9dac44c344a875ab5d31cb7abcdefg"
          ]
        }
      },
      "description": "Portal wlan settings"
    },
    "portal_allowed_hostnames": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of hostnames without http(s):// (matched by substring)",
      "default": [],
      "examples": [
        [
          "snapchat.com",
          "ibm.com"
        ]
      ]
    },
    "portal_allowed_subnets": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of CIDRs",
      "default": [],
      "examples": [
        [
          "63.5.3.0/24"
        ]
      ]
    },
    "portal_api_secret": {
      "type": [
        "string",
        "null"
      ],
      "description": "API secret (auto-generated) that can be used to sign guest authorization requests, only generated when auth is set to `external`",
      "examples": [
        "EIfPMOykI3lMlDdNPub2WcbqT6dNOtWwmYHAd6bY"
      ]
    },
    "portal_denied_hostnames": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of hostnames without http(s):// (matched by substring), this takes precedence over portal_allowed_hostnames",
      "default": [],
      "examples": [
        [
          "msg.snapchat.com"
        ]
      ]
    },
    "portal_image": {
      "type": [
        "string",
        "null"
      ],
      "description": "Url of portal background image",
      "readOnly": true,
      "examples": [
        "https://url/to/image.png"
      ]
    },
    "portal_sso_url": {
      "type": [
        "string",
        "null"
      ],
      "description": "URL used in the SSO process, auto-generated when auth is set to `sso`",
      "readOnly": true
    },
    "portal_template_url": {
      "type": [
        "string",
        "null"
      ],
      "description": "N.B portal_template will be forked out of wlan objects soon. To fetch portal_template, please query portal_template_url. To update portal_template, use Wlan Portal Template.",
      "readOnly": true
    },
    "qos": {
      "title": "wlan_qos",
      "type": "object",
      "properties": {
        "class": {
          "type": "string",
          "description": "enum: `background`, `best_effort`, `video`, `voice`"
        },
        "overwrite": {
          "type": "boolean",
          "description": "Whether to overwrite QoS",
          "default": false
        }
      }
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
    "rateset": {
      "type": "object",
      "additionalProperties": {
        "title": "wlan_datarates",
        "type": "object",
        "properties": {
          "eht": {
            "type": [
              "string",
              "null"
            ],
            "description": "If `template`==`custom`. EHT MCS bitmasks for 4 streams (16-bit for each stream, MCS0 is least significant bit)",
            "examples": [
              "3fff0fff0fff03ff"
            ]
          },
          "he": {
            "type": [
              "string",
              "null"
            ],
            "description": "If `template`==`custom`. HE MCS bitmasks for 4 streams (16-bit for each stream, MCS0 is least significant bit",
            "examples": [
              "0fff0fff0fff0fff"
            ]
          },
          "ht": {
            "type": [
              "string",
              "null"
            ],
            "description": "If `template`==`custom`. MCS bitmasks for 4 streams (16-bit for each stream, MCS0 is least significant bit), e.g. 00ff 00f0 001f limits HT rates to MCS 0-7 for 1 stream, MCS 4-7 for 2 stream (i.e. MCS 12-15), MCS 1-5 for 3 stream (i.e. MCS 16-20)",
            "examples": [
              "00ff00ff00ff"
            ]
          },
          "legacy": {
            "type": "array",
            "items": {
              "title": "wlan_datarates_legacy_item",
              "enum": [
                "1",
                "11",
                "11b",
                "12",
                "12b",
                "18",
                "18b",
                "1b",
                "2",
                "24",
                "24b",
                "2b",
                "36",
                "36b",
                "48",
                "48b",
                "5.5",
                "5.5b",
                "54",
                "54b",
                "6",
                "6b",
                "9",
                "9b"
              ],
              "type": "string",
              "description": "enum: `1`, `11`, `11b`, `12`, `12b`, `18`, `18b`, `1b`, `2`, `24`, `24b`, `2b`, `36`, `36b`, `48`, `48b`, `5.5`, `5.5b`, `54`, `54b`, `6`, `6b`, `9`, `9b`"
            },
            "description": "If `template`==`custom`. List of supported rates (IE=1) and extended supported rates (IE=50) for custom template, append \u2018b\u2019 at the end to indicate a rate being basic/mandatory. If `template`==`custom` is configured and legacy does not define at least one basic rate, it will use `no-legacy` default values",
            "examples": [
              [
                "6",
                "9",
                "12",
                "18",
                "24b",
                "36",
                "48",
                "54"
              ]
            ]
          },
          "min_rssi": {
            "type": "integer",
            "description": "Minimum RSSI for client to connect, 0 means not enforcing",
            "contentEncoding": "int32",
            "default": 0,
            "examples": [
              -70
            ]
          },
          "template": {
            "type": "object",
            "description": "Data Rates template to apply. enum: \n  * `no-legacy`: no 11b\n  * `compatible`: all, like before, default setting that Broadcom/Atheros used\n  * `legacy-only`: disable 802.11n and 802.11ac\n  * `high-density`: no 11b, no low rates\n  * `custom`: user defined"
          },
          "vht": {
            "type": [
              "string",
              "null"
            ],
            "description": "If `template`==`custom`. MCS bitmasks for 4 streams (16-bit for each stream, MCS0 is least significant bit), e.g. 03ff 01ff 00ff limits VHT rates to MCS 0-9 for 1 stream, MCS 0-8 for 2 streams, and MCS 0-7 for 3 streams.",
            "examples": [
              "03ff03ff03ff01ff"
            ]
          }
        },
        "description": "Data rates wlan settings"
      },
      "description": "Property key is the RF band. enum: `24`, `5`, `6`"
    },
    "reconnect_clients_when_roaming_mxcluster": {
      "type": "boolean",
      "description": "When different mxcluster is on different subnet, we'd want to disconnect clients (so they'll reconnect and get new IPs)",
      "default": false
    },
    "roam_mode": {
      "type": "string",
      "description": "enum: `11r`, `OKC`, `NONE`"
    },
    "schedule": {
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
      "description": "WLAN operating schedule, default is disabled"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "sle_excluded": {
      "type": "boolean",
      "description": "Whether to exclude this WLAN from SLE metrics",
      "default": false
    },
    "ssid": {
      "type": "string",
      "description": "Name of the SSID",
      "examples": [
        "corporate"
      ]
    },
    "template_id": {
      "type": [
        "string",
        "null"
      ],
      "contentEncoding": "uuid"
    },
    "thumbnail": {
      "type": [
        "string",
        "null"
      ],
      "description": "Url of portal background image thumbnail",
      "readOnly": true
    },
    "use_eapol_v1": {
      "type": "boolean",
      "description": "If `auth.type`==`eap` or `auth.type`==`psk`, should only be set for legacy client, such as pre-2004, 802.11b devices",
      "default": false
    },
    "vlan_enabled": {
      "type": "boolean",
      "description": "If vlan tagging is enabled",
      "default": false
    },
    "vlan_id": {
      "type": "object"
    },
    "vlan_ids": {
      "type": "object"
    },
    "vlan_pooling": {
      "type": "boolean",
      "description": "Requires `vlan_enabled`==`true` to be set to `true`. Vlan pooling allows AP to place client on different VLAN using a deterministic algorithm",
      "default": false
    },
    "wlan_limit_down": {
      "type": "object",
      "description": "In kbps, value from 1 to 999000"
    },
    "wlan_limit_down_enabled": {
      "type": "boolean",
      "description": "If downlink limiting for whole wlan is enabled",
      "default": false
    },
    "wlan_limit_up": {
      "type": "object",
      "description": "In kbps, value from 1 to 999000"
    },
    "wlan_limit_up_enabled": {
      "type": "boolean",
      "description": "If uplink limiting for whole wlan is enabled",
      "default": false
    },
    "wxtag_ids": {
      "type": [
        "array",
        "null"
      ],
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "List of wxtag_ids"
    },
    "wxtunnel_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "When `interface`=`wxtunnel`, id of the WXLAN Tunnel"
    },
    "wxtunnel_remote_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "When `interface`=`wxtunnel`, remote tunnel identifier"
    }
  },
  "required": [
    "ssid"
  ],
  "description": "**Note**: portal_template will be forked out of wlan objects soon. To fetch portal_template, please query portal_template_url. To update portal_template, use Wlan Portal Template."
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

`mistapi.api.v1.sites.wlans.updateSiteWlan()`

## Usage Context

Updates a WLAN's configuration (SSID name, security, VLAN, band steering, etc.).

## Gotchas

- Changes trigger a config push and may briefly disconnect clients.

## Related Endpoints

- [GET_sites_site_id_wlans_wlan_id.md](GET_sites_site_id_wlans_wlan_id.md) — WLAN details
- [GET_sites_site_id_wlans.md](GET_sites_site_id_wlans.md) — List WLANs

## MistHelper Notes

Used by MistHelper via `updateSiteWlan` in Menus 49, 102 (WLAN management).
