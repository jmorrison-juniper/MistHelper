# deleteSite

> deleteSite

## HTTP

`DELETE /api/v1/sites/{site_id}`

## Description

Delete Site

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

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

`mistapi.api.v1.sites.sites.deleteSite()`

## Usage Context

Deletes an entire site from the organization. Removes all configuration, devices, maps, and associated data.

## Gotchas

- **EXTREMELY DESTRUCTIVE**: All devices are unassigned, all config is lost, all historical data for the site is permanently removed.
- Devices become unclaimed and must be re-adopted to a new site.
- This is irreversible. Require explicit confirmation before executing.

## Related Endpoints

- [GET_sites_site_id.md](GET_sites_site_id.md) — Get site details
- [PUT_sites_site_id.md](PUT_sites_site_id.md) — Update site
- [../orgs/POST_orgs_org_id_sites.md](../orgs/POST_orgs_org_id_sites.md) — Create site

## MistHelper Notes

Not currently used by MistHelper directly. Menu **1** uses `listOrgSites` for site listing.
