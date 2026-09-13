# listSiteRoamingEvents

> listSiteRoamingEvents

## HTTP

`GET /api/v1/sites/{site_id}/events/fast_roam`

## Description

List Roaming Events data

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
| type | string | No |  |  | Event type |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |

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
      "description": "Link to query next set of results. value is null if no next page exists."
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "event_fastroam",
        "required": [
          "ap_mac",
          "client_mac",
          "fromap",
          "latency",
          "ssid",
          "timestamp"
        ],
        "type": "object",
        "properties": {
          "ap_mac": {
            "type": "string"
          },
          "client_mac": {
            "type": "string"
          },
          "fromap": {
            "type": "string"
          },
          "latency": {
            "type": "number"
          },
          "ssid": {
            "type": "string"
          },
          "subtype": {
            "type": "string"
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "type": {
            "type": "string",
            "description": "enum: `fail`, `none`, `pingpong`, `poor`, `slow`, `success`"
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

`mistapi.api.v1.sites.events.listSiteRoamingEvents()`

## Usage Context

Retrieves fast roaming (802.11r/OKC) events at a site. Shows successful and failed roam attempts between APs.

## Gotchas

- Fast roaming must be enabled on the WLAN. Events only appear for 802.11r/OKC-capable clients.

## Related Endpoints

- [GET_sites_site_id_clients_events_search.md](GET_sites_site_id_clients_events_search.md) — All client events
- [GET_sites_site_id_clients_sessions_search.md](GET_sites_site_id_clients_sessions_search.md) — Client sessions

## MistHelper Notes

Not currently used by MistHelper directly.
