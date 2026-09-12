# searchMspOrgGroup

> searchMspOrgGroup

## HTTP

`GET /api/v1/msps/{msp_id}/search`

## Description

Search in MSP Orgs

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| type | string | Yes |  |  | Orgs |
| q | string | Yes |  |  | Search string |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "next": {
      "type": "string"
    },
    "page": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "response_search_item",
        "required": [
          "id",
          "text",
          "type"
        ],
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "description": "Unique ID of the object instance in the Mist Organization",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "53f10664-3ce8-4c27-b382-0ef66432349f"
            ]
          },
          "text": {
            "type": "string"
          },
          "type": {
            "type": "string"
          }
        }
      },
      "description": ""
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "limit",
    "page",
    "results",
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

`mistapi.api.v1.msps.msps.searchMspOrgGroup()`

## Usage Context

Searches MSP organization groups with filtering capabilities. Use this to find specific org groups within a large MSP by name or other attributes without listing all groups.

## Gotchas

- Despite the generic URL path, this endpoint specifically searches org groups, not all MSP resources.
- Results are paginated — handle pagination for complete results.

## Related Endpoints

- [GET_msps_msp_id_orggroups.md](GET_msps_msp_id_orggroups.md) — List all org groups (no filtering)
- [GET_msps_msp_id_orgs_search.md](GET_msps_msp_id_orgs_search.md) — Search orgs (different resource type)

## MistHelper Notes

Not currently used by MistHelper directly.
