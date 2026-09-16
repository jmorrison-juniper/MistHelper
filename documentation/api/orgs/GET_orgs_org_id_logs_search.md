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

Use this endpoint to read the resource at `/api/v1/orgs/{org_id}/logs/search`.
Common use cases:

- Use it when you need to get a list of change logs for the current Org.
- Use it in an audit or status workflow before you make a related change.
- Treat this endpoint as a read-only request.
- The installed `mistapi` 0.64.0 signature is `listOrgAuditLogs(mist_session: mistapi.__api_session.APISession, org_id: str, site_id: str | None = None, admin_name: str | None = None, message: str | None = None, sort: str | None = None, start: str | None = None, end: str | None = None, duration: str | None = None, limit: int | None = None, page: int | None = None) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `org_id`. Use identifiers from a trusted Mist read.
- Query parameters include `site_id`, `admin_name`, `message`, `sort`, `start`. Keep filters narrow for repeatable results.

## Related Endpoints

- [GET_orgs_org_id_logs.md](GET_orgs_org_id_logs.md) -- listOrgAuditLogs uses `GET /api/v1/orgs/{org_id}/logs`.
- [GET_orgs_org_id_logs_count.md](GET_orgs_org_id_logs_count.md) -- countOrgAuditLogs uses `GET /api/v1/orgs/{org_id}/logs/count`.
- [DELETE_orgs_org_id.md](DELETE_orgs_org_id.md) -- deleteOrg uses `DELETE /api/v1/orgs/{org_id}`.

## MistHelper Notes

Menu Operation **22** exports recent organization audit logs.
Menu Operation **98** exports organization audit logs for 52 weeks.
Menu Operation **25** uses this endpoint for the audit log analysis report.
Menu Operation **153** includes this endpoint in bulk organization data collection.
Verification source: `git grep -n "listOrgAuditLogs" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` was also checked for endpoint family menu coverage.
