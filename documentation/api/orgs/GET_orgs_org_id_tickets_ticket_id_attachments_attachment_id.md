# GetOrgTicketAttachment

> GetOrgTicketAttachment

## HTTP

`GET /api/v1/orgs/{org_id}/tickets/{ticket_id}/attachments/{attachment_id}`

## Description

Get Org ticket Attachment

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| ticket_id | string | Yes |  |
| attachment_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "content_url": {
      "type": "string",
      "examples": [
        "https://api.mist.com/api/v1/forward/download?jwt=..."
      ]
    }
  }
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

`mistapi.api.v1.orgs.tickets.GetOrgTicketAttachment()`

## Usage Context

Retrieves a specific attachment from a support ticket.

## Gotchas

- Returns binary file content; handle the response accordingly.

## Related Endpoints

- [GET_orgs_org_id_tickets_ticket_id.md](GET_orgs_org_id_tickets_ticket_id.md) — Get ticket details
- [GET_orgs_org_id_tickets.md](GET_orgs_org_id_tickets.md) — List tickets

## MistHelper Notes

Not currently used by MistHelper directly.
