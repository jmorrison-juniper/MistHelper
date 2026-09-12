# getSiteEventsForClient

> getSiteEventsForClient

## HTTP

`GET /api/v1/sites/{site_id}/clients/{client_mac}/events`

## Description

Get the list of events for a specific client

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| client_mac | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| type | string | No |  |  | E.g. MARVIS_EVENT_CLIENT_DHCP_STUCK |
| proto | string | No |  |  | a / b / g / n / ac / ax |
| band | string | No |  |  | 802.11 Band |
| channel | string | No |  |  |  |
| wlan_id | string | No |  |  |  |
| ssid | string | No |  |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

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

`mistapi.api.v1.sites.clients_-_wireless.getSiteEventsForClient()`

## Usage Context

Retrieves events for a specific wireless client identified by MAC address at a site.

## Gotchas

- MAC address must be in colon-separated format.

## Related Endpoints

- [GET_sites_site_id_stats_clients.md](GET_sites_site_id_stats_clients.md) — Client stats
- [GET_sites_site_id_stats_clients_client_mac.md](GET_sites_site_id_stats_clients_client_mac.md) — Client details

## MistHelper Notes

Not currently used by MistHelper directly.
