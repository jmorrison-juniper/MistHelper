# createSiteWxTunnel

> createSiteWxTunnel

## HTTP

`POST /api/v1/sites/{site_id}/wxtunnels`

## Description

Create Site WxLan Tunnel

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

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
    "dmvpn": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "Whether DMVPN is enabled",
          "default": false
        },
        "holding_time": {
          "type": "integer",
          "description": "Optional; the holding time for NHRP \u2018registration requests\u2019  and \u2018resolution replies\u2019 sent from the Mist AP (in seconds); default 600",
          "contentEncoding": "int32"
        },
        "host_routes": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Optional; list of IPv4 DMVPN peer host ip-addresses to which traffic is forwarded"
        }
      },
      "description": "Dynamic Multipoint VPN configurations"
    },
    "for_mgmt": {
      "type": "boolean",
      "description": "Determined during creation time and cannot be toggled. A management tunnel cannot be used by wxlan rule or by wlan",
      "default": false
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "hello_interval": {
      "maximum": 300.0,
      "minimum": 1.0,
      "type": "integer",
      "description": "In seconds, used as heartbeat to detect if a tunnel is alive. AP will try another peer after missing N hellos specified by hello_retries.",
      "contentEncoding": "int32",
      "default": 60
    },
    "hello_retries": {
      "maximum": 30.0,
      "minimum": 2.0,
      "type": "integer",
      "contentEncoding": "int32",
      "default": 7
    },
    "hostname": {
      "type": "string",
      "description": "Optional, overwrite the hostname in SCCRQ control message, default is  or null, %H and %M can be used, which will be replace with corresponding values:\n  * %H: name of the ap if provided (and will be stripped so it can be used for hostname) and fallbacks to MAC\n  * %M: MAC (e.g. 5c5b350e0060)"
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
    "ipsec": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "Whether ipsec is enabled, requires DMVPN be enabled",
          "default": false
        },
        "psk": {
          "type": "string",
          "description": "IPSec pre-shared key"
        }
      },
      "required": [
        "psk"
      ],
      "description": "IPSec-related configurations; requires DMVPN be enabled"
    },
    "is_static": {
      "type": "boolean",
      "description": "Whether it\u2019s static/unmanaged (i.e. no control session). As the session configurations are not compatible, cannot be toggled.",
      "default": false
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
      "description": "0 to enable PMTU, 552-1500 to start PMTU with a lower MTU",
      "contentEncoding": "int32",
      "default": 0
    },
    "name": {
      "type": "string",
      "description": "The name of the tunnel"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "peers": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of remote peers\u2019 IP or hostname"
    },
    "router_id": {
      "type": "string",
      "description": "Optional, overwrite the router-id in SCCRQ control message, default is \"\" or null, can also be an IPv4 address"
    },
    "secret": {
      "type": "string",
      "description": "Secret, \u2018\u2019 if no auth is used"
    },
    "sessions": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "wxlan_tunnel_session",
        "type": "object",
        "properties": {
          "ap_as_session_id": {
            "type": "string",
            "description": "If `use_ap_as_session_ids`==`true`, only apmac is supported right now. This is the name WLAN should use for wxtunnel_remote_id"
          },
          "comment": {
            "type": "string",
            "description": "Optional, user-specified string for display purpose"
          },
          "enable_cookie": {
            "type": "boolean"
          },
          "ethertype": {
            "type": "string",
            "description": "enum: `ethernet`, `vlan`"
          },
          "local_session_id": {
            "maximum": 2147483647.0,
            "minimum": 1.0,
            "type": "integer",
            "description": "1-2147483647",
            "contentEncoding": "int32"
          },
          "pseudo_802.1ad_enabled": {
            "type": "boolean",
            "description": "Optional. Enables the pseudo 802.1ad QinQ mode where the AP device drops the outer vlan tag (QinQ). This mode is useful when tunneling Mist AP\u2019s to some aggregation routers.",
            "default": false
          },
          "remote_id": {
            "type": "string",
            "description": "Remote-id of the session, has to be unique in the same tunnel"
          },
          "remote_session_id": {
            "maximum": 2147483647.0,
            "minimum": 1.0,
            "type": "integer",
            "description": "1-2147483647",
            "contentEncoding": "int32"
          },
          "use_ap_as_session_ids": {
            "type": "boolean",
            "description": "Whether to use AP (last 4 bytes of MAC currently) as session ids",
            "default": false
          }
        }
      },
      "description": "Sessions to be established with the tunnel. Has to be >= 1 in order for this tunnel to be useful. For management tunnel, it can only have 1"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "udp_port": {
      "type": "integer",
      "description": "UDP port if `use_udp`==`true`",
      "contentEncoding": "int32"
    },
    "use_udp": {
      "type": "boolean",
      "description": "Whether to use UDP instead of IP (proto=115, which is default of L2TPv3)",
      "default": false
    }
  },
  "required": [
    "name"
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
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "dmvpn": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "Whether DMVPN is enabled",
          "default": false
        },
        "holding_time": {
          "type": "integer",
          "description": "Optional; the holding time for NHRP \u2018registration requests\u2019  and \u2018resolution replies\u2019 sent from the Mist AP (in seconds); default 600",
          "contentEncoding": "int32"
        },
        "host_routes": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Optional; list of IPv4 DMVPN peer host ip-addresses to which traffic is forwarded"
        }
      },
      "description": "Dynamic Multipoint VPN configurations"
    },
    "for_mgmt": {
      "type": "boolean",
      "description": "Determined during creation time and cannot be toggled. A management tunnel cannot be used by wxlan rule or by wlan",
      "default": false
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "hello_interval": {
      "maximum": 300.0,
      "minimum": 1.0,
      "type": "integer",
      "description": "In seconds, used as heartbeat to detect if a tunnel is alive. AP will try another peer after missing N hellos specified by hello_retries.",
      "contentEncoding": "int32",
      "default": 60
    },
    "hello_retries": {
      "maximum": 30.0,
      "minimum": 2.0,
      "type": "integer",
      "contentEncoding": "int32",
      "default": 7
    },
    "hostname": {
      "type": "string",
      "description": "Optional, overwrite the hostname in SCCRQ control message, default is  or null, %H and %M can be used, which will be replace with corresponding values:\n  * %H: name of the ap if provided (and will be stripped so it can be used for hostname) and fallbacks to MAC\n  * %M: MAC (e.g. 5c5b350e0060)"
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
    "ipsec": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "Whether ipsec is enabled, requires DMVPN be enabled",
          "default": false
        },
        "psk": {
          "type": "string",
          "description": "IPSec pre-shared key"
        }
      },
      "required": [
        "psk"
      ],
      "description": "IPSec-related configurations; requires DMVPN be enabled"
    },
    "is_static": {
      "type": "boolean",
      "description": "Whether it\u2019s static/unmanaged (i.e. no control session). As the session configurations are not compatible, cannot be toggled.",
      "default": false
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
      "description": "0 to enable PMTU, 552-1500 to start PMTU with a lower MTU",
      "contentEncoding": "int32",
      "default": 0
    },
    "name": {
      "type": "string",
      "description": "The name of the tunnel"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "peers": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of remote peers\u2019 IP or hostname"
    },
    "router_id": {
      "type": "string",
      "description": "Optional, overwrite the router-id in SCCRQ control message, default is \"\" or null, can also be an IPv4 address"
    },
    "secret": {
      "type": "string",
      "description": "Secret, \u2018\u2019 if no auth is used"
    },
    "sessions": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "wxlan_tunnel_session",
        "type": "object",
        "properties": {
          "ap_as_session_id": {
            "type": "string",
            "description": "If `use_ap_as_session_ids`==`true`, only apmac is supported right now. This is the name WLAN should use for wxtunnel_remote_id"
          },
          "comment": {
            "type": "string",
            "description": "Optional, user-specified string for display purpose"
          },
          "enable_cookie": {
            "type": "boolean"
          },
          "ethertype": {
            "type": "string",
            "description": "enum: `ethernet`, `vlan`"
          },
          "local_session_id": {
            "maximum": 2147483647.0,
            "minimum": 1.0,
            "type": "integer",
            "description": "1-2147483647",
            "contentEncoding": "int32"
          },
          "pseudo_802.1ad_enabled": {
            "type": "boolean",
            "description": "Optional. Enables the pseudo 802.1ad QinQ mode where the AP device drops the outer vlan tag (QinQ). This mode is useful when tunneling Mist AP\u2019s to some aggregation routers.",
            "default": false
          },
          "remote_id": {
            "type": "string",
            "description": "Remote-id of the session, has to be unique in the same tunnel"
          },
          "remote_session_id": {
            "maximum": 2147483647.0,
            "minimum": 1.0,
            "type": "integer",
            "description": "1-2147483647",
            "contentEncoding": "int32"
          },
          "use_ap_as_session_ids": {
            "type": "boolean",
            "description": "Whether to use AP (last 4 bytes of MAC currently) as session ids",
            "default": false
          }
        }
      },
      "description": "Sessions to be established with the tunnel. Has to be >= 1 in order for this tunnel to be useful. For management tunnel, it can only have 1"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "udp_port": {
      "type": "integer",
      "description": "UDP port if `use_udp`==`true`",
      "contentEncoding": "int32"
    },
    "use_udp": {
      "type": "boolean",
      "description": "Whether to use UDP instead of IP (proto=115, which is default of L2TPv3)",
      "default": false
    }
  },
  "required": [
    "name"
  ],
  "description": "WxLAn Tunnel"
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

`mistapi.api.v1.sites.wxtunnels.createSiteWxTunnel()`

## Usage Context

Creates a new WxLAN tunnel at a site. Tunnels encapsulate WLAN traffic to a remote endpoint.

## Gotchas

- Tunnel endpoint must be reachable. MTU settings affect throughput.

## Related Endpoints

- [GET_sites_site_id_wxtunnels.md](GET_sites_site_id_wxtunnels.md) — List WxTunnels
- [GET_sites_site_id_wxtunnels_wxtunnel_id.md](GET_sites_site_id_wxtunnels_wxtunnel_id.md) — Tunnel details

## MistHelper Notes

Not currently used by MistHelper directly.
