# searchOrgTunnelsStats

> searchOrgTunnelsStats

## HTTP

`GET /api/v1/orgs/{org_id}/stats/tunnels/search`

## Description

By default the endpoint returns only `wxtunnel` type stats, to get `wan` type stats
you need to specify `type=wan` in the query parameters.


Tunnel types:
- `wxtunnel` (default) - A WxLan Tunnel (WxTunnel) are used to create a secure connection between Juniper Mist Access Points and third-party VPN concentrators using protocols such as L2TPv3 or dmvpn.
- `wan` - A WAN Tunnel is a secure connection between two Gateways, typically used for site-to-site or mesh connectivity. It can be configured with various protocols and encryption methods.


If `type` is not specified or `type`==`wxtunnel`, the following parameters are supported:
- `mxcluster_id` - the MX cluster ID
- `site_id` - the site ID
- `wxtunnel_id` - the WX tunnel ID
- `ap` - the AP MAC address


If `type`==`wan`, the following parameters are supported:
- `mac` - the MAC address of the WAN device
- `node` - the node ID
- `peer_ip` - the peer IP address
- `peer_host` - the peer host name
- `ip` - the IP address of the WAN device
- `tunnel_name` - the name of the tunnel
- `protocol` - the protocol used for the tunnel
- `auth_algo` - the authentication algorithm used for the tunnel
- `encrypt_algo` - the encryption algorithm used for the tunnel
- `ike_version` - the IKE version used for the tunnel
- `up` - the status of the tunnel (up or down)


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
| mxcluster_id | string | No |  |  | If `type`==`wxtunnel` |
| site_id | string | No |  |  |  |
| wxtunnel_id | string | No |  |  | If `type`==`wxtunnel` |
| ap | string | No |  |  | If `type`==`wxtunnel` |
| mac | string | No |  |  | If `type`==`wan` |
| node | string | No |  |  | If `type`==`wan` |
| peer_ip | string | No |  |  | If `type`==`wan` |
| peer_host | string | No |  |  | If `type`==`wan` |
| ip | string | No |  |  | If `type`==`wan` |
| tunnel_name | string | No |  |  | If `type`==`wan` |
| protocol | string | No |  |  | If `type`==`wan` |
| auth_algo | string | No |  |  | If `type`==`wan` |
| encrypt_algo | string | No |  |  | If `type`==`wan` |
| ike_version | string | No |  |  | If `type`==`wan` |
| up | string | No |  |  | If `type`==`wan` |
| type | string | No |  |  |  |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 5m |  | Duration like 7d, 2w |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "next": {
      "type": "string"
    },
    "results": {
      "type": "array",
      "items": {
        "oneOf": [
          {
            "title": "stats_mxtunnel",
            "required": [
              "remote_ip"
            ],
            "type": "object",
            "properties": {
              "ap": {
                "type": "string",
                "readOnly": true
              },
              "for_site": {
                "type": "boolean",
                "readOnly": true
              },
              "fwupdate": {
                "title": "fwupdate_stat",
                "type": "object",
                "properties": {
                  "progress": {
                    "maximum": 100.0,
                    "minimum": 0.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "readOnly": true,
                    "examples": [
                      10
                    ]
                  },
                  "status": {
                    "type": "object",
                    "description": "enum: `inprogress`, `failed`, `upgraded`, `success`, `scheduled`, `error`",
                    "readOnly": true
                  },
                  "status_id": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "readOnly": true,
                    "examples": [
                      5
                    ]
                  },
                  "timestamp": {
                    "type": "number",
                    "description": "Epoch (seconds)",
                    "readOnly": true
                  },
                  "will_retry": {
                    "type": [
                      "boolean",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      false
                    ]
                  }
                }
              },
              "last_seen": {
                "type": [
                  "number",
                  "null"
                ],
                "description": "Last seen timestamp",
                "readOnly": true,
                "examples": [
                  1470417522
                ]
              },
              "mtu": {
                "type": "integer",
                "contentEncoding": "int32",
                "readOnly": true
              },
              "mxcluster_id": {
                "type": "string",
                "contentEncoding": "uuid",
                "readOnly": true
              },
              "mxedge_id": {
                "type": "string",
                "contentEncoding": "uuid",
                "readOnly": true
              },
              "mxtunnel_id": {
                "type": "string",
                "contentEncoding": "uuid",
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
              "peer_mxedge_id": {
                "type": "string",
                "description": "MxEdge ID of the peer(mist edge to mist edge tunnel)",
                "contentEncoding": "uuid",
                "readOnly": true
              },
              "remote_ip": {
                "type": "string",
                "readOnly": true
              },
              "remote_port": {
                "type": "integer",
                "contentEncoding": "int32",
                "readOnly": true
              },
              "rx_control_pkts": {
                "type": "integer",
                "contentEncoding": "int32",
                "readOnly": true
              },
              "sessions": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "title": "stats_mxtunnel_session",
                  "required": [
                    "local_sid",
                    "remote_id",
                    "remote_sid",
                    "state"
                  ],
                  "type": "object",
                  "properties": {
                    "local_sid": {
                      "type": "integer",
                      "description": "Remote sessions id (dynamically unless Tunnel is said to be static)",
                      "contentEncoding": "int32"
                    },
                    "remote_id": {
                      "type": "string",
                      "description": "WxlanTunnel Remote ID"
                    },
                    "remote_sid": {
                      "type": "integer",
                      "description": "Remote sessions id (dynamically unless Tunnel is said to be static)",
                      "contentEncoding": "int32"
                    },
                    "state": {
                      "type": "string"
                    }
                  }
                },
                "description": "List of sessions",
                "readOnly": true
              },
              "site_id": {
                "type": "string",
                "contentEncoding": "uuid",
                "readOnly": true,
                "examples": [
                  "441a1214-6928-442a-8e92-e1d34b8ec6a6"
                ]
              },
              "state": {
                "type": "string",
                "description": "enum: `established`, `established_with_sessions`, `idle`, `wait-ctrl-conn`, `wait-ctrl-reply`",
                "readOnly": true
              },
              "tx_control_pkts": {
                "type": "integer",
                "contentEncoding": "int32",
                "readOnly": true
              },
              "uptime": {
                "type": "integer",
                "contentEncoding": "int32",
                "readOnly": true
              }
            },
            "description": "MxTunnels statistics"
          },
          {
            "title": "stats_wan_tunnel",
            "required": [
              "peer_ip"
            ],
            "type": "object",
            "properties": {
              "auth_algo": {
                "type": "string",
                "description": "Authentication algorithm"
              },
              "encrypt_algo": {
                "type": "string",
                "description": "Encryption algorithm"
              },
              "ike_version": {
                "type": "string",
                "description": "IKE version"
              },
              "ip": {
                "type": "string",
                "description": "IP Address"
              },
              "last_event": {
                "type": "string",
                "description": "Reason of why the tunnel is down"
              },
              "mac": {
                "type": "string",
                "description": "Router mac address"
              },
              "node": {
                "type": "string",
                "description": "Node0/node1"
              },
              "org_id": {
                "type": "string",
                "contentEncoding": "uuid",
                "readOnly": true,
                "examples": [
                  "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
                ]
              },
              "peer_host": {
                "type": "string",
                "description": "Peer host"
              },
              "peer_ip": {
                "type": "string",
                "description": "Peer ip address"
              },
              "priority": {
                "type": "string",
                "description": "enum: `primary`, `secondary`"
              },
              "protocol": {
                "type": "string",
                "description": "enum: `gre`, `ipsec`"
              },
              "rx_bytes": {
                "type": [
                  "integer",
                  "null"
                ],
                "description": "Amount of traffic received since connection",
                "contentEncoding": "int64",
                "readOnly": true,
                "examples": [
                  8515104416
                ]
              },
              "rx_pkts": {
                "type": [
                  "integer",
                  "null"
                ],
                "description": "Amount of packets received since connection",
                "contentEncoding": "int64",
                "readOnly": true,
                "examples": [
                  57770567
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
              "tunnel_name": {
                "type": "string",
                "description": "Mist Tunnel Name"
              },
              "tx_bytes": {
                "type": [
                  "integer",
                  "null"
                ],
                "description": "Amount of traffic sent since connection",
                "contentEncoding": "int64",
                "readOnly": true,
                "examples": [
                  211217389682
                ]
              },
              "tx_pkts": {
                "type": [
                  "integer",
                  "null"
                ],
                "description": "Amount of packets sent since connection",
                "contentEncoding": "int64",
                "readOnly": true,
                "examples": [
                  812204062
                ]
              },
              "up": {
                "type": "boolean"
              },
              "uptime": {
                "type": "integer",
                "description": "Duration from first (or last) SA was established",
                "contentEncoding": "int32"
              },
              "wan_name": {
                "type": "string",
                "description": "WAN interface name",
                "examples": [
                  "wan"
                ]
              }
            }
          }
        ]
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "end",
    "limit",
    "results",
    "start",
    "total"
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

`mistapi.api.v1.orgs.stats_-_tunnels.searchOrgTunnelsStats()`

## Usage Context

Searches for tunnel statistics across the organization.

## Gotchas

- Can filter by tunnel type, peer IP, and status.

## Related Endpoints

- [GET_orgs_org_id_stats_tunnels_count.md](GET_orgs_org_id_stats_tunnels_count.md) — Count tunnels
- [GET_orgs_org_id_stats_vpn_peers_search.md](GET_orgs_org_id_stats_vpn_peers_search.md) — VPN peers

## MistHelper Notes

Not currently used by MistHelper directly.
