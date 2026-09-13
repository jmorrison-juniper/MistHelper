# uploadSiteMxEdgeSupportFiles

> uploadSiteMxEdgeSupportFiles

## HTTP

`POST /api/v1/sites/{site_id}/mxedges/{mxedge_id}/support`

## Description

Support / Upload Mist Edge support files

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

`mistapi.api.v1.sites.mxedges.uploadSiteMxEdgeSupportFiles()`

## Usage Context

Requests support data from a Mist Edge appliance (logs, diagnostics) for troubleshooting.

## Gotchas

- Support bundle generation may take several minutes for large deployments.

## Related Endpoints

- [GET_sites_site_id_mxedges_mxedge_id.md](GET_sites_site_id_mxedges_mxedge_id.md) — Mist Edge config
- [GET_sites_site_id_stats_mxedges_mxedge_id.md](GET_sites_site_id_stats_mxedges_mxedge_id.md) — Mist Edge stats

## MistHelper Notes

Not currently used by MistHelper directly.
