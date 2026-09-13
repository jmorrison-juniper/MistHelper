# listOrgAuditLogs

> listOrgAuditLogs

## HTTP

`GET /api/v1/orgs/{org_id}/logs`

## Description

Get List of change logs for the current Org

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| site_id | string | No |  |  | Site id |
| admin_name | string | No |  |  | Admin name or email |
| message | string | No |  |  | Message |
| sort | string | No |  |  | Sort order |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "next": {
      "type": "string"
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "log_event",
        "required": [
          "message",
          "org_id",
          "timestamp"
        ],
        "type": "object",
        "properties": {
          "admin_id": {
            "type": [
              "string",
              "null"
            ],
            "description": "admin id",
            "contentEncoding": "uuid",
            "readOnly": true
          },
          "admin_name": {
            "type": [
              "string",
              "null"
            ],
            "description": "Name of the admin that performs the action",
            "readOnly": true
          },
          "after": {
            "type": "object",
            "description": "field values after the change",
            "readOnly": true
          },
          "before": {
            "type": "object",
            "description": "field values prior to the change",
            "readOnly": true
          },
          "device_id": {
            "type": [
              "string",
              "null"
            ],
            "description": "Device id",
            "contentEncoding": "uuid",
            "readOnly": true
          },
          "for_site": {
            "type": "boolean",
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
          "message": {
            "type": "string",
            "description": "log message",
            "readOnly": true
          },
          "org_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "site_id": {
            "type": [
              "string",
              "null"
            ],
            "contentEncoding": "uuid",
            "readOnly": true
          },
          "src_ip": {
            "type": "string",
            "description": "sender source ip address"
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "end",
    "limit",
    "results",
    "start",
    "total"
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.logs.listOrgAuditLogs()`

## Usage Context

Retrieves audit logs for the organization showing admin actions.

## Gotchas

- Logs include API calls, configuration changes, and admin logins.
- Default time range is limited; specify `start` and `end` for broader queries.

## Related Endpoints

- [GET_orgs_org_id_logs_count.md](GET_orgs_org_id_logs_count.md) — Count audit logs
- [GET_orgs_org_id_events_system_search.md](GET_orgs_org_id_events_system_search.md) — System events

## MistHelper Notes

Not currently used by MistHelper directly.
