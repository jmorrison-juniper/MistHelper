# countSiteAlarms

> countSiteAlarms

## HTTP

`GET /api/v1/sites/{site_id}/alarms/count`

## Description

Count by Distinct Attributes of Site Alarms

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
| distinct | string | No |  |  | Group by and count the alarms by some distinct field |
| ack_admin_name | string | No |  |  | Name of the admins who have acked the alarms; accepts multiple values separated by comma |
| acked | boolean | No |  |  |  |
| type | string | No |  |  | Key-name of the alarms; accepts multiple values separated by comma |
| severity | string | No |  |  | Alarm severity; accepts multiple values separated by comma |
| group | string | No |  |  | Alarm group name; accepts multiple values separated by comma |
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

`mistapi.api.v1.sites.alarms.countSiteAlarms()`

## Usage Context

Returns the count of alarms at a site, optionally filtered by severity, type, or time range. Useful for dashboard summaries.

## Gotchas

- Count includes both acknowledged and unacknowledged alarms unless filtered.

## Related Endpoints

- [GET_sites_site_id_alarms_search.md](GET_sites_site_id_alarms_search.md) — Search alarms with details
- [POST_sites_site_id_alarms_ack.md](POST_sites_site_id_alarms_ack.md) — Acknowledge alarms

## MistHelper Notes

Not currently used by MistHelper directly. Menu **56** uses `searchOrgAlarms` at org level.
