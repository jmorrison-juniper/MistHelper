# countMspsMarvisActions

> countMspsMarvisActions

## HTTP

`GET /api/v1/msps/{msp_id}/suggestion/count`

## Description

Count by Distinct Attributes of Marvis actions

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
| distinct | string | No |  |  |  |
| limit | integer | No | 100 |  |  |

## Request Body

None.

## Response

### 200

Marvis Actions Count

```json
{
  "type": "object",
  "properties": {
    "distinct": {
      "type": "string",
      "examples": [
        "status"
      ]
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1000
      ]
    },
    "results": {
      "type": "array",
      "items": {
        "title": "response_count_marvis_actions_result",
        "type": "object",
        "properties": {
          "count": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              24
            ]
          }
        },
        "additionalProperties": {
          "type": "string"
        }
      },
      "description": "",
      "examples": [
        [
          {
            "count": 24,
            "status": "002e176a-0000-000-1111-002e208b20e1"
          },
          {
            "count": 12,
            "status": "2d3f176a-0000-000-2222-002e208f176a"
          },
          {
            "count": 15,
            "status": "08b2176a-0000-000-3333-002e208b2d3f"
          }
        ]
      ]
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        3
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.msps.marvis.countMspsMarvisActions()`

## Usage Context

Returns the count of Marvis AI action suggestions across MSP-managed organizations. Marvis Actions are AI-driven recommendations for resolving network issues, improving performance, or optimizing configurations.

## Gotchas

- Marvis Actions require an active Marvis subscription/license for the managed organizations.
- The count reflects pending (unresolved) suggestions; resolved suggestions are not included.

## Related Endpoints

- [GET_msps_msp_id_tickets.md](GET_msps_msp_id_tickets.md) — Support tickets (manual vs AI-suggested actions)
- [GET_msps_msp_id_insights_metric.md](GET_msps_msp_id_insights_metric.md) — SLE metrics that may trigger Marvis suggestions

## MistHelper Notes

Not currently used by MistHelper directly.
