# searchSiteWirelessClientSessions

> searchSiteWirelessClientSessions

## HTTP

`GET /api/v1/sites/{site_id}/clients/sessions/search`

## Description

Search Client Sessions

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
| ap | string | No |  |  | AP MAC |
| band | string | No |  |  | 802.11 Band |
| client_family | string | No |  |  | E.g. "Mac", "iPhone", "Apple watch" |
| client_manufacture | string | No |  |  | E.g. "Apple" |
| client_model | string | No |  |  | E.g. "8+", "XS" |
| client_username | string | No |  |  | Username |
| client_os | string | No |  |  | E.g. "Mojave", "Windows 10", "Linux" |
| ssid | string | No |  |  | SSID |
| wlan_id | string | No |  |  | WLAN_id |
| psk_id | string | No |  |  | PSK ID |
| psk_name | string | No |  |  | PSK Name |
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
      "type": "array",
      "items": {
        "title": "response_client_sessions_search_item",
        "required": [
          "ap",
          "band",
          "client_manufacture",
          "connect",
          "disconnect",
          "duration",
          "mac",
          "org_id",
          "site_id",
          "ssid",
          "timestamp",
          "wlan_id"
        ],
        "type": "object",
        "properties": {
          "ap": {
            "type": "string",
            "readOnly": true
          },
          "band": {
            "type": "string",
            "readOnly": true
          },
          "client_manufacture": {
            "type": "string",
            "readOnly": true
          },
          "connect": {
            "type": "number",
            "readOnly": true
          },
          "disconnect": {
            "type": "number",
            "readOnly": true
          },
          "duration": {
            "type": "number",
            "readOnly": true
          },
          "mac": {
            "type": "string",
            "readOnly": true
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
          "ssid": {
            "type": "string",
            "readOnly": true
          },
          "tags": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "readOnly": true
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "wlan_id": {
            "type": "string",
            "contentEncoding": "uuid"
          }
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

`mistapi.api.v1.sites.clients_-_wireless.searchSiteWirelessClientSessions()`

## Usage Context

Searches wireless client sessions at a site with filtering by client MAC, SSID, AP, duration, and time range.

## Gotchas

- Sessions with long durations may span multiple API pages. Use cursor-based pagination.

## Related Endpoints

- [GET_sites_site_id_clients_sessions_count.md](GET_sites_site_id_clients_sessions_count.md) — Session count
- [GET_sites_site_id_clients_search.md](GET_sites_site_id_clients_search.md) — Search clients

## MistHelper Notes

Not currently used by MistHelper directly.
