# deleteSiteAsset

> deleteSiteAsset

## HTTP

`DELETE /api/v1/sites/{site_id}/assets/{asset_id}`

## Description

Delete Site Asset

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| asset_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

### 201

Created

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

`mistapi.api.v1.sites.assets.deleteSiteAsset()`

## Usage Context

Deletes a BLE asset record from a site. Removes the tracked asset and its location history.

## Gotchas

- Location history for the asset is permanently lost.

## Related Endpoints

- [GET_sites_site_id_assets.md](GET_sites_site_id_assets.md) — List all assets
- [POST_sites_site_id_assets.md](POST_sites_site_id_assets.md) — Create new asset

## MistHelper Notes

Not currently used by MistHelper directly.
