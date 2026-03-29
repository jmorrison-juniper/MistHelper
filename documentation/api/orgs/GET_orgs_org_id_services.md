# listOrgServices

> listOrgServices

## HTTP

`GET /api/v1/orgs/{org_id}/services`

## Description

Get List of Org Services

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
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "array",
  "items": {
    "title": "service",
    "type": "object",
    "properties": {
      "addresses": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "If `type`==`custom`, IPv4 and/or IPv6 subnets (e.g. 10.0.0.0/8, fd28::/128)",
        "examples": [
          [
            "10.0.0.0/8",
            "172.21.0.0/16",
            "2001:db8:abcd:12::/64",
            "fd28::/128"
          ]
        ]
      },
      "app_categories": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "When `type`==`app_categories`, list of application categories are available through [List App Category Definitions]($e/Constants%20Definitions/listAppCategoryDefinitions)",
        "examples": [
          [
            "Sports"
          ]
        ]
      },
      "app_subcategories": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "When `type`==`app_categories`, list of application categories are available through [List App Sub Category Definitions]($e/Constants%20Definitions/listAppSubCategoryDefinitions)",
        "examples": [
          [
            "Shopping"
          ]
        ]
      },
      "apps": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "When `type`==`apps`, list of applications are available through:\n  * [List Applications]($e/Constants%20Definitions/listApplications)\n  * [List Gateway Applications]($e/Constants%20Definitions/listGatewayApplications)\n  * /insight/top_app_by-bytes?wired=true",
        "examples": [
          [
            "office365",
            "okta"
          ]
        ]
      },
      "client_limit_down": {
        "maximum": 107374182.0,
        "minimum": 0.0,
        "type": "integer",
        "description": "0 means unlimited, value from 0 to 107374182",
        "contentEncoding": "int32",
        "default": 0,
        "examples": [
          300000
        ]
      },
      "client_limit_up": {
        "maximum": 107374182.0,
        "minimum": 0.0,
        "type": "integer",
        "description": "0 means unlimited, value from 0 to 107374182",
        "contentEncoding": "int32",
        "default": 0,
        "examples": [
          300000
        ]
      },
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "description": {
        "type": "string"
      },
      "dscp": {
        "type": "object",
        "description": "For SSR only, when `traffic_type`==`custom`. 0-63 or variable"
      },
      "failover_policy": {
        "type": "string",
        "description": "enum: `non_revertible`, `none`, `revertible`"
      },
      "hostnames": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "If `type`==`custom`, web filtering"
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
      "max_jitter": {
        "type": "object",
        "description": "For SSR only, when `traffic_type`==`custom`, for uplink selection. 0-2147483647 or variable"
      },
      "max_latency": {
        "type": "object",
        "description": "For SSR only, when `traffic_type`==`custom`, for uplink selection. 0-2147483647 or variable"
      },
      "max_loss": {
        "type": "object",
        "description": "For SSR only, when `traffic_type`==`custom`, for uplink selection. 0-100 or variable"
      },
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
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
      "service_limit_down": {
        "maximum": 107374182.0,
        "minimum": 0.0,
        "type": "integer",
        "description": "0 means unlimited, value from 0 to 107374182",
        "contentEncoding": "int32",
        "default": 0,
        "examples": [
          300000
        ]
      },
      "service_limit_up": {
        "maximum": 107374182.0,
        "minimum": 0.0,
        "type": "integer",
        "description": "0 means unlimited, value from 0 to 107374182",
        "contentEncoding": "int32",
        "default": 0,
        "examples": [
          300000
        ]
      },
      "sle_enabled": {
        "type": "boolean",
        "description": "Whether to enable measure SLE",
        "default": false
      },
      "specs": {
        "type": "array",
        "items": {
          "title": "service_spec",
          "type": "object",
          "properties": {
            "port_range": {
              "type": "string",
              "description": "Port number, port range, or variable",
              "examples": [
                "8080,8443"
              ]
            },
            "protocol": {
              "type": "string",
              "description": "`https`/ `tcp` / `udp` / `icmp` / `gre` / `any` / `:protocol_number`, `protocol_number` is between 1-254",
              "default": "any",
              "examples": [
                "tcp"
              ]
            }
          }
        },
        "description": "When `type`==`custom`, optional, if it doesn't exist, http and https is assumed"
      },
      "ssr_relaxed_tcp_state_enforcement": {
        "type": "boolean",
        "default": false
      },
      "traffic_class": {
        "type": "string",
        "description": "when `traffic_type`==`custom`. enum: `best_effort`, `high`, `low`, `medium`"
      },
      "traffic_type": {
        "type": "string",
        "description": "values from [List Traffic Types]($e/Constants%20Definitions/listTrafficTypes)",
        "default": "data_best_effort"
      },
      "type": {
        "type": "string",
        "description": "enum: `app_categories`, `apps`, `custom`, `urls`"
      },
      "urls": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "When `type`==`urls`, no need for spec as URL can encode the ports being used"
      }
    },
    "description": "Applications used for the Gateway configurations"
  },
  "description": "",
  "examples": [
    [
      {
        "addresses": [
          "string"
        ],
        "apps": [
          "string"
        ],
        "dscp": 8,
        "hostnames": [
          "string"
        ],
        "max_jitter": 0,
        "max_latency": 0,
        "max_loss": 0,
        "name": "string",
        "specs": [
          {
            "port_range": "0",
            "protocol": "any"
          }
        ],
        "traffic_class": "best_effort",
        "traffic_type": "default",
        "type": "custom"
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.services.listOrgServices()`

## Usage Context

Lists all service definitions for the organization.

## Gotchas

- Services can be custom-defined or use built-in application signatures.

## Related Endpoints

- [GET_orgs_org_id_services_service_id.md](GET_orgs_org_id_services_service_id.md) — Get specific service
- [POST_orgs_org_id_services.md](POST_orgs_org_id_services.md) — Create service

## MistHelper Notes

Used by MistHelper via `listOrgServices` in Menu 4.
