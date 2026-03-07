# deleteSiteMap

> deleteSiteMap

## HTTP

`DELETE /api/v1/sites/{site_id}/maps/{map_id}`

## Description

Delete Site Map

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

`mistapi.api.v1.sites.maps.deleteSiteMap()`

## Usage Context

Deletes a map (floor plan) from a site. Removes the map, its image, AP placements, zones, and associated location data.

## Gotchas

- **DESTRUCTIVE**: All AP placement data, zones, and location calibration for this floor are permanently lost.
- APs assigned to this map become unplaced.

## Related Endpoints

- [GET_sites_site_id_maps.md](GET_sites_site_id_maps.md) — List all maps
- [POST_sites_site_id_maps.md](POST_sites_site_id_maps.md) — Create new map

## MistHelper Notes

Used by Menu **112** (`MapsManagerLauncher`) for map deletion operations.
