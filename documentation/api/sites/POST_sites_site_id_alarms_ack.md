# AckSiteMultipleAlarms

> AckSiteMultipleAlarms

## HTTP

`POST /api/v1/sites/{site_id}/alarms/ack`

## Description

Ack multiple Site Alarms

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

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
      "description": "",
      "examples": [
        [
          "ccb8c94d-ca56-4075-932f-1f2ab444ff2c",
          "98ff4a3d-ec9b-4138-a42e-54fc3335179d"
        ]
      ]
    },
    "note": {
      "type": "string",
      "description": "Some text note describing the intent",
      "examples": [
        "maintenance window"
      ]
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

`mistapi.api.v1.sites.alarms.AckSiteMultipleAlarms()`

## Usage Context

Acknowledges specific alarms at a site by providing a list of alarm IDs.

## Gotchas

- Requires valid alarm IDs. Invalid IDs are silently ignored.

## Related Endpoints

- [POST_sites_site_id_alarms_ack_all.md](POST_sites_site_id_alarms_ack_all.md) — Ack all alarms
- [POST_sites_site_id_alarms_unack.md](POST_sites_site_id_alarms_unack.md) — Unack specific alarms

## MistHelper Notes

Not currently used by MistHelper directly.
