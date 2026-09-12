# deleteOrgMxEdge

> deleteOrgMxEdge

## HTTP

`DELETE /api/v1/orgs/{org_id}/mxedges/{mxedge_id}`

## Description

Delete Org MxEdge

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
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

`mistapi.api.v1.orgs.mxedges.deleteOrgMxEdge()`

## Usage Context

Deletes a Mist Edge appliance from the organization.

## Gotchas

- Active tunnels and services on the Mist Edge are disrupted.

## Related Endpoints

- [GET_orgs_org_id_mxedges.md](GET_orgs_org_id_mxedges.md) — List Mist Edges
- [POST_orgs_org_id_mxedges.md](POST_orgs_org_id_mxedges.md) — Create Mist Edge

## MistHelper Notes

Used by MistHelper via `listOrgMxEdges` in Menu 59.
