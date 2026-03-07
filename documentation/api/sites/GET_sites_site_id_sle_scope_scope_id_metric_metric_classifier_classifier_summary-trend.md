# getSiteSleClassifierSummaryTrend

> getSiteSleClassifierSummaryTrend

## HTTP

`GET /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/classifier/{classifier}/summary-trend`

## Description

Get SLE classifier Summary Trend

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| scope | string | Yes |  |
| scope_id | string | Yes | * site_id if `scope`==`site` * device_id if `scope`==`ap`, `scope`==`switch` or `scope`==`gateway` * mac if `scope`==`client` |
| metric | string | Yes | Values from `listSiteSlesMetrics` |
| classifier | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |

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
      "title": "sle_trend_classifier",
      "required": [
        "interval",
        "name",
        "x_label",
        "y_label"
      ],
      "type": "object",
      "properties": {
        "interval": {
          "type": "number"
        },
        "name": {
          "minLength": 1,
          "type": "string"
        },
        "samples": {
          "title": "sle_classifier_samples",
          "required": [
            "degraded",
            "duration",
            "total"
          ],
          "type": "object",
          "properties": {
            "degraded": {
              "type": "array",
              "items": {
                "oneOf": [
                  {
                    "type": "number"
                  }
                ]
              },
              "description": ""
            },
            "duration": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "description": ""
            },
            "total": {
              "type": "array",
              "items": {
                "oneOf": [
                  {
                    "type": "number"
                  }
                ]
              },
              "description": ""
            }
          }
        },
        "x_label": {
          "minLength": 1,
          "type": "string"
        },
        "y_label": {
          "minLength": 1,
          "type": "string"
        }
      }
    },
    "end": {
      "type": "number"
    },
    "metric": {
      "minLength": 1,
      "type": "string"
    },
    "start": {
      "type": "number"
    }
  },
  "required": [
    "classifier",
    "end",
    "metric",
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.sles.getSiteSleClassifierSummaryTrend()`

## Usage Context

Retrieves the time-series trend for a specific SLE classifier, showing how that root cause category changes over time.

## Gotchas

- Trend granularity depends on the time range requested.

## Related Endpoints

- [GET_sites_site_id_sle_scope_scope_id_metric_metric_classifier_classifier_summary.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_classifier_classifier_summary.md) — Classifier summary
- [GET_sites_site_id_sle_scope_scope_id_metric_metric_summary-trend.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_summary-trend.md) — Overall trend

## MistHelper Notes

Used by Menu **53** via SLE analysis workflow.
