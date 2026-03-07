# deleteSiteWxRule

> deleteSiteWxRule

## HTTP

`DELETE /api/v1/sites/{site_id}/wxrules/{wxrule_id}`

## Description

Delete Site WxLan Rule

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
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

`mistapi.api.v1.sites.wxrules.deleteSiteWxRule()`

## Usage Context

Deletes a WxLAN rule from a site. Removes the wireless LAN access restriction rule.

## Gotchas

- Clients previously blocked by this rule will gain access immediately.

## Related Endpoints

- [GET_sites_site_id_wxrules.md](GET_sites_site_id_wxrules.md) — List WxLAN rules
- [POST_sites_site_id_wxrules.md](POST_sites_site_id_wxrules.md) — Create WxLAN rule

## MistHelper Notes

Not currently used by MistHelper directly.
