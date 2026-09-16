# getSiteInsightMetricsForAP

> getSiteInsightMetricsForAP

## HTTP

`GET /api/v1/sites/{site_id}/insights/ap/{device_id}/stats`

## Description

Get AP Insight Metrics

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| metrics | string | Yes |  |  | Comma separated Metric names, e.g. `num_clients,num_stressed_clients`. See possible values at [List Insight Metrics](/#operations/listInsightMetrics) |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Time-series insight metric response for a device",
  "properties": {
    "end": {
      "description": "Epoch timestamp for the end of the metric query window",
      "type": "integer"
    },
    "interval": {
      "description": "Aggregation interval in seconds for each metric sample",
      "type": "integer"
    },
    "limit": {
      "description": "Maximum number of metric samples returned in this page",
      "type": "integer"
    },
    "page": {
      "description": "Returned page number for paginated metric samples",
      "type": "integer"
    },
    "results": {
      "description": "Device metric result values aligned with the response timestamps",
      "items": {
        "description": "Device metric result value, returned as a string or integer",
        "oneOf": [
          {
            "type": "string"
          },
          {
            "type": "integer"
          }
        ]
      },
      "type": "array"
    },
    "rt": {
      "description": "Unique string values returned or accepted by this schema",
      "items": {
        "type": "string"
      },
      "type": "array",
      "uniqueItems": true
    },
    "start": {
      "description": "Epoch timestamp for the start of the metric query window",
      "type": "integer"
    }
  },
  "required": [
    "end",
    "interval",
    "results",
    "start"
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

`mistapi.api.v1.sites.insights.getSiteInsightMetricsForAP()`

## Usage Context

Use this endpoint to read the resource at
`/api/v1/sites/{site_id}/insights/ap/{device_id}/stats`.
Common use cases:

- Use it when you need to get AP Insight Metrics.
- Use it in an audit or status workflow before you make a related change.
- Treat this endpoint as a read-only request.
- The installed `mistapi` 0.64.0 signature is `getSiteInsightMetricsForAP(mist_session: mistapi.__api_session.APISession, site_id: str, device_id: str, metrics: str, start: str | None = None, end: str | None = None, duration: str | None = None, interval: str | None = None, limit: int | None = None, page: int | None = None) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `site_id`, `device_id`. Use identifiers from a trusted Mist read.
- Query parameters include `metrics`, `start`, `end`, `duration`, `interval`. Keep filters narrow for repeatable results.

## Related Endpoints

- [GET_sites_site_id_insights_fingerprints_count.md](../orgs/GET_sites_site_id_insights_fingerprints_count.md) -- countOrgClientFingerprints uses `GET /api/v1/sites/{site_id}/insights/fingerprints/count`.
- [GET_sites_site_id_insights_fingerprints_search.md](../orgs/GET_sites_site_id_insights_fingerprints_search.md) -- searchOrgClientFingerprints uses `GET /api/v1/sites/{site_id}/insights/fingerprints/search`.
- [GET_sites_site_id_insights.md](GET_sites_site_id_insights.md) -- getSiteInsightMetrics uses `GET /api/v1/sites/{site_id}/insights`.

## MistHelper Notes

MistHelper does not currently call `getSiteInsightMetricsForAP`.
Verification source: `git grep -n "getSiteInsightMetricsForAP" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
