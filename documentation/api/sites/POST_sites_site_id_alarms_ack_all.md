# ackSiteAllAlarms

> ackSiteAllAlarms

## HTTP

`POST /api/v1/sites/{site_id}/alarms/ack_all`

## Description

Ack all Site Alarms

**N.B.**: Batch size for multiple alarm ack and unack has to be less or or equal to 1000.

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
  "title": "note_string",
  "type": "object",
  "properties": {
    "note": {
      "type": "string",
      "description": "Some text note describing the intent",
      "examples": [
        "maintenance window"
      ]
    }
  }
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

`mistapi.api.v1.sites.alarms.ackSiteAllAlarms()`

## Usage Context

Acknowledges all active alarms at a site in bulk.

## Gotchas

- Destructive operation: acknowledges ALL alarms, not a selective subset.

## Related Endpoints

- [POST_sites_site_id_alarms_ack.md](POST_sites_site_id_alarms_ack.md) — Ack specific alarms
- [POST_sites_site_id_alarms_unack_all.md](POST_sites_site_id_alarms_unack_all.md) — Unack all alarms

## MistHelper Notes

Not currently used by MistHelper directly.
