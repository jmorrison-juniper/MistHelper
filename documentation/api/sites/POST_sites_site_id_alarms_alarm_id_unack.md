# unackSiteAlarm

> unackSiteAlarm

## HTTP

`POST /api/v1/sites/{site_id}/alarms/{alarm_id}/unack`

## Description

Unack Site Alarm

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| alarm_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "note": {
      "type": "string",
      "description": "Some text note describing the intent",
      "examples": [
        "maintenance window"
      ]
    }
  },
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

`mistapi.api.v1.sites.alarms.unackSiteAlarm()`

## Usage Context

Unacknowledges a single alarm by alarm ID, restoring it to active state.

## Gotchas

- No known gotchas.

## Related Endpoints

- [POST_sites_site_id_alarms_alarm_id_ack.md](POST_sites_site_id_alarms_alarm_id_ack.md) — Ack alarm
- [POST_sites_site_id_alarms_unack.md](POST_sites_site_id_alarms_unack.md) — Unack multiple alarms

## MistHelper Notes

Not currently used by MistHelper directly.
