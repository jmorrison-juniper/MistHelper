# deleteOrgWxRule

> deleteOrgWxRule

## HTTP

`DELETE /api/v1/orgs/{org_id}/wxrules/{wxrule_id}`

## Description

Delete Org WxRule

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| wxrule_id | string | Yes |  |

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

`mistapi.api.v1.orgs.wxrules.deleteOrgWxRule()`

## Usage Context

Deletes a WxLAN rule from the organization.

## Gotchas

- Traffic matching this rule will no longer be controlled.

## Related Endpoints

- [GET_orgs_org_id_wxrules.md](GET_orgs_org_id_wxrules.md) — List WxRules
- [POST_orgs_org_id_wxrules.md](POST_orgs_org_id_wxrules.md) — Create WxRule

## MistHelper Notes

Not currently used by MistHelper directly.
