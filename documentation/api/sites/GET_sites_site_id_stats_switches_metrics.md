# getSiteSwitchesMetrics

> getSiteSwitchesMetrics

## HTTP

`GET /api/v1/sites/{site_id}/stats/switches/metrics`

## Description

Get version compliance metrics for managed or monitored switches

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| type | string | No |  |  |  |
| scope | string | No |  |  |  |
| switch_mac | string | No |  |  | Switch mac, used only with metric `type`==`active_ports_summary` |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "active_ports_summary": {
      "title": "response_switch_metrics_active_ports_summary",
      "type": "object",
      "properties": {
        "details": {
          "title": "switch_metrics_active_ports_summary_details",
          "type": "object",
          "properties": {
            "active_port_count": {
              "type": "integer",
              "contentEncoding": "int32"
            },
            "total_port_count": {
              "type": "integer",
              "contentEncoding": "int32"
            }
          }
        },
        "score": {
          "type": "integer",
          "contentEncoding": "int32"
        },
        "total_switch_count": {
          "type": "integer",
          "contentEncoding": "int32"
        }
      }
    },
    "config_success": {
      "title": "response_switch_metrics_config_success",
      "type": "object",
      "properties": {
        "details": {
          "title": "response_switch_metrics_config_success_details",
          "type": "object",
          "properties": {
            "config_success_count": {
              "type": "integer",
              "contentEncoding": "int32"
            }
          }
        },
        "score": {
          "type": "integer",
          "contentEncoding": "int32"
        },
        "total_switch_count": {
          "type": "integer",
          "contentEncoding": "int32"
        }
      }
    },
    "version_compliance": {
      "title": "response_switch_metrics_version_compliance",
      "type": "object",
      "properties": {
        "details": {
          "title": "response_switch_metrics_version_compliance_details",
          "type": "object",
          "properties": {
            "major_versions": {
              "type": "array",
              "items": {
                "title": "switch_metrics_compliance_major_version",
                "type": "object",
                "properties": {
                  "major_count": {
                    "type": "integer",
                    "contentEncoding": "int32"
                  },
                  "major_version": {
                    "type": "string"
                  },
                  "model": {
                    "type": "string"
                  },
                  "system_names": {
                    "uniqueItems": true,
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": ""
                  }
                }
              },
              "description": ""
            }
          }
        },
        "score": {
          "type": "integer",
          "contentEncoding": "int32"
        },
        "total_switch_count": {
          "type": "integer",
          "contentEncoding": "int32"
        }
      }
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

`mistapi.api.v1.sites.stats_-_devices.getSiteSwitchesMetrics()`

## Usage Context

Retrieves aggregated switch metrics for a site, including port utilization, PoE usage, and error summaries.

## Gotchas

- Metrics are aggregated across all managed switches at the site.

## Related Endpoints

- [GET_sites_site_id_stats_devices.md](GET_sites_site_id_stats_devices.md) — Device stats
- [GET_sites_site_id_stats_ports_search.md](GET_sites_site_id_stats_ports_search.md) — Port stats

## MistHelper Notes

Not currently used by MistHelper directly.
