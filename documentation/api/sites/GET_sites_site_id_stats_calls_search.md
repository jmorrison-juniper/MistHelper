# searchSiteCalls

> searchSiteCalls

## HTTP

`GET /api/v1/sites/{site_id}/stats/calls/search`

## Description

Search Calls

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
| mac | string | No |  |  | Device identifier |
| app | string | No |  |  | Third party app name |
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

Example response

```json
{
  "title": "response_stats_calls",
  "type": "object",
  "properties": {
    "end": {
      "type": "number"
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
        "title": "stats_call",
        "type": "object",
        "properties": {
          "app": {
            "type": "string"
          },
          "audio_quality": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "end_time": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "mac": {
            "type": "string"
          },
          "meeting_id": {
            "type": "string"
          },
          "org_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "rating": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "screen_share_quality": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "start_time": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "video_quality": {
            "type": "integer",
            "contentEncoding": "int32"
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "number"
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
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

`mistapi.api.v1.sites.stats_-_calls.searchSiteCalls()`

## Usage Context

Searches call statistics at a site. Returns individual call records with quality metrics (MOS, jitter, packet loss).

## Gotchas

- Call quality metrics use MOS (Mean Opinion Score) scale of 1-5.

## Related Endpoints

- [GET_sites_site_id_stats_calls_count.md](GET_sites_site_id_stats_calls_count.md) — Count calls
- [GET_sites_site_id_stats_calls_troubleshoot.md](GET_sites_site_id_stats_calls_troubleshoot.md) — Troubleshoot calls

## MistHelper Notes

Not currently used by MistHelper directly.
