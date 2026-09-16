# countOrgMarvisClientEvents

> countOrgMarvisClientEvents

## HTTP

`GET /api/v1/orgs/{org_id}/marvisclients/events/count`

## Description

Count Marvis Client events by a distinct field.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| distinct | string | No | type |  | Field to count by. enum: `type`, `device_id`, `wifi_mac`, `wifi_ip`, `hostname`, `ssid`, `bssid`, `channel`, `pre_bssid`, `pre_channel` |
| type | string | No |  |  | Filter by event type |
| device_id | string | No |  |  | Filter by Marvis Client installation device UUID |
| wifi_mac | string | No |  |  | Filter by device Wi-Fi MAC address |
| wifi_ip | string | No |  |  | Filter by device Wi-Fi IP address |
| hostname | string | No |  |  | Filter by device hostname |
| ssid | string | No |  |  | Filter by SSID involved in roam events |
| bssid | string | No |  |  | Filter by BSSID the client roamed to |
| channel | string | No |  |  | Filter by channel the client roamed to |
| pre_bssid | string | No |  |  | Filter by BSSID the client roamed from |
| pre_channel | string | No |  |  | Filter by channel the client roamed from |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |

## Request Body

None.

## Response

### 200

Count result

```json
{
  "additionalProperties": false,
  "description": "Distinct count response for time-bounded search results",
  "properties": {
    "distinct": {
      "description": "Field used to group the count results",
      "type": "string"
    },
    "end": {
      "description": "Search window end timestamp for the count request, in epoch seconds",
      "type": "integer"
    },
    "limit": {
      "description": "Maximum number of distinct count results requested",
      "type": "integer"
    },
    "results": {
      "description": "List of count result rows",
      "items": {
        "additionalProperties": {
          "type": "string"
        },
        "description": "Count result row with the matching distinct field values",
        "properties": {
          "count": {
            "description": "Number of matching items for the distinct value or values in this result",
            "type": "integer"
          }
        },
        "required": [
          "count"
        ],
        "type": "object"
      },
      "type": "array",
      "uniqueItems": true
    },
    "start": {
      "description": "Search window start timestamp for the count request, in epoch seconds",
      "type": "integer"
    },
    "total": {
      "description": "Number of distinct result buckets returned",
      "type": "integer"
    }
  },
  "required": [
    "distinct",
    "end",
    "limit",
    "results",
    "start",
    "total"
  ],
  "type": "object"
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

`mistapi.api.v1.orgs.clients_-_marvis.countOrgMarvisClientEvents()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
