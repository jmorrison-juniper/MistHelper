# deleteOrgAlarmTemplate

> deleteOrgAlarmTemplate

## HTTP

`DELETE /api/v1/orgs/{org_id}/alarmtemplates/{alarmtemplate_id}`

## Description

Delete Org Alarm Template

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| alarmtemplate_id | string | Yes |  |

## Request Body

None.

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

`mistapi.api.v1.orgs.alarm_templates.deleteOrgAlarmTemplate()`

## Usage Context

Deletes an alarm template from the organization.

## Gotchas

- Sites using this template will revert to default alarm behavior.

## Related Endpoints

- [GET_orgs_org_id_alarmtemplates.md](GET_orgs_org_id_alarmtemplates.md) — List templates
- [POST_orgs_org_id_alarmtemplates.md](POST_orgs_org_id_alarmtemplates.md) — Create template

## MistHelper Notes

Used by MistHelper via `listOrgAlarmTemplates` in Menu 1 (Alarms export).
