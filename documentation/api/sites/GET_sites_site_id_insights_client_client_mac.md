# getSiteInsightMetricsForClient

> getSiteInsightMetricsForClient

## HTTP

`GET /api/v1/sites/{site_id}/insights/client/{client_mac}`

## Description

Get Client Insight Metrics

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| metrics | string | Yes |  |  | Comma separated Metric names, e.g. `top-app-by-num_client,top-app-by-bytes`. See possible values at [List Insight Metrics](/#operations/listInsightMetrics) |
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
  "description": "Insight metric response for a requested time range and aggregation interval",
  "properties": {
    "end": {
      "description": "Window end timestamp for the returned insight metrics",
      "type": "integer"
    },
    "interval": {
      "description": "Aggregation interval used for the metric results",
      "type": "integer"
    },
    "limit": {
      "description": "Maximum number of insight metric result items returned",
      "type": "integer"
    },
    "results": {
      "description": "Results depends on the `metric` - some return numbers (e.g. bytes, ap-count), others return objects",
      "items": {
        "anyOf": [
          {
            "type": "number"
          },
          {
            "additionalProperties": true,
            "type": "object"
          }
        ],
        "description": "Insight metric result item, returned either as a number or an object depending on the requested metric"
      },
      "type": "array",
      "uniqueItems": true
    },
    "start": {
      "description": "Window start timestamp for the returned insight metrics",
      "type": "integer"
    }
  },
  "required": [
    "end",
    "interval",
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

`mistapi.api.v1.sites.insights.getSiteInsightMetricsForClient()`

## Usage Context

Retrieves detailed insight metrics for a specific wireless client by MAC address (e.g., throughput, latency, RSSI over time).

## Gotchas

- Requires a valid `metrics` query parameter. Available metrics vary by client type and activity.
- Time range must be specified for meaningful trend data.
- The live Mist cloud answers this query form with HTTP 404 and an empty body. A live probe on 2026-09-23 found this result for all 12 client-scope metrics. The path form `GET /api/v1/sites/{site_id}/insights/client/{client_mac}/{metric}` returns HTTP 200 with data. Issue #3297 records the probe.

## Related Endpoints

- [GET_sites_site_id_insights_device_device_mac_metric.md](GET_sites_site_id_insights_device_device_mac_metric.md) — Device insights
- [GET_sites_site_id_insights.md](GET_sites_site_id_insights.md) — Site-level insight metrics

## MistHelper Notes

Menu **75** requests the path form `/api/v1/sites/{site_id}/insights/client/{client_mac}/{metric}` through `apisession.mist_get()`. The SDK function builds the query form, and the live cloud refuses that form. Issue #3297 records the probe.
