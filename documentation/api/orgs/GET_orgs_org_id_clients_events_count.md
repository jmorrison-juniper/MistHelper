# countOrgWirelessClientEvents

> countOrgWirelessClientEvents

## HTTP

`GET /api/v1/orgs/{org_id}/clients/events/count`

## Description

Count by Distinct Attributes of Client-Events

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
| distinct | string | No |  |  |  |
| type | string | No |  |  | See [List Device Events Definitions]($e/Constants%20Events/listDeviceEventsDefinitions) |
| reason_code | integer | No |  |  | For assoc/disassoc events |
| ssid | string | No |  |  | SSID Name |
| ap | string | No |  |  | AP MAC |
| proto | string | No |  |  | a / b / g / n / ac / ax |
| band | string | No |  |  | 802.11 Band |
| wlan_id | string | No |  |  | WLAN ID |
| site_id | string | No |  |  | Site ID |
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

`mistapi.api.v1.orgs.clients_-_wireless.countOrgWirelessClientEvents()`

## Usage Context

Returns the count of wireless client events for the organization.

## Gotchas

- Use `distinct` parameter to group by event type.

## Related Endpoints

- [GET_orgs_org_id_clients_events_search.md](GET_orgs_org_id_clients_events_search.md) — Search events
- [GET_orgs_org_id_clients_count.md](GET_orgs_org_id_clients_count.md) — Client counts

## MistHelper Notes

Used by MistHelper via `searchOrgWirelessClientEvents` in Menu 69.
