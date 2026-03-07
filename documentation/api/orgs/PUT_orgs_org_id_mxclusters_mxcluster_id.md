# updateOrgMxEdgeCluster

> updateOrgMxEdgeCluster

## HTTP

`PUT /api/v1/orgs/{org_id}/mxclusters/{mxcluster_id}`

## Description

Update Org MxEdge Cluster

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| mxcluster_id | string | Yes |  |

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
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
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
    },
    "radsec_tls": {
      "title": "mxcluster_radsec_tls",
      "type": "object",
      "properties": {
        "keypair": {
          "type": "string"
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
    "tunterm_ap_subnets": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of subnets where we allow AP to establish Mist Tunnels from"
    },
    "tunterm_dhcpd_config": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "servers": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": ""
        },
        "type": {
          "type": "string",
          "description": "enum: `relay`"
        }
      },
      "description": "DHCP server/relay configuration of Mist Tunneled VLANs. Property key is the VLAN ID"
    },
    "tunterm_extra_routes": {
      "type": "object",
      "additionalProperties": {
        "title": "mxcluster_tunterm_extra_route",
        "type": "object",
        "properties": {
          "via": {
            "type": "string"
          }
        }
      },
      "description": "Extra routes for Mist Tunneled VLANs. Property key is a CIDR"
    },
    "tunterm_hosts": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Hostnames or IPs where a Mist Tunnel will use as the Peer (i.e. they are reachable from AP)"
    },
    "tunterm_hosts_order": {
      "type": "array",
      "items": {
        "type": "integer",
        "contentEncoding": "int32"
      },
      "description": "List of index of tunterm_hosts"
    },
    "tunterm_hosts_selection": {
      "type": "string",
      "description": "Ordering of tunterm_hosts for mxedge within the same mxcluster. enum:\n  * `shuffle`: the ordering of tunterm_hosts is randomized by the device''s MAC\n  * `shuffle-by-site`: shuffle by site_id+tunnel_id (so when client connects to a specific Tunnel, it will go to the same (order of) mxedge, and we load-balancing between tunnels)\n  * `ordered`: order decided by tunterm_hosts_order"
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
    "tunterm_monitoring_disabled": {
      "type": "boolean"
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
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
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
    },
    "radsec_tls": {
      "title": "mxcluster_radsec_tls",
      "type": "object",
      "properties": {
        "keypair": {
          "type": "string"
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
    "tunterm_ap_subnets": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of subnets where we allow AP to establish Mist Tunnels from"
    },
    "tunterm_dhcpd_config": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "servers": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": ""
        },
        "type": {
          "type": "string",
          "description": "enum: `relay`"
        }
      },
      "description": "DHCP server/relay configuration of Mist Tunneled VLANs. Property key is the VLAN ID"
    },
    "tunterm_extra_routes": {
      "type": "object",
      "additionalProperties": {
        "title": "mxcluster_tunterm_extra_route",
        "type": "object",
        "properties": {
          "via": {
            "type": "string"
          }
        }
      },
      "description": "Extra routes for Mist Tunneled VLANs. Property key is a CIDR"
    },
    "tunterm_hosts": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Hostnames or IPs where a Mist Tunnel will use as the Peer (i.e. they are reachable from AP)"
    },
    "tunterm_hosts_order": {
      "type": "array",
      "items": {
        "type": "integer",
        "contentEncoding": "int32"
      },
      "description": "List of index of tunterm_hosts"
    },
    "tunterm_hosts_selection": {
      "type": "string",
      "description": "Ordering of tunterm_hosts for mxedge within the same mxcluster. enum:\n  * `shuffle`: the ordering of tunterm_hosts is randomized by the device''s MAC\n  * `shuffle-by-site`: shuffle by site_id+tunnel_id (so when client connects to a specific Tunnel, it will go to the same (order of) mxedge, and we load-balancing between tunnels)\n  * `ordered`: order decided by tunterm_hosts_order"
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
    "tunterm_monitoring_disabled": {
      "type": "boolean"
    }
  },
  "description": "MxCluster"
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

`mistapi.api.v1.orgs.mxclusters.updateOrgMxEdgeCluster()`

## Usage Context

Updates an existing Mist Edge cluster configuration.

## Gotchas

- Cluster changes may cause brief tunnel reconnections.

## Related Endpoints

- [GET_orgs_org_id_mxclusters_mxcluster_id.md](GET_orgs_org_id_mxclusters_mxcluster_id.md) — Get cluster
- [POST_orgs_org_id_mxclusters.md](POST_orgs_org_id_mxclusters.md) — Create cluster

## MistHelper Notes

Not currently used by MistHelper directly.
