# searchOrgWirelessClientEvents

> searchOrgWirelessClientEvents

## HTTP

`GET /api/v1/orgs/{org_id}/clients/events/search`

## Description

Get Org Clients Events

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| type | string | No |  |  | See [List Device Events Definitions]($e/Constants%20Events/listDeviceEventsDefinitions) |
| reason_code | integer | No |  |  | For assoc/disassoc events |
| ssid | string | No |  |  | SSID Name |
| ap | string | No |  |  | AP MAC |
| key_mgmt | string | No |  |  | Key Management Protocol, e.g. WPA2-PSK, WPA3-SAE, WPA2-Enterprise |
| proto | string | No |  |  | a / b / g / n / ac / ax |
| band | string | No |  |  | 802.11 Band |
| wlan_id | string | No |  |  | WLAN_id |
| nacrule_id | string | No |  |  | Nacrule_id |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| limit | integer | No | 100 |  |  |
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
        "title": "events_client",
        "required": [
          "band",
          "timestamp"
        ],
        "type": "object",
        "properties": {
          "ap": {
            "type": "string"
          },
          "band": {
            "type": "string",
            "description": "enum: `24`, `5`, `6`"
          },
          "bssid": {
            "type": "string"
          },
          "channel": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "key_mgmt": {
            "type": "string",
            "description": "Key management protocol used for the latest authentication. enum: `WPA2-PSK`, `WPA2-PSK-FT`, `WPA2-PSK-SHA256`, `WPA3-EAP-SHA256`, `WPA3-SAE-FT`, `WPA3-SAE-PSK`"
          },
          "proto": {
            "type": "string",
            "description": "enum: `a`, `ac`, `ax`, `b`, `be`, `g`, `n`"
          },
          "ssid": {
            "type": "string"
          },
          "text": {
            "type": "string"
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "type": {
            "type": "string",
            "description": "Event type, e.g. MARVIS_EVENT_CLIENT_FBT_FAILURE"
          },
          "type_code": {
            "type": "integer",
            "description": "For assoc/disassoc events",
            "contentEncoding": "int32"
          },
          "wlan_id": {
            "type": "string",
            "contentEncoding": "uuid"
          }
        },
        "description": "Client events"
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

`mistapi.api.v1.orgs.clients_-_wireless.searchOrgWirelessClientEvents()`

## Usage Context

Searches wireless client events across the organization with filtering.

## Gotchas

- Time range defaults to last hour if not specified.
- Large orgs may require filtering by site or client MAC.

## Related Endpoints

- [GET_orgs_org_id_clients_events_count.md](GET_orgs_org_id_clients_events_count.md) — Count events
- [GET_orgs_org_id_clients_search.md](GET_orgs_org_id_clients_search.md) — Search clients

## MistHelper Notes

Used by MistHelper via `searchOrgWirelessClientEvents` in Menu 69.
