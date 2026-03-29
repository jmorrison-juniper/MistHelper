# suppressOrgAlarm

> suppressOrgAlarm

## HTTP

`POST /api/v1/orgs/{org_id}/alarmtemplates/suppress`

## Description

In certain situations, for example, scheduled maintenance, you may want to suspend alarms to be triggered against Sites for a period of time.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "applies": {
      "type": "object",
      "properties": {
        "org_id": {
          "type": "string",
          "description": "UUID of the current org (if provided, the alarms will be suppressed at org level)",
          "contentEncoding": "uuid"
        },
        "site_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "contentEncoding": "uuid"
          },
          "description": "List of UUID of the sites within the org (if provided, the alarms will be suppressed for all the mentioned sites under the org)"
        },
        "sitegroup_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "contentEncoding": "uuid"
          },
          "description": "List of UUID of the site groups within the org (if provided, the alarms will be suppressed for all the sites under those site groups)"
        }
      },
      "description": "If `scope`==`site`. Object defines the scope (within the org e.g. whole org, and/or some site_groups, and/or some sites) for which the alarm service has to be suppressed for some `duration`"
    },
    "duration": {
      "maximum": 15552000.0,
      "minimum": 0.0,
      "type": "number",
      "description": "Duration, in seconds. Maximum duration is 86400 * 180 (180 days). 0 is to un-suppress alarms",
      "default": 3600
    },
    "scheduled_time": {
      "type": "integer",
      "description": "Epoch_time in seconds, Default as now, accepted time range is from now to now + 7 days",
      "contentEncoding": "int32"
    },
    "scope": {
      "type": "string",
      "description": "level of scope. enum: `org`, `site`"
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

`mistapi.api.v1.orgs.alarm_templates.suppressOrgAlarm()`

## Usage Context

Suppresses specific alarm types across the organization.

## Gotchas

- Suppressed alarms will not trigger notifications.

## Related Endpoints

- [GET_orgs_org_id_alarmtemplates_suppress.md](GET_orgs_org_id_alarmtemplates_suppress.md) — Get suppressed alarms
- [GET_orgs_org_id_alarmtemplates.md](GET_orgs_org_id_alarmtemplates.md) — List templates

## MistHelper Notes

Not currently used by MistHelper directly.
