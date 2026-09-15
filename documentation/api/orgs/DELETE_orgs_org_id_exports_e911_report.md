# disableOrgE911Report

> disableOrgE911Report

## HTTP

`DELETE /api/v1/orgs/{org_id}/exports/e911_report`

## Description

Disable automatic E911 AP BSSID report generation for the organization.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "E911 AP BSSID report status for the organization",
  "properties": {
    "detail": {
      "description": "Human-readable description of the action taken",
      "type": "string"
    },
    "last_generated": {
      "description": "Unix timestamp of when the report file was last generated. Only present when `status` is `available`.",
      "type": "integer"
    },
    "status": {
      "description": "Current status of E911 report generation. enum: `disabled`, `scheduled`, `available`",
      "enum": [
        "disabled",
        "scheduled",
        "available"
      ],
      "type": "string"
    },
    "url": {
      "description": "Presigned URL to download the CSV file. Only present when `status` is `available`.",
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

`mistapi.api.v1.orgs.reports.disableOrgE911Report()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
