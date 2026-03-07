# countOrgJsiSirt

> countOrgJsiSirt

## HTTP

`GET /api/v1/orgs/{org_id}/jsi/sirt/count`

## Description

Get count of SIRT advisories grouped by specified field

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
| distinct | string | Yes |  |  | Field to group by. enum: `jsa_updated_date`, `models`, `severity`, `versions` |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |

## Request Body

None.

## Response

### 200

OK

```json
{
  "title": "response_count",
  "required": [
    "distinct",
    "end",
    "limit",
    "results",
    "start",
    "total"
  ],
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

`mistapi.api.v1.orgs.jsi.countOrgJsiSirt()`

## Usage Context

Returns the count of JSI SIRT (Security Incident Response Team) entries.

## Gotchas

- No known gotchas.

## Related Endpoints

- [GET_orgs_org_id_jsi_sirt_search.md](GET_orgs_org_id_jsi_sirt_search.md) — Search SIRT
- [GET_orgs_org_id_jsi_inventory.md](GET_orgs_org_id_jsi_inventory.md) — JSI inventory

## MistHelper Notes

Not currently used by MistHelper directly.
