# unsuppressOrgSuppressedAlarms

> unsuppressOrgSuppressedAlarms

## HTTP

`DELETE /api/v1/orgs/{org_id}/alarmtemplates/suppress`

## Description

Un-Suppress Suppressed Alarms

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

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

`mistapi.api.v1.orgs.alarm_templates.unsuppressOrgSuppressedAlarms()`

## Usage Context

Removes alarm suppression rules from the organization.

## Gotchas

- Removing suppression may trigger a flood of previously suppressed alerts.

## Related Endpoints

- [GET_orgs_org_id_alarmtemplates.md](GET_orgs_org_id_alarmtemplates.md) — List templates
- [POST_orgs_org_id_alarmtemplates_suppress.md](POST_orgs_org_id_alarmtemplates_suppress.md) — Suppress alarms

## MistHelper Notes

Not currently used by MistHelper directly.
