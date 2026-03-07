# searchSiteDiscoveredSwitchesMetrics

> searchSiteDiscoveredSwitchesMetrics

## HTTP

`GET /api/v1/sites/{site_id}/stats/discovered_switch_metrics/search`

## Description

Search Discovered Switch Metrics

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
| scope | string | No |  |  | Metric scope |
| type | string | No |  |  | Metric type |
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
      "type": "array",
      "items": {
        "title": "discovered_switch_metric",
        "type": "object",
        "properties": {
          "adopted": {
            "type": "boolean"
          },
          "aps": {
            "type": "array",
            "items": {
              "title": "discovered_switch_metric_ap",
              "type": "object",
              "properties": {
                "hostname": {
                  "type": "string"
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
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "when": {
                  "type": "string"
                }
              }
            },
            "description": ""
          },
          "chassis_id": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          },
          "hostname": {
            "type": "string",
            "examples": [
              "SW-HLAB-ea2e00"
            ]
          },
          "mgmt_addr": {
            "type": "string",
            "examples": [
              "10.10.20.42"
            ]
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
          "scope": {
            "type": "string",
            "examples": [
              "site"
            ]
          },
          "score": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              100
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
            "type": "string",
            "examples": [
              "Juniper Networks, Inc. ex4100-f-12p Ethernet Switch, kernel JUNOS 22.4R3.25, Build date: 2024-02-10 00:49:09 UTC Copyright (c) 1996-2024 Juniper Networks, Inc."
            ]
          },
          "system_name": {
            "type": "string",
            "examples": [
              "SW-HLAB-ea2e00"
            ]
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "type": {
            "type": "string",
            "examples": [
              "inactive_wired_vlans"
            ]
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

`mistapi.api.v1.sites.stats_-_discovered_switches.searchSiteDiscoveredSwitchesMetrics()`

## Usage Context

Searches metrics for discovered (unmanaged) switches at a site. Useful for identifying devices to onboard.

## Gotchas

- Discovered switches are detected via LLDP/CDP but not yet claimed to Mist.

## Related Endpoints

- [GET_sites_site_id_stats_discovered_switches_search.md](GET_sites_site_id_stats_discovered_switches_search.md) — Search discovered switches
- [GET_sites_site_id_stats_discovered_switches_count.md](GET_sites_site_id_stats_discovered_switches_count.md) — Count discovered switches

## MistHelper Notes

Not currently used by MistHelper directly.
