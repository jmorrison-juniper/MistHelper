# searchSiteRogueEvents

> searchSiteRogueEvents

## HTTP

`GET /api/v1/sites/{site_id}/rogues/events/search`

## Description

Search Rogue Events

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
| ssid | string | No |  |  | SSID of the network detected as threat |
| bssid | string | No |  |  | BSSID of the network detected as threat |
| ap_mac | string | No |  |  | MAC of the device that had strongest signal strength for ssid/bssid pair |
| channel | integer | No |  |  | Channel over which ap_mac heard ssid/bssid pair |
| seen_on_lan | boolean | No |  |  | Whether the reporting AP see a wireless client (on LAN) connecting to it |
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
      "type": "integer",
      "contentEncoding": "int32"
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
        "title": "events_rogue",
        "required": [
          "ap",
          "bssid",
          "channel",
          "rssi",
          "ssid",
          "timestamp"
        ],
        "type": "object",
        "properties": {
          "ap": {
            "type": "string"
          },
          "bssid": {
            "type": "string"
          },
          "channel": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "rssi": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "ssid": {
            "type": "string"
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          }
        },
        "description": "Rogue events"
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

`mistapi.api.v1.sites.rogues.searchSiteRogueEvents()`

## Usage Context

Searches rogue AP events at a site. Returns detection details including BSSID, RSSI, channel, and detecting APs.

## Gotchas

- Uses cursor-based pagination. High-density environments may generate many rogue detections.

## Related Endpoints

- [GET_sites_site_id_rogues_events_count.md](GET_sites_site_id_rogues_events_count.md) — Count events
- [GET_sites_site_id_rogues_rogue_bssid.md](GET_sites_site_id_rogues_rogue_bssid.md) — Specific rogue details

## MistHelper Notes

Used by Menu **81** for rogue AP data export.
