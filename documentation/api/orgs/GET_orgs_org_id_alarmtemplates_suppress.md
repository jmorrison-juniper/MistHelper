# listOrgSuppressedAlarms

> listOrgSuppressedAlarms

## HTTP

`GET /api/v1/orgs/{org_id}/alarmtemplates/suppress`

## Description

Get List of Org Alarms Currently Suppressed

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
| scope | string | No |  |  | Returns both scopes if not specified |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "title": "response_org_suppress_alarm_item",
        "type": "object",
        "properties": {
          "duration": {
            "type": "integer",
            "description": "Duration, in seconds. Maximum duration is 86400 * 14 (14 days). 0 is to un-suppress alarms.",
            "contentEncoding": "int32"
          },
          "expire_time": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "scheduled_time": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "scope": {
            "type": "string",
            "description": "level of scope. enum: `org`, `site`"
          },
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          }
        }
      },
      "description": ""
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

`mistapi.api.v1.orgs.alarm_templates.listOrgSuppressedAlarms()`

## Usage Context

Retrieves the list of suppressed alarm templates for the organization.

## Gotchas

- Suppressed alarms are silenced but still recorded.

## Related Endpoints

- [GET_orgs_org_id_alarmtemplates.md](GET_orgs_org_id_alarmtemplates.md) — List templates
- [POST_orgs_org_id_alarmtemplates_suppress.md](POST_orgs_org_id_alarmtemplates_suppress.md) — Suppress alarms

## MistHelper Notes

Not currently used by MistHelper directly.
