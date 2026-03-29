# deleteSiteAssetFilter

> deleteSiteAssetFilter

## HTTP

`DELETE /api/v1/sites/{site_id}/assetfilters/{assetfilter_id}`

## Description

Deletes an existing BLE asset filter for the given site.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
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

`mistapi.api.v1.sites.asset_filters.deleteSiteAssetFilter()`

## Usage Context

Deletes an asset filter at a site. Asset filters control which BLE asset beacons are tracked and reported.

## Gotchas

- Deleting an active filter stops tracking for matching assets immediately.

## Related Endpoints

- [GET_sites_site_id_assetfilters.md](GET_sites_site_id_assetfilters.md) — List existing filters
- [POST_sites_site_id_assetfilters.md](POST_sites_site_id_assetfilters.md) — Create new filter

## MistHelper Notes

Not currently used by MistHelper directly.
