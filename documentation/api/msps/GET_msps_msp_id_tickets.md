# listMspTickets

> listMspTickets

## HTTP

`GET /api/v1/msps/{msp_id}/tickets`

## Description

Get List of Tickets of a MSP

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |

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
  "type": "array",
  "items": {
    "title": "ticket",
    "required": [
      "subject",
      "type"
    ],
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
    "description": "Support Ticket"
  },
  "description": "",
  "examples": [
    [
      {
        "comments": [
          {
            "attachments": [
              {
                "content_type": "string",
                "content_url": "string"
              }
            ],
            "author": "string",
            "comment": "string",
            "created_at": 0
          }
        ],
        "created_at": 0,
        "id": "b069b358-4c97-5319-1f8c-7c5ca64d6ab1",
        "requester": "string",
        "status": "open",
        "subject": "string",
        "type": "string",
        "updated_at": 0
      }
    ]
  ]
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

`mistapi.api.v1.msps.tickets.listMspTickets()`

## Usage Context

Lists support tickets across all organizations managed by the MSP. Provides a unified view of open issues, RMA requests, and Juniper TAC cases for the MSP's entire customer base.

## Gotchas

- Tickets may include sensitive customer information — access should be restricted to authorized MSP administrators.
- Results are paginated; use pagination parameters for complete ticket lists.

## Related Endpoints

- [GET_msps_msp_id_tickets_count.md](GET_msps_msp_id_tickets_count.md) — Get ticket count before fetching
- [GET_msps_msp_id_suggestion_count.md](GET_msps_msp_id_suggestion_count.md) — Marvis AI action suggestions

## MistHelper Notes

Not currently used by MistHelper directly.
