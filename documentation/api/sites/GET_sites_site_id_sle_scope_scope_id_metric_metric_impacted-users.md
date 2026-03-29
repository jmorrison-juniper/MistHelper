# listSiteSleImpactedWirelessClients

> listSiteSleImpactedWirelessClients

## HTTP

`GET /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-users`

## Description

For Wireless SLEs. List the impacted wireless users optionally filtered by classifier and failure type

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| scope | string | Yes |  |
| scope_id | string | Yes |  |
| metric | string | Yes | Values from `listSiteSlesMetrics` |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| classifier | string | No |  |  |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "classifier": {
      "type": "string"
    },
    "clients": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "sle_impacted_users_client",
        "type": "object",
        "properties": {
          "degraded": {
            "type": "number"
          },
          "duration": {
            "type": "number"
          },
          "gateways": {
            "type": "array",
            "items": {
              "title": "sle_impacted_client_gateway",
              "type": "object",
              "properties": {
                "chassis_mac": {
                  "type": "string"
                },
                "gateway_mac": {
                  "type": "string"
                },
                "gateway_name": {
                  "type": "string"
                },
                "interfaces": {
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
          "mac": {
            "type": "string"
          },
          "name": {
            "type": "string"
          },
          "src_ip": {
            "type": "string"
          },
          "total": {
            "type": "number"
          }
        }
      },
      "description": ""
    },
    "end": {
      "type": "number"
    },
    "failure": {
      "type": "string"
    },
    "limit": {
      "type": "number"
    },
    "metric": {
      "minLength": 1,
      "type": "string"
    },
    "page": {
      "type": "number"
    },
    "start": {
      "type": "number"
    },
    "total_count": {
      "type": "number"
    },
    "users": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "sle_impacted_users_user",
        "type": "object",
        "properties": {
          "ap_mac": {
            "type": "string"
          },
          "ap_name": {
            "type": "string"
          },
          "degraded": {
            "type": "number"
          },
          "device_os": {
            "type": "string"
          },
          "device_type": {
            "type": "string"
          },
          "duration": {
            "type": "number"
          },
          "mac": {
            "type": "string"
          },
          "name": {
            "type": "string"
          },
          "ssid": {
            "type": "string"
          },
          "total": {
            "type": "number"
          },
          "wlan_id": {
            "type": "string"
          }
        }
      },
      "description": ""
    }
  },
  "required": [
    "classifier",
    "end",
    "failure",
    "limit",
    "metric",
    "page",
    "start",
    "total_count"
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

`mistapi.api.v1.sites.sles.listSiteSleImpactedWirelessClients()`

## Usage Context

Lists users impacted by SLE failures. Provides user identity context for experience issues.

## Gotchas

- User identification depends on 802.1X or NAC being configured.

## Related Endpoints

- [GET_sites_site_id_sle_scope_scope_id_metric_metric_impact-summary.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_impact-summary.md) — Impact summary
- [GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-clients.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-clients.md) — Impacted clients

## MistHelper Notes

Used by Menu **53** via SLE analysis workflow.
