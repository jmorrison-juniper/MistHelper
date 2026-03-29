# listSiteSleImpactedInterfaces

> listSiteSleImpactedInterfaces

## HTTP

`GET /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impacted-interfaces`

## Description

For Wired and WAN SLEs. List the impacted interfaces optionally filtered by classifier and failure type

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
    "end": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "failure": {
      "type": "string"
    },
    "interfaces": {
      "type": "array",
      "items": {
        "title": "sle_impacted_interfaces_interface",
        "type": "object",
        "properties": {
          "degraded": {
            "type": "number"
          },
          "duration": {
            "type": "number"
          },
          "interface_name": {
            "type": "string"
          },
          "switch_mac": {
            "type": "string"
          },
          "switch_name": {
            "type": "string"
          },
          "total": {
            "type": "number"
          }
        }
      },
      "description": ""
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "metric": {
      "type": "string"
    },
    "page": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "total_count": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  }
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

`mistapi.api.v1.sites.sles.listSiteSleImpactedInterfaces()`

## Usage Context

Lists interfaces impacted by SLE failures. Shows which physical ports are contributing to poor experience.

## Gotchas

- Only relevant for wired (switch/gateway) SLE scopes.

## Related Endpoints

- [GET_sites_site_id_sle_scope_scope_id_metric_metric_impact-summary.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_impact-summary.md) — Impact summary
- [GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-switches.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-switches.md) — Impacted switches

## MistHelper Notes

Used by Menu **53** via SLE analysis workflow.
