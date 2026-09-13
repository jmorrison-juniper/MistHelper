# searchSiteZoneSessions

> searchSiteZoneSessions

## HTTP

`GET /api/v1/sites/{site_id}/{zone_type}/visits/search`

## Description

Search Zone Sessions

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| zone_type | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| user_type | string | No |  |  | User type, client (default) / sdkclient / asset |
| user | string | No |  |  | Client MAC / Asset MAC / SDK UUID |
| scope_id | string | No |  |  | If `scope`==`map`/`zone`/`rssizone`, the scope id |
| scope | string | No |  |  | Scope |
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

Result of Search Zone Sessions

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "number",
      "examples": [
        1541705289.769911
      ]
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1
      ]
    },
    "next": {
      "type": "string",
      "examples": [
        "/api/v1/sites/67970e46-4e12-11e6-9188-0242ac110007/zones/visits/search?limit=2&end=1541705247.000&scope_id=85fbba9e-4e12-11e6-9188-0242ac110007&user_type=asset&start=1541618889.77"
      ]
    },
    "results": {
      "type": "array",
      "items": {
        "title": "response_zone_search_item",
        "type": "object",
        "properties": {
          "enter": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              1541705254
            ]
          },
          "scope": {
            "type": "string",
            "examples": [
              "map"
            ]
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "user": {
            "type": "string",
            "examples": [
              "c4b301c81166"
            ]
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "number",
      "examples": [
        1541618889.769886
      ]
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        5892
      ]
    }
  }
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

`mistapi.api.v1.sites.zones.searchSiteZoneSessions()`

## Usage Context

Searches zone visit records by zone type. Returns entry/exit times, dwell duration, and visitor counts.

## Gotchas

- Uses cursor-based pagination. Zone visits data accumulates quickly for busy zones.

## Related Endpoints

- [GET_sites_site_id_zone_type_count.md](GET_sites_site_id_zone_type_count.md) — Zone visit count
- [GET_sites_site_id_stats_zones.md](GET_sites_site_id_stats_zones.md) — Zone stats

## MistHelper Notes

Not currently used by MistHelper directly.
