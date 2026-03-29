# searchOrgPskPortalLogs

> searchOrgPskPortalLogs

## HTTP

`GET /api/v1/orgs/{org_id}/pskportals/logs/search`

## Description

Search Org PSK Portal Logs

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
| psk_name | string | No |  |  |  |
| psk_id | string | No |  |  |  |
| pskportal_id | string | No |  |  |  |
| id | string | No |  |  | audit_id |
| admin_name | string | No |  |  |  |
| admin_id | string | No |  |  |  |
| name_id | string | No |  |  | Name_id used in SSO |
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

Example response

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1428954000
      ]
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        100
      ]
    },
    "next": {
      "type": "string"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "response_psk_portal_logs_search_item",
        "type": "object",
        "properties": {
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
            "examples": [
              "Rotate PSK test@mist.com"
            ]
          },
          "name_id": {
            "type": "string",
            "examples": [
              "test@mist.com"
            ]
          },
          "org_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "psk_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "examples": [
              "608fe603-f9f0-4ce9-9473-04ef6c6ea749"
            ]
          },
          "psk_name": {
            "type": "string",
            "examples": [
              "test@mist.com"
            ]
          },
          "pskportal_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "examples": [
              "c1742c09-af35-4161-96ef-7dc65c6d5674"
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
      "contentEncoding": "int32",
      "examples": [
        1428939600
      ]
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        135
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.psk_portals.searchOrgPskPortalLogs()`

## Usage Context

Searches PSK portal log entries across the organization.

## Gotchas

- Useful for auditing PSK usage and access.

## Related Endpoints

- [GET_orgs_org_id_pskportals_logs_count.md](GET_orgs_org_id_pskportals_logs_count.md) — Count logs
- [GET_orgs_org_id_pskportals.md](GET_orgs_org_id_pskportals.md) — List portals

## MistHelper Notes

Not currently used by MistHelper directly.
