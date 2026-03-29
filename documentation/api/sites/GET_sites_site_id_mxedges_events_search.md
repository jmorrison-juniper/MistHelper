# searchSiteMistEdgeEvents

> searchSiteMistEdgeEvents

## HTTP

`GET /api/v1/sites/{site_id}/mxedges/events/search`

## Description

Search Site Mist Edge Events

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
| mxedge_id | string | No |  |  | Mist edge id |
| mxcluster_id | string | No |  |  | Mist edge cluster id |
| type | string | No |  |  | See [List Device Events Definitions]($e/Constants%20Events/listDeviceEventsDefinitions) |
| service | string | No |  |  | Service running on mist edge(mxagent, tunterm etc) |
| component | string | No |  |  | Component like PS1, PS2 |
| limit | integer | No | 10 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1694708579
      ]
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        10
      ]
    },
    "next": {
      "type": "string"
    },
    "page": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        3
      ]
    },
    "results": {
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "mxedge_event",
        "type": "object",
        "properties": {
          "audit_id": {
            "type": "string",
            "description": "Unique ID of the object instance in the Mist Organization",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "53f10664-3ce8-4c27-b382-0ef66432349f"
            ]
          },
          "component": {
            "type": [
              "string",
              "null"
            ],
            "examples": [
              "PS1",
              "Fan1"
            ]
          },
          "device_id": {
            "type": [
              "string",
              "null"
            ],
            "description": "Device id",
            "contentEncoding": "uuid",
            "readOnly": true
          },
          "device_type": {
            "type": "string"
          },
          "from_version": {
            "type": "string"
          },
          "mac": {
            "type": "string"
          },
          "mxcluster_id": {
            "type": "string",
            "examples": [
              "2815c917-58e7-472f-a190-bfd44fb58d05"
            ]
          },
          "mxedge_id": {
            "type": "string",
            "examples": [
              "00000000-0000-0000-1000-020000dc585c"
            ]
          },
          "mxedge_name": {
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
          "package": {
            "type": "string"
          },
          "service": {
            "type": "string",
            "examples": [
              "tunterm"
            ]
          },
          "severity": {
            "title": "event_severity",
            "enum": [
              "normal",
              "critical",
              "high",
              "warning"
            ],
            "type": "string"
          },
          "sys_info.usage": {
            "title": "mxedge_event_sys_info",
            "type": "object",
            "properties": {
              "resource": {
                "type": "string"
              },
              "severity": {
                "title": "event_severity",
                "enum": [
                  "normal",
                  "critical",
                  "high",
                  "warning"
                ],
                "type": "string"
              }
            }
          },
          "text": {
            "type": "string"
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "to_version": {
            "type": "string"
          },
          "type": {
            "type": "string",
            "examples": [
              "ME_SERVICE_STOPPED"
            ]
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1694622179
      ]
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.mxedges.searchSiteMistEdgeEvents()`

## Usage Context

Searches Mist Edge events at a site (tunnel failures, reboots, config changes) with filtering by type and time.

## Gotchas

- Uses cursor-based pagination.

## Related Endpoints

- [GET_sites_site_id_mxedges_events_count.md](GET_sites_site_id_mxedges_events_count.md) — Count edge events
- [GET_sites_site_id_mxedges.md](GET_sites_site_id_mxedges.md) — List edges

## MistHelper Notes

Not currently used by MistHelper directly.
