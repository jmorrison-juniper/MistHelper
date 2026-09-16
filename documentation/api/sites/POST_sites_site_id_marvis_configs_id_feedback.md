# submitSiteMarvisConfigFeedback

> submitSiteMarvisConfigFeedback

## HTTP

`POST /api/v1/sites/{site_id}/marvis_configs/{id}/feedback`

## Description

Submit feedback on a Marvis-injected config action (e.g. mark as invalid).

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "additionalProperties": false,
  "description": "Feedback submission for a Marvis config action",
  "properties": {
    "note": {
      "description": "Free-text note about the feedback",
      "type": "string"
    },
    "type": {
      "description": "Feedback type. enum: `invalid`",
      "enum": [
        "invalid"
      ],
      "type": "string"
    }
  },
  "type": "object"
}
```

## Response

### 200

Marvis Config Feedback response

```json
{
  "additionalProperties": false,
  "description": "Response after submitting feedback on a Marvis config action",
  "properties": {
    "feedback_note": {
      "description": "The note provided with the feedback",
      "type": "string"
    },
    "feedback_type": {
      "description": "The feedback type that was submitted",
      "type": "string"
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

`mistapi.api.v1.sites.marvis_configs.submitSiteMarvisConfigFeedback()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
