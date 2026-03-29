# deleteOrgAssetFilter

> deleteOrgAssetFilter

## HTTP

`DELETE /api/v1/orgs/{org_id}/assetfilters/{assetfilter_id}`

## Description

Deletes an existing BLE asset filter for the given site.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| assetfilter_id | string | Yes |  |

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

`mistapi.api.v1.orgs.asset_filters.deleteOrgAssetFilter()`

## Usage Context

Deletes an asset filter from the organization.

## Gotchas

- Deleting a filter immediately stops tracking assets matching its criteria.

## Related Endpoints

- [GET_orgs_org_id_assetfilters.md](GET_orgs_org_id_assetfilters.md) — List filters
- [POST_orgs_org_id_assetfilters.md](POST_orgs_org_id_assetfilters.md) — Create filter

## MistHelper Notes

Not currently used by MistHelper directly.
