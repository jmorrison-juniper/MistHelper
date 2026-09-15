# listOrgAuditLogs

> listOrgAuditLogs

## HTTP

`GET /api/v1/orgs/{org_id}/logs/search`

## Description

Get a list of change logs for the current Org

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| site_id | string | No |  |  | Filter results by site identifier. Accepts multiple comma-separated values. |
| admin_name | string | No |  |  | Filter results by one or more administrator names or email addresses. Supports comma-separated values |
| message | string | No |  |  | Filter results by one or more message text values. Supports comma-separated values |
| sort | string | No |  |  | Field used to sort results; a leading `-` indicates descending order. enum: `-timestamp`, `admin_id`, `site_id`, `timestamp` |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Paginated response for audit log search results",
  "properties": {
    "end": {
      "description": "Epoch timestamp for the end of the audit log search window",
      "type": "integer"
    },
    "limit": {
      "description": "Maximum number of audit log events returned in this page",
      "type": "integer"
    },
    "next": {
      "description": "Pagination cursor or URL for retrieving the next page of audit log events",
      "type": "string"
    },
    "results": {
      "description": "Audit log events returned by a log query",
      "items": {
        "additionalProperties": false,
        "description": "Audit log event recorded for an organization or site",
        "properties": {
          "admin_id": {
            "description": "Admin user identifier associated with the log event",
            "format": "uuid",
            "readOnly": true,
            "type": [
              "string",
              "null"
            ]
          },
          "admin_name": {
            "description": "Name of the admin that performs the action",
            "readOnly": true,
            "type": [
              "string",
              "null"
            ]
          },
          "after": {
            "additionalProperties": true,
            "description": "field values after the change",
            "readOnly": true,
            "type": "object"
          },
          "before": {
            "additionalProperties": true,
            "description": "field values prior to the change",
            "readOnly": true,
            "type": "object"
          },
          "device_id": {
            "description": "Device identifier associated with the log event",
            "format": "uuid",
            "readOnly": true,
            "type": [
              "string",
              "null"
            ]
          },
          "for_site": {
            "description": "Whether this log event is scoped to a site",
            "readOnly": true,
            "type": "boolean"
          },
          "id": {
            "description": "Unique ID of the object instance in the Mist Organization",
            "examples": [
              "53f10664-3ce8-4c27-b382-0ef66432349f"
            ],
            "format": "uuid",
            "readOnly": true,
            "type": "string"
          },
          "message": {
            "description": "Human-readable log message describing the event",
            "readOnly": true,
            "type": "string"
          },
          "org_id": {
            "description": "Unique identifier of a Mist organization",
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ],
            "format": "uuid",
            "readOnly": true,
            "type": "string"
          },
          "site_id": {
            "description": "Site associated with the log event, if any",
            "format": "uuid",
            "readOnly": true,
            "type": [
              "string",
              "null"
            ]
          },
          "src_ip": {
            "description": "sender source IP address",
            "type": "string"
          },
          "timestamp": {
            "description": "Epoch timestamp, in seconds",
            "format": "double",
            "readOnly": true,
            "type": "number"
          }
        },
        "required": [
          "message",
          "org_id",
          "timestamp"
        ],
        "type": "object"
      },
      "type": "array",
      "uniqueItems": true
    },
    "start": {
      "description": "Epoch timestamp for the start of the audit log search window",
      "type": "integer"
    },
    "total": {
      "description": "Number of audit log events matching the search filters across all pages",
      "type": "integer"
    }
  },
  "required": [
    "end",
    "limit",
    "results",
    "start",
    "total"
  ],
  "type": "object"
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

`mistapi.api.v1.orgs.logs.listOrgAuditLogs()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
