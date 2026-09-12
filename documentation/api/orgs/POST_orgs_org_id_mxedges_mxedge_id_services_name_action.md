# controlOrgMxEdgeServices

> controlOrgMxEdgeServices

## HTTP

`POST /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/services/{name}/{action}`

## Description

Control Services on a Mist Edge

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| mxedge_id | string | Yes |  |
| name | string | Yes | enum: `mxagent`, `mxdas`, `mxnacedge`, `mxocproxy`, `radsecproxy`, `tunterm` |
| action | string | Yes | Restart or start or stop |

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

`mistapi.api.v1.orgs.mxedges.controlOrgMxEdgeServices()`

## Usage Context

Performs an action (start/stop/restart) on a specific Mist Edge service.

## Gotchas

- Service names and available actions vary by Mist Edge configuration.

## Related Endpoints

- [GET_orgs_org_id_mxedges_mxedge_id.md](GET_orgs_org_id_mxedges_mxedge_id.md) — Get Mist Edge
- [POST_orgs_org_id_mxedges_mxedge_id_restart.md](POST_orgs_org_id_mxedges_mxedge_id_restart.md) — Restart Mist Edge

## MistHelper Notes

Not currently used by MistHelper directly.
