# subscribeOrgAlarmsReports

> subscribeOrgAlarmsReports

## HTTP

`POST /api/v1/orgs/{org_id}/subscriptions`

## Description

Subscribe to Org Alarms/Reports
Subscriptions define how Org Alarms/Reports are delivered to whom

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

`mistapi.api.v1.orgs.alarms.subscribeOrgAlarmsReports()`

## Usage Context

Creates or activates a subscription for the organization.

## Gotchas

- Subscription management is typically handled through Juniper channels.

## Related Endpoints

- [GET_orgs_org_id_subscriptions.md](GET_orgs_org_id_subscriptions.md) — List subscriptions
- [GET_orgs_org_id_licenses.md](GET_orgs_org_id_licenses.md) — Get licenses

## MistHelper Notes

Not currently used by MistHelper directly.
