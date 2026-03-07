# UploadOrgTicketAttachment

> UploadOrgTicketAttachment

## HTTP

`POST /api/v1/orgs/{org_id}/tickets/{ticket_id}/attachments`

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

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "file": {
      "type": "string",
      "description": "Ekahau or ibwave file",
      "contentEncoding": "base64"
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

`mistapi.api.v1.orgs.tickets.UploadOrgTicketAttachment()`

## Usage Context

Uploads an attachment to an existing support ticket.

## Gotchas

- File size limits may apply.

## Related Endpoints

- [GET_orgs_org_id_tickets_id.md](GET_orgs_org_id_tickets_id.md) — Get ticket
- [POST_orgs_org_id_tickets_ticket_id_comments.md](POST_orgs_org_id_tickets_ticket_id_comments.md) — Add comment

## MistHelper Notes

Not currently used by MistHelper directly.
