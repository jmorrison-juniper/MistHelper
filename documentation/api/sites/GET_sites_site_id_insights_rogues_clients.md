# listSiteRogueClients

> listSiteRogueClients

## HTTP

`GET /api/v1/sites/{site_id}/insights/rogues/clients`

## Description

Get List of Site Rogue Clients

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
      "type": "string"
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "insight_rogue_client",
        "required": [
          "annotation",
          "ap_mac",
          "avg_rssi",
          "band",
          "bssid",
          "client_mac",
          "num_aps"
        ],
        "type": "object",
        "properties": {
          "annotation": {
            "type": "string"
          },
          "ap_mac": {
            "type": "string"
          },
          "avg_rssi": {
            "type": "number"
          },
          "band": {
            "type": "string"
          },
          "bssid": {
            "type": "string"
          },
          "client_mac": {
            "type": "string"
          },
          "num_aps": {
            "type": "integer",
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

`mistapi.api.v1.sites.rogues.listSiteRogueClients()`

## Usage Context

Retrieves a list of rogue clients detected at a site. Rogue clients are devices associated with unauthorized APs.

## Gotchas

- Results may be delayed. Rogue detection relies on periodic scanning.

## Related Endpoints

- [GET_sites_site_id_insights_rogues.md](GET_sites_site_id_insights_rogues.md) — Rogue APs
- [GET_sites_site_id_devices.md](GET_sites_site_id_devices.md) — Site devices

## MistHelper Notes

Not currently used by MistHelper directly.
