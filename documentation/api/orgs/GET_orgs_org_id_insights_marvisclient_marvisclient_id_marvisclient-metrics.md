# getOrgMarvisClientInsights

> getOrgMarvisClientInsights

## HTTP

`GET /api/v1/orgs/{org_id}/insights/marvisclient/{marvisclient_id}/marvisclient-metrics`

## Description

Return time-series metrics for a specific Marvis Client device. For the full list of supported metric field names and example values, refer to [List Insight Metrics](/#operations/listInsightMetrics) under `/api/v1/const/insight_metrics`.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
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

Marvis Client time-series metrics

```json
{
  "additionalProperties": false,
  "description": "Time-series performance metrics for a Marvis Client device",
  "properties": {
    "avg_battery": {
      "description": "Average battery level per interval bucket",
      "items": {
        "type": "number"
      },
      "type": "array"
    },
    "avg_cellular_rssi": {
      "description": "Average cellular RSSI per interval bucket, in dBm",
      "items": {
        "type": "number"
      },
      "type": "array"
    },
    "avg_cpu": {
      "description": "Average CPU utilization per interval bucket (0\u2013100)",
      "items": {
        "type": "number"
      },
      "type": "array"
    },
    "avg_memory": {
      "description": "Average memory utilization per interval bucket (0\u2013100)",
      "items": {
        "type": "number"
      },
      "type": "array"
    },
    "avg_wifi_rssi": {
      "description": "Average Wi-Fi RSSI per interval bucket, in dBm",
      "items": {
        "type": "number"
      },
      "type": "array"
    },
    "end": {
      "description": "End of the reporting window, in epoch seconds",
      "type": "integer"
    },
    "interval": {
      "description": "Duration of each interval bucket, in seconds",
      "type": "integer"
    },
    "limit": {
      "description": "Maximum number of results requested",
      "type": "integer"
    },
    "page": {
      "description": "Current page number",
      "type": "integer"
    },
    "rt": {
      "description": "List of ISO 8601 timestamp strings for each interval bucket",
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "start": {
      "description": "Start of the reporting window, in epoch seconds",
      "type": "integer"
    }
  },
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

`mistapi.api.v1.orgs.insights.getOrgMarvisClientInsights()`

## Usage Context

Use this endpoint to read the resource at
`/api/v1/orgs/{org_id}/insights/marvisclient/{marvisclient_id}/marvisclient-metrics`.
Common use cases:

- Use it when you need to return time-series metrics for a specific Marvis Client device.
- Use it in an audit or status workflow before you make a related change.
- Treat this endpoint as a read-only request.
- The installed `mistapi` 0.64.0 signature is `getOrgMarvisClientInsights(mist_session: mistapi.__api_session.APISession, org_id: str, marvisclient_id: str, duration: str | None = None, interval: str | None = None, start: str | None = None, end: str | None = None, limit: int | None = None, page: int | None = None) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `org_id`, `marvisclient_id`. Use identifiers from a trusted Mist read.
- Query parameters include `duration`, `interval`, `start`, `end`, `limit`. Keep filters narrow for repeatable results.

## Related Endpoints

- [GET_orgs_org_id_insights_metric.md](GET_orgs_org_id_insights_metric.md) -- getOrgSle uses `GET /api/v1/orgs/{org_id}/insights/{metric}`.
- [GET_orgs_org_id_insights_sites-sle.md](GET_orgs_org_id_insights_sites-sle.md) -- getOrgSitesSle uses `GET /api/v1/orgs/{org_id}/insights/sites-sle`.
- [DELETE_orgs_org_id.md](DELETE_orgs_org_id.md) -- deleteOrg uses `DELETE /api/v1/orgs/{org_id}`.

## MistHelper Notes

MistHelper does not currently call `getOrgMarvisClientInsights`.
Verification source: `git grep -n "getOrgMarvisClientInsights" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
