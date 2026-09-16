# getSiteInsightMetricsForAP

> getSiteInsightMetricsForAP

## HTTP

`GET /api/v1/sites/{site_id}/insights/ap/{device_id}/stats`

## Description

Get AP Insight Metrics

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| metrics | string | Yes |  |  | Comma separated Metric names, e.g. `num_clients,num_stressed_clients`. See possible values at [List Insight Metrics](/#operations/listInsightMetrics) |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Time-series insight metric response for a device",
  "properties": {
    "end": {
      "description": "Epoch timestamp for the end of the metric query window",
      "type": "integer"
    },
    "interval": {
      "description": "Aggregation interval in seconds for each metric sample",
      "type": "integer"
    },
    "limit": {
      "description": "Maximum number of metric samples returned in this page",
      "type": "integer"
    },
    "page": {
      "description": "Returned page number for paginated metric samples",
      "type": "integer"
    },
    "results": {
      "description": "Device metric result values aligned with the response timestamps",
      "items": {
        "description": "Device metric result value, returned as a string or integer",
        "oneOf": [
          {
            "type": "string"
          },
          {
            "type": "integer"
          }
        ]
      },
      "type": "array"
    },
    "rt": {
      "description": "Unique string values returned or accepted by this schema",
      "items": {
        "type": "string"
      },
      "type": "array",
      "uniqueItems": true
    },
    "start": {
      "description": "Epoch timestamp for the start of the metric query window",
      "type": "integer"
    }
  },
  "required": [
    "end",
    "interval",
    "results",
    "start"
  ],
  "type": "object"
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

`mistapi.api.v1.sites.insights.getSiteInsightMetricsForAP()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
