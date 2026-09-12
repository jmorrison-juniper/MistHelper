# listSiteRogueAPs

> listSiteRogueAPs

## HTTP

`GET /api/v1/sites/{site_id}/insights/rogues`

## Description

Get List of Site Rogue/Neighbor APs

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
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| interval | string | No |  |  | Aggregation works by giving a time range plus interval (e.g. 1d, 1h, 10m) where aggregation function would be applied to. |

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
      "type": "string",
      "description": "Link to next set of results. If more results aren\u2019t present, next is null."
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "insight_rogue_ap",
        "required": [
          "ap_mac",
          "avg_rssi",
          "bssid",
          "channel",
          "num_aps"
        ],
        "type": "object",
        "properties": {
          "ap_mac": {
            "type": "string",
            "description": "MAC of the device that had strongest signal strength for ssid/bssid pair"
          },
          "avg_rssi": {
            "type": "number",
            "description": "Average signal strength of ap_mac for ssid/bssid pair"
          },
          "bssid": {
            "type": "string",
            "description": "BSSID of the network detected as threat"
          },
          "channel": {
            "type": "string",
            "description": "Channel over which ap_mac heard ssid/bssid pair"
          },
          "delta_x": {
            "type": "number",
            "description": "X position relative to the reporting AP (`ap_mac`)"
          },
          "delta_y": {
            "type": "number",
            "description": "Y position relative to the reporting AP (`ap_mac`)"
          },
          "num_aps": {
            "type": "integer",
            "description": "Num of aps that heard the ssid/bssid pair",
            "contentEncoding": "int32"
          },
          "seen_on_lan": {
            "type": "boolean",
            "description": "Whether the reporting AP see a wireless client (on LAN) connecting to it"
          },
          "ssid": {
            "type": "string",
            "description": "SSID of the network detected as threat"
          },
          "times_heard": {
            "type": "integer",
            "description": "Represents number of times the pair was heard in the interval. Each count roughly corresponds to a minute.",
            "contentEncoding": "int32"
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "end",
    "limit",
    "results",
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.rogues.listSiteRogueAPs()`

## Usage Context

Retrieves rogue AP insight data for a site, including detected unauthorized access points and their risk assessment.

## Gotchas

- Rogue detection depends on AP scanning. Results vary with scan radio availability.

## Related Endpoints

- [GET_sites_site_id_rogues_events_search.md](GET_sites_site_id_rogues_events_search.md) — Rogue events
- [GET_sites_site_id_rogues_rogue_bssid.md](GET_sites_site_id_rogues_rogue_bssid.md) — Specific rogue details

## MistHelper Notes

Used by Menu **81** for rogue AP data export.
