# countOrgMarvisClientsStats

> countOrgMarvisClientsStats

## HTTP

`GET /api/v1/orgs/{org_id}/stats/marvisclients/count`

## Description

Count Marvis Client stats records by a distinct field.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| distinct | string | No | os_type |  | Field to count by. enum: `device_id`, `wifi_mac`, `wifi_ip`, `hostname`, `model`, `mfg`, `serial`, `os_type`, `os_version` |
| device_id | string | No |  |  | Filter by Marvis Client installation device UUID |
| wifi_mac | string | No |  |  | Filter by device Wi-Fi MAC address |
| wifi_ip | string | No |  |  | Filter by device Wi-Fi IP address |
| hostname | string | No |  |  | Filter by device hostname |
| model | string | No |  |  | Filter by device model |
| mfg | string | No |  |  | Filter by device manufacturer |
| serial | string | No |  |  | Filter by device serial number |
| os_type | string | No |  |  | Filter by device OS type or platform |
| os_version | string | No |  |  | Filter by device OS version |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |

## Request Body

None.

## Response

### 200

Count result

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

`mistapi.api.v1.orgs.stats.countOrgMarvisClientsStats()`

## Usage Context

Use this endpoint to read the resource at
`/api/v1/orgs/{org_id}/stats/marvisclients/count`.
Common use cases:

- Use it when you need to count Marvis Client stats records by a distinct field.
- Use it in an audit or status workflow before you make a related change.
- Treat this endpoint as a read-only request.
- The installed `mistapi` 0.64.0 signature is `countOrgMarvisClientsStats(mist_session: mistapi.__api_session.APISession, org_id: str, distinct: str | None = None, device_id: str | None = None, wifi_mac: str | None = None, wifi_ip: str | None = None, hostname: str | None = None, model: str | None = None, mfg: str | None = None, serial: str | None = None, os_type: str | None = None, os_version: str | None = None, limit: int | None = None, start: str | None = None, end: str | None = None, duration: str | None = None) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `org_id`. Use identifiers from a trusted Mist read.
- Query parameters include `distinct`, `device_id`, `wifi_mac`, `wifi_ip`, `hostname`. Keep filters narrow for repeatable results.
- Count endpoints return totals, not records. Use the matching search endpoint for details.

## Related Endpoints

- [DELETE_orgs_org_id_stats_marvisclients.md](DELETE_orgs_org_id_stats_marvisclients.md) -- deleteOrgMarvisClient uses `DELETE /api/v1/orgs/{org_id}/stats/marvisclients`.
- [GET_orgs_org_id_stats_marvisclients_search.md](GET_orgs_org_id_stats_marvisclients_search.md) -- searchOrgMarvisClientsStats uses `GET /api/v1/orgs/{org_id}/stats/marvisclients/search`.
- [GET_orgs_org_id_stats.md](GET_orgs_org_id_stats.md) -- getOrgStats uses `GET /api/v1/orgs/{org_id}/stats`.

## MistHelper Notes

Menu Operation **235** offers this org count endpoint.
Verification source: `git grep -n "countOrgMarvisClientsStats" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` was also checked for endpoint family menu coverage.
