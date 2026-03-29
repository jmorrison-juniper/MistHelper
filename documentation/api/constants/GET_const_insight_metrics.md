# listInsightMetrics

> listInsightMetrics

## HTTP

`GET /api/v1/const/insight_metrics`

## Description

List Insight Metrics

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

Insight Metrics Definition

```json
{
  "type": "object",
  "additionalProperties": {
    "title": "const_insight_metrics_property",
    "type": "object",
    "properties": {
      "ctype": {
        "uniqueItems": true,
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": ""
      },
      "description": {
        "type": "string"
      },
      "example": {
        "anyOf": [
          {
            "type": "array",
            "items": {
              "anyOf": [
                {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                {
                  "type": "number"
                },
                {
                  "type": "string"
                },
                {
                  "type": "boolean"
                },
                {
                  "type": "object"
                }
              ]
            }
          },
          {
            "type": "object",
            "additionalProperties": {
              "type": "array",
              "items": {
                "$ref": "#/components/schemas/const_insight_metrics_property_examples_object"
              }
            }
          }
        ]
      },
      "intervals": {
        "type": "object",
        "additionalProperties": {
          "title": "const_insight_metrics_property_interval",
          "type": "object",
          "properties": {
            "interval": {
              "type": "integer",
              "contentEncoding": "int32"
            },
            "max_age": {
              "type": "integer",
              "contentEncoding": "int32"
            }
          }
        },
        "description": "Property key is the interval (e.g. 10m, 1h, ...)"
      },
      "keys": {
        "type": "object"
      },
      "params": {
        "type": "object",
        "additionalProperties": {
          "title": "const_insight_metrics_property_param",
          "type": "object",
          "properties": {
            "required": {
              "type": "boolean"
            }
          }
        },
        "description": "Property key is the parameter name"
      },
      "report_durations": {
        "type": "object",
        "additionalProperties": {
          "title": "const_insight_metrics_property_report_duration",
          "type": "object",
          "properties": {
            "duration": {
              "type": "integer",
              "contentEncoding": "int32"
            },
            "interval": {
              "type": "integer",
              "contentEncoding": "int32"
            }
          }
        },
        "description": "Property key is the duration (e.g. 1d, 1w, ...)"
      },
      "report_scopes": {
        "uniqueItems": true,
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": ""
      },
      "scopes": {
        "type": "array",
        "items": {
          "title": "const_insight_metrics_property_scope",
          "enum": [
            "ap",
            "client",
            "device",
            "gateway",
            "map",
            "msp",
            "mxcluster",
            "mxedge",
            "org",
            "otherdevice",
            "rssizone",
            "sdkclient",
            "site",
            "switch",
            "wlan",
            "zone"
          ],
          "type": "string",
          "description": "enum: `ap`, `client`, `device`, `gateway`, `map`, `msp`, `mxcluster`, `mxedge`, `org`, `otherdevice`, `rssizone`, `sdkclient`, `site`, `switch`, `wlan`, `zone`"
        },
        "description": ""
      },
      "sle_baselined": {
        "type": "boolean"
      },
      "sle_classifiers": {
        "uniqueItems": true,
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": ""
      },
      "type": {
        "type": "string"
      },
      "unit": {
        "type": "string"
      },
      "values": {
        "type": "object"
      }
    }
  },
  "description": "Property key is the metric name"
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

`mistapi.api.v1.constants.definitions.listInsightMetrics()`

## Usage Context

Returns the list of all available insight/SLE (Service Level Expectation) metric definitions, including metric names, descriptions, and applicable scopes (org, site, device). Use this to discover which metrics are available for performance monitoring and SLE dashboards.

## Gotchas

- Metric availability depends on the device type and license tier — some advanced metrics require Premium Analytics.
- Metric names must match exactly when querying SLE data; use the values from this endpoint.

## Related Endpoints

- [../orgs/GET_orgs_org_id_sle.md](../orgs/GET_orgs_org_id_insights_sites-sle.md) — Org-level SLE metrics
- [../sites/GET_sites_site_id_sle.md](../sites/GET_sites_site_id_sle_scope_scope_id_metrics.md) — Site-level SLE metrics

## MistHelper Notes

Not currently used by MistHelper as a direct constants lookup. Menu **57-62** (`OrgSLEExporter` and related) export SLE data whose metric types correspond to definitions here.
