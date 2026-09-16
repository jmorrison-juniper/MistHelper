# countSiteIotEndpoints

> countSiteIotEndpoints

## HTTP

`GET /api/v1/sites/{site_id}/iotendpoints/count`

## Description

Count IoT Endpoints

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| distinct | string | No |  |  | Field used to group this count response. enum: `ap_mac`, `mac`, `site_id`, `type` |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |

## Request Body

None.

## Response

### 200

Result of Count

```json
{
  "additionalProperties": false,
  "description": "Distinct count response for time-bounded search results",
  "properties": {
    "distinct": {
      "description": "Field used to group the count results",
      "type": "string"
    },
    "end": {
      "description": "Search window end timestamp for the count request, in epoch seconds",
      "type": "integer"
    },
    "limit": {
      "description": "Maximum number of distinct count results requested",
      "type": "integer"
    },
    "results": {
      "description": "List of count result rows",
      "items": {
        "additionalProperties": {
          "type": "string"
        },
        "description": "Count result row with the matching distinct field values",
        "properties": {
          "count": {
            "description": "Number of matching items for the distinct value or values in this result",
            "type": "integer"
          }
        },
        "required": [
          "count"
        ],
        "type": "object"
      },
      "type": "array",
      "uniqueItems": true
    },
    "start": {
      "description": "Search window start timestamp for the count request, in epoch seconds",
      "type": "integer"
    },
    "total": {
      "description": "Number of distinct result buckets returned",
      "type": "integer"
    }
  },
  "required": [
    "distinct",
    "end",
    "limit",
    "results",
    "start",
    "total"
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

`mistapi.api.v1.sites.iotendpoints.countSiteIotEndpoints()`

## Usage Context

Use this endpoint to read the resource at `/api/v1/sites/{site_id}/iotendpoints/count`.
Common use cases:

- Use it when you need to count IoT Endpoints.
- Use it in an audit or status workflow before you make a related change.
- Treat this endpoint as a read-only request.
- The installed `mistapi` 0.64.0 signature is `countSiteIotEndpoints(mist_session: mistapi.__api_session.APISession, site_id: str, distinct: str | None = None, start: str | None = None, end: str | None = None, duration: str | None = None, limit: int | None = None) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `site_id`. Use identifiers from a trusted Mist read.
- Query parameters include `distinct`, `start`, `end`, `duration`, `limit`. Keep filters narrow for repeatable results.
- Count endpoints return totals, not records. Use the matching search endpoint for details.

## Related Endpoints

- [GET_sites_site_id_iotendpoints_search.md](GET_sites_site_id_iotendpoints_search.md) -- searchSiteIotEndpoints uses `GET /api/v1/sites/{site_id}/iotendpoints/search`.
- [POST_sites_site_id_iotendpoints_id_zigbee_rejoin.md](POST_sites_site_id_iotendpoints_id_zigbee_rejoin.md) -- rejoinSiteIotEndpointZigbee uses `POST /api/v1/sites/{site_id}/iotendpoints/{id}/zigbee_rejoin`.
- [GET_sites_site_id_insights_fingerprints_count.md](../orgs/GET_sites_site_id_insights_fingerprints_count.md) -- countOrgClientFingerprints uses `GET /api/v1/sites/{site_id}/insights/fingerprints/count`.

## MistHelper Notes

Menu Operation **236** offers this site count endpoint.
Verification source: `git grep -n "countSiteIotEndpoints" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` was also checked for endpoint family menu coverage.
