# deleteOrgJseIntegration

> deleteOrgJseIntegration

## HTTP

`DELETE /api/v1/orgs/{org_id}/setting/jse/setup`

## Description

Delete JSE Integration

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

`mistapi.api.v1.orgs.integration_jse.deleteOrgJseIntegration()`

## Usage Context

Removes the Juniper Security Edge (JSE) integration setup.

## Gotchas

- Disables JSE security services for the organization.

## Related Endpoints

- [POST_orgs_org_id_setting_jse_setup.md](POST_orgs_org_id_setting_jse_setup.md) — Setup JSE
- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Org settings

## MistHelper Notes

Not currently used by MistHelper directly.
