# countOrgMxEdges

> countOrgMxEdges

## HTTP

`GET /api/v1/orgs/{org_id}/mxedges/count`

## Description

Count by Distinct Attributes of Org Mist Edges

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| distinct | string | No |  |  |  |
| mxedge_id | string | No |  |  | Mist edge id |
| site_id | string | No |  |  | Mist edge site id |
| mxcluster_id | string | No |  |  | Mist edge cluster id |
| model | string | No |  |  | Model name |
| distro | string | No |  |  | Debian code name (buster, bullseye) |
| tunterm_version | string | No |  |  | tunterm version |
| sort | string | No |  |  | Sort options, -prefix represents DESC order, default is -last_seen |
| stats | boolean | No |  |  | Whether to return device stats, default is false |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
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

`mistapi.api.v1.orgs.mxedges.countOrgMxEdges()`

## Usage Context

Returns the count of Mist Edge appliances grouped by specified fields.

## Gotchas

- No known gotchas.

## Related Endpoints

- [GET_orgs_org_id_mxedges_search.md](GET_orgs_org_id_mxedges_search.md) — Search edges
- [GET_orgs_org_id_mxedges.md](GET_orgs_org_id_mxedges.md) — List edges

## MistHelper Notes

Not currently used by MistHelper directly.
