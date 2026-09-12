# getSiteSleSummary

> **DEPRECATED** -- This endpoint is deprecated and may be removed in a future release.

> getSiteSleSummary

## HTTP

`GET /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/summary`

## Description

Get the summary for the SLE metric


This API Endpoint is deprecated and replaced by [Get Site SLE Summary Trend]($e/Sites%20SLEs/getSiteSleSummaryTrend)

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
        "title": "sle_classifier",
        "required": [
          "impact",
          "interval",
          "name",
          "x_label",
          "y_label"
        ],
        "type": "object",
        "properties": {
          "impact": {
            "title": "sle_classifier_impact",
            "required": [
              "num_aps",
              "num_users",
              "total_aps",
              "total_users"
            ],
            "type": "object",
            "properties": {
              "num_aps": {
                "type": "number"
              },
              "num_users": {
                "type": "number"
              },
              "total_aps": {
                "type": "number"
              },
              "total_users": {
                "type": "number"
              }
            }
          },
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
    "events": {
      "type": "array",
      "items": {
        "type": "object"
      },
      "description": ""
    },
    "impact": {
      "title": "sle_summary_impact",
      "required": [
        "num_aps",
        "num_users",
        "total_aps",
        "total_users"
      ],
      "type": "object",
      "properties": {
        "num_aps": {
          "type": "number"
        },
        "num_users": {
          "type": "number"
        },
        "total_aps": {
          "type": "number"
        },
        "total_users": {
          "type": "number"
        }
      }
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
    "events",
    "impact",
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

`mistapi.api.v1.sites.sles.getSiteSleSummary()`

## Usage Context

Retrieves the overall SLE summary for a specific metric and scope. Shows the percentage of users/sessions meeting the SLE threshold.

## Gotchas

- Summary is computed over the requested time range. Default varies by API version.

## Related Endpoints

- [GET_sites_site_id_sle_scope_scope_id_metric_metric_summary-trend.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_summary-trend.md) — Trend over time
- [GET_sites_site_id_sle_scope_scope_id_metric_metric_classifiers.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_classifiers.md) — Failure classifiers

## MistHelper Notes

Used by Menu **53** via SLE analysis workflow.
