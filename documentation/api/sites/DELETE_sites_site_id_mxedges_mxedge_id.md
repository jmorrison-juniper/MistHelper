# deleteSiteMxEdge

> deleteSiteMxEdge

## HTTP

`DELETE /api/v1/sites/{site_id}/mxedges/{mxedge_id}`

## Description

Delete Site Mist Edge

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

`mistapi.api.v1.sites.mxedges.deleteSiteMxEdge()`

## Usage Context

Deletes a Mist Edge appliance from a site. Removes the edge device from management.

## Gotchas

- Tunneled APs connected through this edge will lose connectivity.
- Ensure traffic is migrated to other edges before deletion.

## Related Endpoints

- [GET_sites_site_id_mxedges.md](GET_sites_site_id_mxedges.md) — List site Mist Edges
- [GET_sites_site_id_mxedges_mxedge_id.md](GET_sites_site_id_mxedges_mxedge_id.md) — Get specific edge details

## MistHelper Notes

Not currently used by MistHelper directly. Menu **59** uses `listOrgMxEdges` at org level.
