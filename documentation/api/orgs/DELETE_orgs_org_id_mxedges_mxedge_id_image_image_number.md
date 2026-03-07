# deleteOrgMxEdgeImage

> deleteOrgMxEdgeImage

## HTTP

`DELETE /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/image/{image_number}`

## Description

Remove MxEdge Image

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| mxedge_id | string | Yes |  |
| image_number | integer | Yes |  |

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

`mistapi.api.v1.orgs.mxedges.deleteOrgMxEdgeImage()`

## Usage Context

Deletes a specific image from a Mist Edge appliance.

## Gotchas

- No known gotchas.

## Related Endpoints

- [GET_orgs_org_id_mxedges_mxedge_id.md](GET_orgs_org_id_mxedges_mxedge_id.md) — Mist Edge details
- [POST_orgs_org_id_mxedges_mxedge_id_image.md](POST_orgs_org_id_mxedges_mxedge_id_image_image_number.md) — Upload image

## MistHelper Notes

Not currently used by MistHelper directly.
