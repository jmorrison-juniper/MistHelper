# getSiteSleHistogram

> getSiteSleHistogram

## HTTP

`GET /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/histogram`

## Description

Get the histogram for the SLE metric

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
    "data": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "sle_histogram_data_item",
        "required": [
          "value"
        ],
        "type": "object",
        "properties": {
          "range": {
            "type": "array",
            "items": {
              "type": [
                "number",
                "null"
              ]
            },
            "description": ""
          },
          "value": {
            "type": "number"
          }
        }
      },
      "description": ""
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
    },
    "x_label": {
      "minLength": 1,
      "type": "string"
    },
    "y_label": {
      "minLength": 1,
      "type": "string"
    }
  },
  "required": [
    "data",
    "end",
    "metric",
    "start",
    "x_label",
    "y_label"
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

`mistapi.api.v1.sites.sles.getSiteSleHistogram()`

## Usage Context

Retrieves the histogram distribution for an SLE metric. Shows the distribution of user experience scores.

## Gotchas

- Histogram buckets are predefined by the metric type.

## Related Endpoints

- [GET_sites_site_id_sle_scope_scope_id_metric_metric_summary.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_summary.md) — SLE summary
- [GET_sites_site_id_sle_scope_scope_id_metric_metric_threshold.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_threshold.md) — SLE threshold

## MistHelper Notes

Used by Menu **53** via SLE analysis workflow.
