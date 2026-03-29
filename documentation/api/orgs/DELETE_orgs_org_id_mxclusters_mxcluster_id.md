# deleteOrgMxEdgeCluster

> deleteOrgMxEdgeCluster

## HTTP

`DELETE /api/v1/orgs/{org_id}/mxclusters/{mxcluster_id}`

## Description

Delete Org MXEdge Cluster

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| mxcluster_id | string | Yes |  |

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

`mistapi.api.v1.orgs.mxclusters.deleteOrgMxEdgeCluster()`

## Usage Context

Deletes a Mist Edge cluster from the organization.

## Gotchas

- All Mist Edges in the cluster must be removed first.

## Related Endpoints

- [GET_orgs_org_id_mxclusters.md](GET_orgs_org_id_mxclusters.md) — List clusters
- [POST_orgs_org_id_mxclusters.md](POST_orgs_org_id_mxclusters.md) — Create cluster

## MistHelper Notes

Not currently used by MistHelper directly.
