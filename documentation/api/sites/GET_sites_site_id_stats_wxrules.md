# getSiteWxRulesUsage

> getSiteWxRulesUsage

## HTTP

`GET /api/v1/sites/{site_id}/stats/wxrules`

## Description

Get Wxlan Rule usage

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

WxRule Stats

```json
{
  "type": "array",
  "items": {
    "title": "stats_wxrule",
    "required": [
      "action",
      "client_mac",
      "dst_allow_wxtags",
      "dst_deny_wxtags",
      "dst_wxtags",
      "name",
      "order",
      "src_wxtags",
      "usage"
    ],
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "description": "enum: `allow`, `block`"
      },
      "client_mac": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "",
        "examples": [
          [
            "3bbbf819bb6f",
            "bd96cbc4910f"
          ]
        ]
      },
      "dst_allow_wxtags": {
        "type": "array",
        "items": {
          "type": "string",
          "contentEncoding": "uuid"
        },
        "description": "",
        "examples": [
          [
            "fff34466-eec0-3756-6765-381c728a6037",
            "eee2c7b0-d1d0-5a30-f349-e35fa43dc3b3"
          ]
        ]
      },
      "dst_deny_wxtags": {
        "type": "array",
        "items": {
          "type": "string",
          "contentEncoding": "uuid"
        },
        "description": "",
        "examples": [
          [
            "aaa34466-eec0-3756-6765-381c728a6037",
            "bbb2c7b0-d1d0-5a30-f349-e35fa43dc3b3"
          ]
        ]
      },
      "dst_wxtags": {
        "type": "array",
        "items": {
          "type": "string",
          "contentEncoding": "uuid"
        },
        "description": "",
        "examples": [
          [
            "d4134466-eec0-3756-6765-381c728a6037",
            "1a42c7b0-d1d0-5a30-f349-e35fa43dc3b3"
          ]
        ]
      },
      "name": {
        "type": "string",
        "examples": [
          "Guest"
        ]
      },
      "order": {
        "type": "integer",
        "contentEncoding": "int32",
        "examples": [
          1
        ]
      },
      "src_wxtags": {
        "type": "array",
        "items": {
          "type": "string",
          "contentEncoding": "uuid"
        },
        "description": "",
        "examples": [
          [
            "8bfc2490-d726-3587-038d-cb2e71bd2330",
            "3aa8e73f-9f46-d827-8d6a-567bb7e67fc9"
          ]
        ]
      },
      "usage": {
        "type": "object",
        "additionalProperties": {
          "title": "stats_wxrule_usage_properties",
          "type": "object",
          "properties": {
            "num_flows": {
              "type": "integer",
              "contentEncoding": "int32"
            }
          }
        },
        "examples": [
          {
            "1a42c7b0-d1d0-5a30-f349-e35fa43dc3b3": {
              "num_flows": 60
            },
            "d4134466-eec0-3756-6765-381c728a6037": {
              "num_flows": 60
            }
          }
        ]
      }
    },
    "description": "Wxrule statistics"
  },
  "description": "",
  "examples": [
    [
      {
        "action": "allow",
        "client_mac": [
          "3bbbf819bb6f",
          "bd96cbc4910f"
        ],
        "dst_allow_wxtags": [
          "fff34466-eec0-3756-6765-381c728a6037",
          "eee2c7b0-d1d0-5a30-f349-e35fa43dc3b3"
        ],
        "dst_deny_wxtags": [
          "aaa34466-eec0-3756-6765-381c728a6037",
          "bbb2c7b0-d1d0-5a30-f349-e35fa43dc3b3"
        ],
        "dst_wxtags": [
          "d4134466-eec0-3756-6765-381c728a6037",
          "1a42c7b0-d1d0-5a30-f349-e35fa43dc3b3"
        ],
        "name": "Guest",
        "order": 1,
        "src_wxtags": [
          "8bfc2490-d726-3587-038d-cb2e71bd2330",
          "3aa8e73f-9f46-d827-8d6a-567bb7e67fc9"
        ],
        "usage": {
          "1a42c7b0-d1d0-5a30-f349-e35fa43dc3b3": {
            "num_flows": 60
          },
          "d4134466-eec0-3756-6765-381c728a6037": {
            "num_flows": 60
          }
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

`mistapi.api.v1.sites.stats_-_wxrules.getSiteWxRulesUsage()`

## Usage Context

Retrieves statistics for WxRules (WLAN restriction rules) at a site, showing rule hit counts.

## Gotchas

- Stats reflect rule matches, not necessarily blocked traffic.

## Related Endpoints

- [GET_sites_site_id_wxrules.md](GET_sites_site_id_wxrules.md) — WxRule configuration
- [GET_sites_site_id_wxtags.md](GET_sites_site_id_wxtags.md) — WxTag configuration

## MistHelper Notes

Not currently used by MistHelper directly.
