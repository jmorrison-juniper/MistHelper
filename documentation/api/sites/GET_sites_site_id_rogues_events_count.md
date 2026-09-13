# countSiteRogueEvents

> countSiteRogueEvents

## HTTP

`GET /api/v1/sites/{site_id}/rogues/events/count`

## Description

Count by Distinct Attributes of Rogue Events

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
| distinct | string | No |  |  |  |
| type | string | No |  |  |  |
| ssid | string | No |  |  | SSID of the network detected as threat |
| bssid | string | No |  |  | BSSID of the network detected as threat |
| ap_mac | string | No |  |  | MAC of the device that had strongest signal strength for ssid/bssid pair |
| channel | string | No |  |  | Channel over which ap_mac heard ssid/bssid pair |
| seen_on_lan | boolean | No |  |  | Whether the reporting AP see a wireless client (on LAN) connecting to it |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| limit | integer | No | 100 |  |  |

## Request Body

None.

## Response

### 200

Result of Count

```json
{
  "type": "object",
  "properties": {
    "distinct": {
      "type": "string"
    },
    "end": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "count_result",
        "required": [
          "count"
        ],
        "type": "object",
        "properties": {
          "count": {
            "type": "integer",
            "contentEncoding": "int32"
          }
        },
        "additionalProperties": {
          "type": "string"
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "distinct",
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

`mistapi.api.v1.sites.rogues.countSiteRogueEvents()`

## Usage Context

Returns the count of rogue AP detection events at a site.

## Gotchas

- Count only; use the search endpoint for event details.

## Related Endpoints

- [GET_sites_site_id_rogues_events_search.md](GET_sites_site_id_rogues_events_search.md) — Search rogue events
- [GET_sites_site_id_insights_rogues.md](GET_sites_site_id_insights_rogues.md) — Rogue insights

## MistHelper Notes

Used by Menu **81** for rogue AP monitoring.
