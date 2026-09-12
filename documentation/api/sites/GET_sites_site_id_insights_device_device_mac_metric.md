# getSiteInsightMetricsForDevice

> getSiteInsightMetricsForDevice

## HTTP

`GET /api/v1/sites/{site_id}/insights/device/{device_mac}/{metric}`

## Description

Get AP Insight Metrics
See metrics possibilities at [List Insight Metrics]($e/Constants%20Definitions/listInsightMetrics)

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| metric | string | Yes | See [List Insight Metrics]($e/Constants%20Definitions/listInsightMetrics) for available metrics |
| device_mac | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| interval | string | No |  |  | Aggregation works by giving a time range plus interval (e.g. 1d, 1h, 10m) where aggregation function would be applied to. |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

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
    "interval": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "page": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "results": {
      "type": "array",
      "items": {
        "oneOf": [
          {
            "type": "string"
          },
          {
            "type": "integer",
            "contentEncoding": "int32"
          }
        ]
      },
      "description": ""
    },
    "rt": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "end",
    "interval",
    "results",
    "start"
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

`mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice()`

## Usage Context

Retrieves detailed insight metrics for a specific device by MAC address (e.g., AP channel utilization, client count trends, uptime).

## Gotchas

- The `metric` parameter must be valid for the device type (AP, switch, or gateway).

## Related Endpoints

- [GET_sites_site_id_insights_client_client_mac_metric.md](GET_sites_site_id_insights_client_client_mac_metric.md) — Client insights
- [GET_sites_site_id_insights_metric.md](GET_sites_site_id_insights_metric.md) — Site-level metrics

## MistHelper Notes

Used by Menu **68** and **69** via `getSiteInsightMetrics`.
