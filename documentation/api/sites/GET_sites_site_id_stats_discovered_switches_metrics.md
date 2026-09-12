# listSiteDiscoveredSwitchesMetrics

> listSiteDiscoveredSwitchesMetrics

## HTTP

`GET /api/v1/sites/{site_id}/stats/discovered_switches/metrics`

## Description

Discovered switches related metrics, lists related switch system names & details if not compliant

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
| threshold | string | No |  |  | Configurable # ap per switch threshold, default 12 |
| system_name | string | No |  |  | System name for switch level metrics, optional |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "inactive_wired_vlans": {
      "title": "dswitches_metrics_inactive_wired_vlans",
      "required": [
        "details",
        "score"
      ],
      "type": "object",
      "properties": {
        "details": {
          "type": "object"
        },
        "score": {
          "type": "number"
        }
      }
    },
    "poe_compliance": {
      "title": "dswitches_metrics_poe_compliance",
      "required": [
        "details",
        "score"
      ],
      "type": "object",
      "properties": {
        "details": {
          "title": "dswitches_metrics_poe_compliance_details",
          "required": [
            "total_aps",
            "total_power"
          ],
          "type": "object",
          "properties": {
            "total_aps": {
              "type": "integer",
              "contentEncoding": "int32"
            },
            "total_power": {
              "type": "number"
            }
          }
        },
        "score": {
          "type": "number"
        }
      }
    },
    "switch_ap_affinity": {
      "title": "dswitches_metrics_switch_ap_affinity",
      "required": [
        "details",
        "score"
      ],
      "type": "object",
      "properties": {
        "details": {
          "title": "dswitches_metrics_switch_ap_affinity_details",
          "required": [
            "system_name",
            "threshold"
          ],
          "type": "object",
          "properties": {
            "system_name": {
              "uniqueItems": true,
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": ""
            },
            "threshold": {
              "type": "number"
            }
          }
        },
        "score": {
          "type": "number"
        }
      }
    },
    "version_compliance": {
      "title": "dswitches_metrics_version_compliance",
      "required": [
        "details",
        "score"
      ],
      "type": "object",
      "properties": {
        "details": {
          "title": "dswitches_metrics_version_compliance_details",
          "required": [
            "major_versions",
            "total_switch_count"
          ],
          "type": "object",
          "properties": {
            "major_versions": {
              "uniqueItems": true,
              "type": "array",
              "items": {
                "title": "dswitches_compliance_major_version",
                "required": [
                  "major_count",
                  "model"
                ],
                "type": "object",
                "properties": {
                  "major_count": {
                    "type": "number"
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
            },
            "total_switch_count": {
              "type": "integer",
              "contentEncoding": "int32"
            }
          }
        },
        "score": {
          "type": "number"
        }
      }
    }
  },
  "required": [
    "inactive_wired_vlans",
    "poe_compliance",
    "switch_ap_affinity",
    "version_compliance"
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

`mistapi.api.v1.sites.stats_-_discovered_switches.listSiteDiscoveredSwitchesMetrics()`

## Usage Context

Retrieves aggregated metrics for discovered switches at a site, including port counts and switch models detected.

## Gotchas

- Metrics are based on LLDP/CDP data and may not include all switch properties.

## Related Endpoints

- [GET_sites_site_id_stats_discovered_switches_search.md](GET_sites_site_id_stats_discovered_switches_search.md) — Search discovered switches
- [GET_sites_site_id_stats_discovered_switch_metrics_search.md](GET_sites_site_id_stats_discovered_switch_metrics_search.md) — Search metrics

## MistHelper Notes

Not currently used by MistHelper directly.
