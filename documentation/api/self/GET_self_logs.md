# listSelfAuditLogs

> listSelfAuditLogs

## HTTP

`GET /api/v1/self/logs`

## Description

Get List of change logs across all Orgs for current admin
Audit logs records all administrative activities done by current admin across all orgs

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
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
    "page": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "audit_log",
        "required": [
          "admin_id",
          "admin_name",
          "id",
          "message",
          "org_id",
          "site_id",
          "timestamp"
        ],
        "type": "object",
        "properties": {
          "admin_id": {
            "type": "string",
            "description": "ID of the administrator",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "456b7016-a916-a4b1-78dd-72b947c152b7"
            ]
          },
          "admin_name": {
            "type": "string"
          },
          "after": {
            "type": "object",
            "description": "Field values after the change"
          },
          "before": {
            "type": "object",
            "description": "Field values prior to the change"
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
            "type": "string"
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
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
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
    "page",
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

`mistapi.api.v1.self.audit_logs.listSelfAuditLogs()`

## Usage Context

Use this endpoint to retrieve the current admin's audit log history. Common use cases:

- Reviewing your own recent API actions for troubleshooting
- Verifying that configuration changes were applied correctly
- Auditing admin activity for compliance purposes

## Gotchas

- Only returns logs for the currently authenticated admin, not other admins in the organization
- For organization-wide audit logs, use `GET /api/v1/orgs/{org_id}/logs` instead
- Results are ordered by timestamp descending (most recent first)

## Related Endpoints

- [../orgs/GET_orgs_org_id_logs.md](../orgs/GET_orgs_org_id_logs.md) -- Organization-level audit logs (all admins)
- [GET_self.md](GET_self.md) -- View current admin profile
- [GET_self_login_failures.md](GET_self_login_failures.md) -- View login failure history

## MistHelper Notes

Not currently used by MistHelper. For org-level audit logs, see Menu Operation **3** (`OrgExportUtils.audit_logs`).
