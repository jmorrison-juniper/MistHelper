# searchOrgSystemEvents

> searchOrgSystemEvents

## HTTP

`GET /api/v1/orgs/{org_id}/events/system/search`

## Description

Search Org System Events

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
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

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
        "title": "org_system_event",
        "type": "object",
        "properties": {
          "change_cat": {
            "type": "string",
            "examples": [
              "admin_action"
            ]
          },
          "metadata": {
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
          "scope": {
            "type": "string",
            "examples": [
              "org"
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
          },
          "type": {
            "type": "string",
            "examples": [
              "delete-wlan"
            ]
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

`mistapi.api.v1.orgs.events.searchOrgSystemEvents()`

## Usage Context

Searches system-level events (audit logs, configuration changes) across the organization.

## Gotchas

- Includes admin actions, API changes, and org-level events.

## Related Endpoints

- [GET_orgs_org_id_events_system_count.md](GET_orgs_org_id_events_system_count.md) — Count system events
- [GET_orgs_org_id_logs.md](GET_orgs_org_id_logs.md) — Audit logs

## MistHelper Notes

Not currently used by MistHelper directly.
