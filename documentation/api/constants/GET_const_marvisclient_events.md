# listMarvisClientEventsDefinitions

> listMarvisClientEventsDefinitions

## HTTP

`GET /api/v1/const/marvisclient_events`

## Description

Return Marvis Client event type definitions used by the Marvis Client event search and count APIs.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of Marvis Client event type definitions

```json
{
  "description": "Marvis Client event type definitions returned by the constants API",
  "items": {
    "additionalProperties": false,
    "description": "A Marvis Client event type definition",
    "properties": {
      "display": {
        "description": "Human-readable name for this Marvis Client event type",
        "examples": [
          "Marvis Client Roamed"
        ],
        "type": "string"
      },
      "key": {
        "description": "Event type key used in Marvis Client event search and count APIs",
        "examples": [
          "MARVISCLIENT_ROAMED"
        ],
        "type": "string"
      }
    },
    "type": "object"
  },
  "type": "array"
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

`mistapi.api.v1.constants.definitions.listMarvisClientEventsDefinitions()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
