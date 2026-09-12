# searchSiteDiscoveredSwitches

> searchSiteDiscoveredSwitches

## HTTP

`GET /api/v1/sites/{site_id}/stats/discovered_switches/search`

## Description

Search Discovered Switches

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
| adopted | boolean | No |  |  |  |
| system_name | string | No |  |  |  |
| hostname | string | No |  |  |  |
| vendor | string | No |  |  |  |
| model | string | No |  |  |  |
| version | string | No |  |  |  |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "number"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "next": {
      "type": "string"
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "discovered_switch",
        "type": "object",
        "properties": {
          "adopted": {
            "type": "boolean"
          },
          "ap_redundancy": {
            "title": "ap_redundancy",
            "type": "object",
            "properties": {
              "modules": {
                "type": "object",
                "additionalProperties": {
                  "title": "ap_redundancy_module",
                  "type": "object",
                  "properties": {
                    "num_aps": {
                      "type": "integer",
                      "contentEncoding": "int32",
                      "examples": [
                        15
                      ]
                    },
                    "num_aps_with_switch_redundancy": {
                      "type": "integer",
                      "contentEncoding": "int32",
                      "examples": [
                        8
                      ]
                    }
                  }
                },
                "description": "Property key is the node id"
              },
              "num_aps": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  15
                ]
              },
              "num_aps_with_switch_redundancy": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  8
                ]
              }
            }
          },
          "aps": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "title": "discovered_switch_ap",
              "type": "object",
              "properties": {
                "hostname": {
                  "type": "string"
                },
                "inactive_wired_vlans": {
                  "type": "array",
                  "items": {
                    "type": "integer",
                    "contentEncoding": "int32"
                  },
                  "description": ""
                },
                "mac": {
                  "type": "string"
                },
                "poe_status": {
                  "type": "boolean"
                },
                "port": {
                  "type": "string"
                },
                "port_id": {
                  "type": "string"
                },
                "power_draw": {
                  "type": "number"
                },
                "when": {
                  "type": "string"
                }
              }
            },
            "description": ""
          },
          "chassis_id": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          },
          "for_site": {
            "type": "boolean",
            "readOnly": true
          },
          "mgmt_addr": {
            "type": "string"
          },
          "model": {
            "type": "string"
          },
          "org_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "system_desc": {
            "type": "string"
          },
          "system_name": {
            "type": "string"
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "vendor": {
            "type": "string"
          },
          "version": {
            "type": "string"
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "number"
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "end",
    "limit",
    "results",
    "start",
    "total"
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.stats_-_discovered_switches.searchSiteDiscoveredSwitches()`

## Usage Context

Searches discovered (unmanaged) switches at a site with filtering capabilities. Used to find switches that can be claimed.

## Gotchas

- Discovered switches may disappear from results if the upstream AP that detected them goes offline.

## Related Endpoints

- [GET_sites_site_id_stats_discovered_switches_count.md](GET_sites_site_id_stats_discovered_switches_count.md) — Count discovered switches
- [GET_sites_site_id_stats_discovered_switches_metrics.md](GET_sites_site_id_stats_discovered_switches_metrics.md) — Metrics

## MistHelper Notes

Not currently used by MistHelper directly.
