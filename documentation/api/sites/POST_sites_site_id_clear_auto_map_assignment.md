# clearSiteAutoMapAssignment

> clearSiteAutoMapAssignment

## HTTP

`POST /api/v1/sites/{site_id}/clear_auto_map_assignment`

## Description

Clear (reject) auto map assignment results for a site without applying them. The cached assignment results are cleared. Omit `map_ids` or provide an empty list to reject all pending assignments; provide specific `map_ids` for a partial reject.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "additionalProperties": false,
  "description": "Request body for accepting or clearing pending map assignments",
  "properties": {
    "map_ids": {
      "description": "Optional list of specific map IDs to apply/clear. If not provided or empty, all pending map assignments are accepted/rejected.",
      "items": {
        "format": "uuid",
        "type": "string"
      },
      "type": "array"
    }
  },
  "type": "object"
}
```

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Result returned after clearing auto map assignment candidates",
  "properties": {
    "message": {
      "description": "Human-readable description of the operation result",
      "type": "string"
    },
    "rejected_maps": {
      "description": "List of map IDs that were successfully rejected",
      "items": {
        "format": "uuid",
        "type": "string"
      },
      "type": "array"
    }
  },
  "required": [
    "message",
    "rejected_maps"
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

`mistapi.api.v1.sites.auto_map_assignment.clearSiteAutoMapAssignment()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
