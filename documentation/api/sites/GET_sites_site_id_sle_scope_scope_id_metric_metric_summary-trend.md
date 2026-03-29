# getSiteSleSummaryTrend

> getSiteSleSummaryTrend

## HTTP

`GET /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/summary-trend`

## Description

Get the summary for the SLE metric trend

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
    "classifiers": {
      "uniqueItems": true,
      "type": "array",
      "items": {
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
      "description": ""
    },
    "end": {
      "type": "number"
    },
    "sle": {
      "title": "sle_summary_sle",
      "required": [
        "interval",
        "name",
        "samples",
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
          "title": "sle_summary_sle_samples",
          "required": [
            "degraded",
            "total",
            "value"
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
            },
            "value": {
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
    "start": {
      "type": "number"
    }
  },
  "required": [
    "classifiers",
    "end",
    "sle",
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

`mistapi.api.v1.sites.sles.getSiteSleSummaryTrend()`

## Usage Context

Retrieves the time-series trend for an SLE metric summary, showing how overall SLE scores change over time.

## Gotchas

- Data granularity adjusts based on time range (hourly for short, daily for long).

## Related Endpoints

- [GET_sites_site_id_sle_scope_scope_id_metric_metric_summary.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_summary.md) — SLE summary
- [GET_sites_site_id_sle_scope_scope_id_metric_metric_histogram.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_histogram.md) — Score histogram

## MistHelper Notes

Used by Menu **53** via SLE analysis workflow.
