# createOrgVpn

> createOrgVpn

## HTTP

`POST /api/v1/orgs/{org_id}/vpns`

## Description

Create Org VPN

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

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
      "minLength": 1,
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
    "path_selection": {
      "type": "object",
      "properties": {
        "strategy": {
          "type": "string",
          "description": "enum: `disabled`, `simple`, `manual`"
        }
      },
      "description": "Only if `type`==`hub_spoke`"
    },
    "paths": {
      "type": "object",
      "additionalProperties": {
        "title": "vpn_path",
        "type": "object",
        "properties": {
          "bfd_profile": {
            "type": "string",
            "description": "enum: `broadband`, `lte`"
          },
          "bfd_use_tunnel_mode": {
            "type": "boolean",
            "description": "If `type`==`mesh` and for SSR only, whether to use tunnel mode",
            "default": false
          },
          "ip": {
            "type": "string",
            "description": "If different from the wan port"
          },
          "peer_paths": {
            "type": "object",
            "additionalProperties": {
              "title": "vpn_path_peer_paths_peer",
              "type": "object",
              "properties": {
                "preference": {
                  "type": "integer",
                  "contentEncoding": "int32"
                }
              },
              "description": "Preference indicates which outgoing wan should be preferred"
            },
            "description": "If `type`==`mesh`, Property key is the Peer Interface name"
          },
          "pod": {
            "maximum": 128.0,
            "minimum": 1.0,
            "type": "integer",
            "contentEncoding": "int32",
            "default": 1,
            "examples": [
              2
            ]
          },
          "traffic_shaping": {
            "title": "vpn_path_traffic_shaping",
            "type": "object",
            "properties": {
              "class_percentage": {
                "maxItems": 4,
                "minItems": 4,
                "type": "array",
                "items": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "description": "percentages for different class of traffic: high / medium / low / best-effort adding up to 100",
                "default": [
                  80,
                  10,
                  9,
                  1
                ]
              },
              "enabled": {
                "type": "boolean"
              },
              "max_tx_kbps": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int32"
              }
            }
          }
        }
      },
      "description": "For `type`==`hub_spoke`, Property key is the VPN name. For `type`==`mesh`, Property key is the Interface name"
    },
    "type": {
      "type": "string",
      "description": "enum: `hub_spoke`, `mesh`"
    }
  },
  "required": [
    "name",
    "paths"
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
      "minLength": 1,
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
    "path_selection": {
      "type": "object",
      "properties": {
        "strategy": {
          "type": "string",
          "description": "enum: `disabled`, `simple`, `manual`"
        }
      },
      "description": "Only if `type`==`hub_spoke`"
    },
    "paths": {
      "type": "object",
      "additionalProperties": {
        "title": "vpn_path",
        "type": "object",
        "properties": {
          "bfd_profile": {
            "type": "string",
            "description": "enum: `broadband`, `lte`"
          },
          "bfd_use_tunnel_mode": {
            "type": "boolean",
            "description": "If `type`==`mesh` and for SSR only, whether to use tunnel mode",
            "default": false
          },
          "ip": {
            "type": "string",
            "description": "If different from the wan port"
          },
          "peer_paths": {
            "type": "object",
            "additionalProperties": {
              "title": "vpn_path_peer_paths_peer",
              "type": "object",
              "properties": {
                "preference": {
                  "type": "integer",
                  "contentEncoding": "int32"
                }
              },
              "description": "Preference indicates which outgoing wan should be preferred"
            },
            "description": "If `type`==`mesh`, Property key is the Peer Interface name"
          },
          "pod": {
            "maximum": 128.0,
            "minimum": 1.0,
            "type": "integer",
            "contentEncoding": "int32",
            "default": 1,
            "examples": [
              2
            ]
          },
          "traffic_shaping": {
            "title": "vpn_path_traffic_shaping",
            "type": "object",
            "properties": {
              "class_percentage": {
                "maxItems": 4,
                "minItems": 4,
                "type": "array",
                "items": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "description": "percentages for different class of traffic: high / medium / low / best-effort adding up to 100",
                "default": [
                  80,
                  10,
                  9,
                  1
                ]
              },
              "enabled": {
                "type": "boolean"
              },
              "max_tx_kbps": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int32"
              }
            }
          }
        }
      },
      "description": "For `type`==`hub_spoke`, Property key is the VPN name. For `type`==`mesh`, Property key is the Interface name"
    },
    "type": {
      "type": "string",
      "description": "enum: `hub_spoke`, `mesh`"
    }
  },
  "required": [
    "name",
    "paths"
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

`mistapi.api.v1.orgs.vpns.createOrgVpn()`

## Usage Context

Creates a new VPN (WAN overlay) configuration in the organization.

## Gotchas

- VPN configs define hub-spoke or mesh topologies for WAN.

## Related Endpoints

- [GET_orgs_org_id_vpns.md](GET_orgs_org_id_vpns.md) — List VPNs
- [PUT_orgs_org_id_vpns_vpn_id.md](PUT_orgs_org_id_vpns_vpn_id.md) — Update VPN

## MistHelper Notes

VPN listing uses Menu 4 (`listOrgVpns`). Creation is not used directly.
