# deleteSitePsk

> deleteSitePsk

## HTTP

`DELETE /api/v1/sites/{site_id}/psks/{psk_id}`

## Description

Delete Site PSK

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| psk_id | string | Yes | PSK ID |

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

`mistapi.api.v1.sites.psks.deleteSitePsk()`

## Usage Context

Deletes a Pre-Shared Key (PSK) from a site. Removes the key and any associated user/device assignments.

## Gotchas

- Clients using this PSK will be disconnected and cannot reconnect until given a new key.

## Related Endpoints

- [GET_sites_site_id_psks.md](GET_sites_site_id_psks.md) — List site PSKs
- [POST_sites_site_id_psks.md](POST_sites_site_id_psks.md) — Create new PSK

## MistHelper Notes

Not currently used by MistHelper directly. Menu **46** uses `listOrgPsks` at org level.
