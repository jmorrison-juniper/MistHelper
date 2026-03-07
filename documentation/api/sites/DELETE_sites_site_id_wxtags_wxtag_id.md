# deleteSiteWxTag

> deleteSiteWxTag

## HTTP

`DELETE /api/v1/sites/{site_id}/wxtags/{wxtag_id}`

## Description

Delete Site WxTag

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| wxtag_id | string | Yes |  |

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

`mistapi.api.v1.sites.wxtags.deleteSiteWxTag()`

## Usage Context

Deletes a WxLAN tag from a site. Removes the tag used to classify clients or resources in WxLAN rules.

## Gotchas

- Any WxLAN rules referencing this tag may become invalid or match nothing.

## Related Endpoints

- [GET_sites_site_id_wxtags.md](GET_sites_site_id_wxtags.md) — List WxLAN tags
- [POST_sites_site_id_wxtags.md](POST_sites_site_id_wxtags.md) — Create WxLAN tag

## MistHelper Notes

Not currently used by MistHelper directly.
