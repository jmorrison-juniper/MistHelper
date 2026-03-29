# getSiteMxEdge

> getSiteMxEdge

## HTTP

`GET /api/v1/sites/{site_id}/mxedges/{mxedge_id}`

## Description

Get Site Mist Edge

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| mxedge_id | string | Yes |  |

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

`mistapi.api.v1.sites.mxedges.getSiteMxEdge()`

## Usage Context

Retrieves details of a specific Mist Edge appliance at a site, including tunnel status and configuration.

## Gotchas

- No known gotchas.

## Related Endpoints

- [PUT_sites_site_id_mxedges_mxedge_id.md](PUT_sites_site_id_mxedges_mxedge_id.md) — Update edge
- [DELETE_sites_site_id_mxedges_mxedge_id.md](DELETE_sites_site_id_mxedges_mxedge_id.md) — Delete edge
- [GET_sites_site_id_mxedges.md](GET_sites_site_id_mxedges.md) — List all edges

## MistHelper Notes

Not currently used by MistHelper directly.
