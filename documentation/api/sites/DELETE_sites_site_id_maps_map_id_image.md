# deleteSiteMapImage

> deleteSiteMapImage

## HTTP

`DELETE /api/v1/sites/{site_id}/maps/{map_id}/image`

## Description

Delete Site Map Image

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| map_id | string | Yes |  |

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

`mistapi.api.v1.sites.maps.deleteSiteMapImage()`

## Usage Context

Deletes the floor plan image from a map. Removes the visual background used for AP placement and location services.

## Gotchas

- AP positions remain but the visual reference for placement is lost.
- Location heatmaps and wayfinding lose their visual context.

## Related Endpoints

- [POST_sites_site_id_maps_map_id_image.md](POST_sites_site_id_maps_map_id_image.md) — Upload new map image
- [GET_sites_site_id_maps_map_id.md](GET_sites_site_id_maps_map_id.md) — Get map details

## MistHelper Notes

Not currently used by MistHelper directly. Menu **112** (`MapsManagerLauncher`) manages map images.
