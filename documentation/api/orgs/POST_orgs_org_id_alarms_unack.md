# unackOrgMultipleAlarms

> unackOrgMultipleAlarms

## HTTP

`POST /api/v1/orgs/{org_id}/alarms/unack`

## Description

Unack multiple Org Alarms

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "alarm_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": ""
    },
    "note": {
      "type": "string",
      "description": "Some text note describing the intent"
    }
  },
  "required": [
    "alarm_ids"
  ],
  "description": "Request Body"
}
```

## Response

### 200

OK

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

`mistapi.api.v1.orgs.alarms.unackOrgMultipleAlarms()`

## Usage Context

Unacknowledges specific alarms by alarm IDs.

## Gotchas

- Requires an array of alarm IDs in the request body.

## Related Endpoints

- [POST_orgs_org_id_alarms_unack_all.md](POST_orgs_org_id_alarms_unack_all.md) — Unack all
- [POST_orgs_org_id_alarms_ack.md](POST_orgs_org_id_alarms_ack.md) — Ack specific

## MistHelper Notes

Not currently used by MistHelper directly.
