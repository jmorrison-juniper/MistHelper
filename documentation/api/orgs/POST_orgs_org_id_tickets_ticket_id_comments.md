# addOrgTicketComment

> addOrgTicketComment

## HTTP

`POST /api/v1/orgs/{org_id}/tickets/{ticket_id}/comments`

## Description

Add Comment to support ticket

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
    "comment": {
      "type": "string",
      "examples": [
        "this is urgent"
      ]
    },
    "file": {
      "type": "string",
      "contentEncoding": "base64"
    }
  }
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "case_number": {
      "type": "string",
      "readOnly": true
    },
    "comments": {
      "type": "array",
      "items": {
        "title": "ticket_comment",
        "required": [
          "author",
          "comment",
          "created_at"
        ],
        "type": "object",
        "properties": {
          "attachment_ids": {
            "type": "array",
            "items": {
              "type": "string",
              "contentEncoding": "uuid"
            },
            "description": "",
            "readOnly": true,
            "examples": [
              [
                "00000000-0000-0000-0000-15231a659c78"
              ]
            ]
          },
          "attachments": {
            "type": "array",
            "items": {
              "title": "ticket_comments_attachment",
              "type": "object",
              "properties": {
                "content_type": {
                  "type": "string",
                  "examples": [
                    "image/png"
                  ]
                },
                "content_url": {
                  "type": "string",
                  "examples": [
                    "https://api.mist.com/api/v1/forward/download?jwt=..."
                  ]
                },
                "created_at": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    1453908369
                  ]
                },
                "file_name": {
                  "type": "string",
                  "examples": [
                    "crash.png"
                  ]
                },
                "id": {
                  "type": "string",
                  "description": "Unique ID of the object instance in the Mist Organization",
                  "contentEncoding": "uuid",
                  "readOnly": true,
                  "examples": [
                    "53f10664-3ce8-4c27-b382-0ef66432349f"
                  ]
                },
                "size_in_bytes": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    1943
                  ]
                }
              }
            },
            "description": "",
            "readOnly": true
          },
          "author": {
            "type": "string",
            "readOnly": true
          },
          "comment": {
            "type": "string"
          },
          "created_at": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          }
        }
      },
      "description": ""
    },
    "created_at": {
      "type": "integer",
      "contentEncoding": "int32",
      "readOnly": true
    },
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    },
    "requester": {
      "type": "string",
      "readOnly": true
    },
    "requester_email": {
      "type": "string",
      "description": "Email of the requester"
    },
    "status": {
      "type": "string",
      "description": "Ticket status. enum: \n  * open: ticket is open, Mist is working on it\n  * pending: ticket is open and Requester attention is needed (e.g. Mist is asking for some more information)\n  * solved: ticket is marked as solved / considered by Mist (requester can update it, causing it to re-open; or rate it)\n  * closed: ticket is archived and cannot be changed."
    },
    "subject": {
      "type": "string"
    },
    "type": {
      "type": "string",
      "description": "Question (default) / bug / critical"
    },
    "updated_at": {
      "type": "integer",
      "contentEncoding": "int32",
      "readOnly": true
    }
  },
  "required": [
    "subject",
    "type"
  ],
  "description": "Support Ticket"
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

`mistapi.api.v1.orgs.tickets.addOrgTicketComment()`

## Usage Context

Adds a comment to an existing support ticket.

## Gotchas

- Comments are appended chronologically.

## Related Endpoints

- [GET_orgs_org_id_tickets_ticket_id.md](GET_orgs_org_id_tickets_ticket_id.md) — Get ticket
- [POST_orgs_org_id_tickets_ticket_id_attachments.md](POST_orgs_org_id_tickets_ticket_id_attachments.md) — Add attachment

## MistHelper Notes

Not currently used by MistHelper directly.
