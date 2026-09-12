# updateOrgMxTunnel

> updateOrgMxTunnel

## HTTP

`PUT /api/v1/orgs/{org_id}/mxtunnels/{mxtunnel_id}`

## Description

Update Org MxTunnel

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| mxtunnel_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "anchor_mxtunnel_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "List of anchor mxtunnels used for forming edge to edge tunnels"
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
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "hello_interval": {
      "maximum": 300.0,
      "minimum": 1.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "In seconds, used as heartbeat to detect if a tunnel is alive. AP will try another peer after missing N hellos specified by `hello_retries`.",
      "contentEncoding": "int32",
      "default": 60
    },
    "hello_retries": {
      "maximum": 30.0,
      "minimum": 2.0,
      "type": [
        "integer",
        "null"
      ],
      "contentEncoding": "int32",
      "default": 7
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
      "title": "mxtunnel_ipsec",
      "type": "object",
      "properties": {
        "dns_servers": {
          "type": [
            "array",
            "null"
          ],
          "items": {
            "type": "string"
          },
          "description": ""
        },
        "dns_suffix": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": ""
        },
        "enabled": {
          "type": "boolean"
        },
        "extra_routes": {
          "type": "array",
          "items": {
            "title": "mxtunnel_ipsec_extra_route",
            "type": "object",
            "properties": {
              "dest": {
                "type": "string"
              },
              "next_hop": {
                "type": "string"
              }
            }
          },
          "description": ""
        },
        "split_tunnel": {
          "type": "boolean"
        },
        "use_mxedge": {
          "type": "boolean"
        }
      }
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
    "mxcluster_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "List of mxclusters to deploy this tunnel to"
    },
    "name": {
      "type": [
        "string",
        "null"
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
    "anchor_mxtunnel_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "List of anchor mxtunnels used for forming edge to edge tunnels"
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
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "hello_interval": {
      "maximum": 300.0,
      "minimum": 1.0,
      "type": [
        "integer",
        "null"
      ],
      "description": "In seconds, used as heartbeat to detect if a tunnel is alive. AP will try another peer after missing N hellos specified by `hello_retries`.",
      "contentEncoding": "int32",
      "default": 60
    },
    "hello_retries": {
      "maximum": 30.0,
      "minimum": 2.0,
      "type": [
        "integer",
        "null"
      ],
      "contentEncoding": "int32",
      "default": 7
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
      "title": "mxtunnel_ipsec",
      "type": "object",
      "properties": {
        "dns_servers": {
          "type": [
            "array",
            "null"
          ],
          "items": {
            "type": "string"
          },
          "description": ""
        },
        "dns_suffix": {
          "uniqueItems": true,
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": ""
        },
        "enabled": {
          "type": "boolean"
        },
        "extra_routes": {
          "type": "array",
          "items": {
            "title": "mxtunnel_ipsec_extra_route",
            "type": "object",
            "properties": {
              "dest": {
                "type": "string"
              },
              "next_hop": {
                "type": "string"
              }
            }
          },
          "description": ""
        },
        "split_tunnel": {
          "type": "boolean"
        },
        "use_mxedge": {
          "type": "boolean"
        }
      }
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
    "mxcluster_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "List of mxclusters to deploy this tunnel to"
    },
    "name": {
      "type": [
        "string",
        "null"
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
  "description": "MxTunnel"
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

`mistapi.api.v1.orgs.mxtunnels.updateOrgMxTunnel()`

## Usage Context

Updates an existing Mist Tunnel configuration.

## Gotchas

- Tunnel changes may cause brief reconnections for APs using this tunnel.

## Related Endpoints

- [GET_orgs_org_id_mxtunnels_mxtunnel_id.md](GET_orgs_org_id_mxtunnels_mxtunnel_id.md) — Get tunnel
- [POST_orgs_org_id_mxtunnels.md](POST_orgs_org_id_mxtunnels.md) — Create tunnel

## MistHelper Notes

Not currently used by MistHelper directly.
