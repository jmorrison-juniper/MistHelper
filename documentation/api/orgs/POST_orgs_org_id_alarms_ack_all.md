# ackOrgAllAlarms

> ackOrgAllAlarms

## HTTP

`POST /api/v1/orgs/{org_id}/alarms/ack_all`

## Description

Ack all Org Alarms

**N.B.**: Batch size for multiple alarm ack and unack has to be less or or equal to 1000.

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

`mistapi.api.v1.orgs.alarms.ackOrgAllAlarms()`

## Usage Context

Acknowledges all alarms for the organization.

## Gotchas

- This is a bulk operation that affects ALL unacknowledged alarms.
- Cannot be easily undone; use with caution.

## Related Endpoints

- [POST_orgs_org_id_alarms_ack.md](POST_orgs_org_id_alarms_ack.md) — Ack specific alarms
- [POST_orgs_org_id_alarms_unack_all.md](POST_orgs_org_id_alarms_unack_all.md) — Unack all

## MistHelper Notes

Not currently used by MistHelper directly.
