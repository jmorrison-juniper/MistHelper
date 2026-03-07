# getOrgSle

> getOrgSle

## HTTP

`GET /api/v1/orgs/{org_id}/insights/{metric}`

## Description

Get Org SLEs (all/worst sites, Mx Edges, ...)

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| metric | string | Yes | See [List Insight Metrics]($e/Constants%20Definitions/listInsightMetrics) for available metrics |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| sle | string | No |  |  | See [List Insight Metrics]($e/Constants%20Definitions/listInsightMetrics) for more details |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| interval | string | No |  |  | Aggregation works by giving a time range plus interval (e.g. 1d, 1h, 10m) where aggregation function would be applied to. |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |

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
    "interval": {
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
        "anyOf": [
          {
            "type": "number"
          },
          {
            "type": "object"
          }
        ]
      },
      "description": "Results depends on the `metric` - some return numbers (e.g. bytes, ap-count), others return objects"
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "end",
    "interval",
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.sles.getOrgSle()`

## Usage Context

Retrieves available insight metrics for the organization.

## Gotchas

- Metrics include SLE scores, throughput, capacity, and more.

## Related Endpoints

- [GET_orgs_org_id_insights_sites-sle.md](GET_orgs_org_id_insights_sites-sle.md) — Sites SLE overview
- [GET_orgs_org_id_stats.md](GET_orgs_org_id_stats.md) — Org stats

## MistHelper Notes

Not currently used by MistHelper directly.
