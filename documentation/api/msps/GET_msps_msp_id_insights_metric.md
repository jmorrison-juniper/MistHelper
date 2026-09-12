# getMspSle

> getMspSle

## HTTP

`GET /api/v1/msps/{msp_id}/insights/{metric}`

## Description

Get MSP SLEs (all/worst Orgs ...)

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |
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

`mistapi.api.v1.msps.sles.getMspSle()`

## Usage Context

Retrieves SLE (Service Level Expectation) metrics at the MSP level, providing aggregated performance insights across all managed organizations. Use this for cross-org performance comparisons and MSP-wide health monitoring.

## Gotchas

- The `metric` path parameter specifies which SLE metric to retrieve (e.g., `wifi-connectivity`, `wan-link-health`).
- Not all metrics are available at MSP scope; some are site-level or device-level only.

## Related Endpoints

- [GET_msps_msp_id_stats_orgs.md](GET_msps_msp_id_stats_orgs.md) — Org operational statistics
- [../constants/GET_const_insight_metrics.md](../constants/GET_const_insight_metrics.md) — Available metric definitions
- [../orgs/GET_orgs_org_id_sle.md](../orgs/GET_orgs_org_id_insights_sites-sle.md) — Org-level SLE data

## MistHelper Notes

Not currently used by MistHelper directly. Menu **57-62** (`OrgSLEExporter` and related) export SLE data at the org level.
