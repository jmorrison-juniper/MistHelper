# countSiteApps

> countSiteApps

## HTTP

`GET /api/v1/sites/{site_id}/stats/apps/count`

## Description

Count by Distinct Attributes of Applications

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
| distinct | string | No |  |  | Default for wireless devices is `ap`. Default for wired devices is `device_mac` |
| device_mac | string | No |  |  | MAC of the device |
| app | string | No |  |  | Application name |
| wired | string | No |  |  | If a device is wired or wireless. Default is False. |
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

`mistapi.api.v1.sites.stats_-_apps.countSiteApps()`

## Usage Context

Returns the count of application statistics entries at a site.

## Gotchas

- Application stats require DPI/application visibility to be enabled on the network.

## Related Endpoints

- [GET_sites_site_id_stats.md](GET_sites_site_id_stats.md) — Site stats overview
- [GET_sites_site_id_insights_client_client_mac.md](GET_sites_site_id_insights_client_client_mac_metric.md) — Per-client app insights

## MistHelper Notes

Not currently used by MistHelper directly.
