# unackOrgAllAlarms

> unackOrgAllAlarms

## HTTP

`POST /api/v1/orgs/{org_id}/alarms/unack_all`

## Description

Unack all Org Alarms

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

`mistapi.api.v1.orgs.alarms.unackOrgAllAlarms()`

## Usage Context

Unacknowledges all alarms for the organization.

## Gotchas

- Bulk operation affecting ALL acknowledged alarms.

## Related Endpoints

- [POST_orgs_org_id_alarms_unack.md](POST_orgs_org_id_alarms_unack.md) — Unack specific
- [POST_orgs_org_id_alarms_ack_all.md](POST_orgs_org_id_alarms_ack_all.md) — Ack all

## MistHelper Notes

Not currently used by MistHelper directly.
