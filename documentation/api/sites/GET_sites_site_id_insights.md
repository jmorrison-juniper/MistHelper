# getSiteInsightMetrics

> getSiteInsightMetrics

## HTTP

`GET /api/v1/sites/{site_id}/insights`

## Description

Get Site Insight Metrics

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| metrics | string | Yes |  |  | Comma separated Metric names, e.g. `num_clients,num_aps`. See possible values at [List Insight Metrics](/#operations/listInsightMetrics) |
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

`mistapi.api.v1.sites.insights.getSiteInsightMetrics()`

## Usage Context

Retrieves site-wide insight metrics aggregated across all devices and clients. Provides high-level performance overview.

## Gotchas

- Available metrics depend on site configuration and device types deployed.
- The live cloud does not serve the query form that this page shows. On 2026-09-23, a GET with `?metrics=<name>` got HTTP 404 and the body `{}`. A comma list got the same result. Issue #3266 records the probe.
- The live cloud serves the path form `GET /api/v1/sites/{site_id}/insights/{metric}`. The same probe got HTTP 200 with data for 55 of 64 metrics, and HTTP 400 for 9 metrics.
- mistapi does not raise an exception for an HTTP 400. It returns the error body in `data`. A caller must read `status_code` before it uses the body as metric data.

## Related Endpoints

- [GET_sites_site_id_insights_client_client_mac.md](GET_sites_site_id_insights_client_client_mac.md) — Client-level insights
- [GET_sites_site_id_insights_device_device_mac_metric.md](GET_sites_site_id_insights_device_device_mac_metric.md) — Device-level insights

## MistHelper Notes

Menu **74** (Export Site Insight Metrics) reads this endpoint. It sends the path form through `apisession.mist_get()`, because the SDK function `getSiteInsightMetrics()` sends the query form. The export keeps `api_function_name="getSiteInsightMetrics"`, so the table name does not change. Menu 74 tells the operator each refused metric, with its HTTP status and its reason.
