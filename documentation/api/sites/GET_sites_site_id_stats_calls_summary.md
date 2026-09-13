# getSiteCallsSummary

> getSiteCallsSummary

## HTTP

`GET /api/v1/sites/{site_id}/stats/calls/summary`

## Description

Summarized, aggregated stats for the site calls

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
| ap_mac | string | No |  |  | AP MAC, optional |
| app | string | No |  |  | APp name (`zoom` or `teams`). default is both. Optional |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "bad_minutes": {
      "type": "number",
      "examples": [
        5566
      ]
    },
    "bad_minutes_client": {
      "type": "number",
      "examples": [
        526
      ]
    },
    "bad_minutes_site_wan": {
      "type": "number",
      "examples": [
        3612
      ]
    },
    "bad_minutes_wireless": {
      "type": "number",
      "examples": [
        1428
      ]
    },
    "num_aps": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1
      ]
    },
    "num_users": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        3
      ]
    },
    "total_minutes": {
      "type": "number",
      "examples": [
        5566
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.stats_-_calls.getSiteCallsSummary()`

## Usage Context

Retrieves a summary of call statistics at a site, including total calls, average MOS score, and quality distribution.

## Gotchas

- Summary aggregates all call types (SIP, Teams, Zoom, etc.) unless filtered.

## Related Endpoints

- [GET_sites_site_id_stats_calls_search.md](GET_sites_site_id_stats_calls_search.md) — Search individual calls
- [GET_sites_site_id_stats_calls_troubleshoot.md](GET_sites_site_id_stats_calls_troubleshoot.md) — Troubleshoot calls

## MistHelper Notes

Not currently used by MistHelper directly.
