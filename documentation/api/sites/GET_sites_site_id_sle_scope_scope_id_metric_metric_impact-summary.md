# getSiteSleImpactSummary

> getSiteSleImpactSummary

## HTTP

`GET /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/impact-summary`

## Description

Get impact summary counts optionally filtered by classifier and failure type
 
* Wireless SLE Fields: `wlan`, `device_type`, `device_os` ,`band`, `ap`, `server`, `mxedge`
* Wired SLE Fields: `switch`, `client`, `vlan`, `interface`, `chassis`
* WAN SLE Fields: `gateway`, `client`, `interface`, `chassis`, `peer_path`, `gateway_zones`

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
| fields | string | No |  |  |  |
| classifier | string | No |  |  |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "ap": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "sle_impact_summary_ap_item",
        "required": [
          "ap_mac",
          "degraded",
          "duration",
          "name",
          "total"
        ],
        "type": "object",
        "properties": {
          "ap_mac": {
            "minLength": 1,
            "type": "string"
          },
          "degraded": {
            "type": "number"
          },
          "duration": {
            "type": "number"
          },
          "name": {
            "minLength": 1,
            "type": "string"
          },
          "total": {
            "type": "number"
          }
        }
      },
      "description": ""
    },
    "band": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "sle_impact_summary_band_item",
        "required": [
          "band",
          "degraded",
          "duration",
          "name",
          "total"
        ],
        "type": "object",
        "properties": {
          "band": {
            "minLength": 1,
            "type": "string"
          },
          "degraded": {
            "type": "number"
          },
          "duration": {
            "type": "number"
          },
          "name": {
            "minLength": 1,
            "type": "string"
          },
          "total": {
            "type": "number"
          }
        }
      },
      "description": ""
    },
    "classifier": {
      "type": "string"
    },
    "device_os": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "sle_impact_summary_device_os_item",
        "required": [
          "degraded",
          "device_os",
          "duration",
          "name",
          "total"
        ],
        "type": "object",
        "properties": {
          "degraded": {
            "type": "number"
          },
          "device_os": {
            "type": "string"
          },
          "duration": {
            "type": "number"
          },
          "name": {
            "minLength": 1,
            "type": "string"
          },
          "total": {
            "type": "number"
          }
        }
      },
      "description": ""
    },
    "device_type": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "sle_impact_summary_device_type_item",
        "required": [
          "degraded",
          "device_type",
          "duration",
          "name",
          "total"
        ],
        "type": "object",
        "properties": {
          "degraded": {
            "type": "number"
          },
          "device_type": {
            "type": "string"
          },
          "duration": {
            "type": "number"
          },
          "name": {
            "minLength": 1,
            "type": "string"
          },
          "total": {
            "type": "number"
          }
        }
      },
      "description": ""
    },
    "end": {
      "type": "number"
    },
    "failure": {
      "type": "string"
    },
    "metric": {
      "minLength": 1,
      "type": "string"
    },
    "start": {
      "type": "number"
    },
    "wlan": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "sle_impact_summary_wlan_item",
        "required": [
          "degraded",
          "duration",
          "name",
          "total",
          "wlan_id"
        ],
        "type": "object",
        "properties": {
          "degraded": {
            "type": "number"
          },
          "duration": {
            "type": "number"
          },
          "name": {
            "minLength": 1,
            "type": "string"
          },
          "total": {
            "type": "number"
          },
          "wlan_id": {
            "minLength": 1,
            "type": "string"
          }
        }
      },
      "description": ""
    }
  },
  "required": [
    "ap",
    "band",
    "classifier",
    "device_os",
    "device_type",
    "end",
    "failure",
    "metric",
    "start",
    "wlan"
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

`mistapi.api.v1.sites.sles.getSiteSleImpactSummary()`

## Usage Context

Retrieves the impact summary for an SLE metric, showing how many users/devices are affected by failures.

## Gotchas

- Impact is calculated over the requested time range.

## Related Endpoints

- [GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-clients.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-clients.md) — Impacted clients
- [GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-aps.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_impacted-aps.md) — Impacted APs

## MistHelper Notes

Used by Menu **53** via SLE analysis workflow.
