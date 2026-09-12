# startSiteMapsAutoGeofence

> startSiteMapsAutoGeofence

## HTTP

`POST /api/v1/sites/{site_id}/maps/auto_geofences`

## Description

The auto geofence service is a map parsing service that uses map image data to identify the exterior of buildings in the map image also known as "geofences". This API processes all maps for a given SiteId. The maps must have an image to parse for the auto geofence service. Repeated POST requests to this endpoint while the auto geofence service is processing the map will be rejected.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

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

`mistapi.api.v1.sites.maps.startSiteMapsAutoGeofence()`

## Usage Context

Auto-generates geofences for all maps at a site based on floor plan boundaries.

## Gotchas

- Overwrites any existing auto-generated geofences.

## Related Endpoints

- [POST_sites_site_id_maps_map_id_auto_geofences.md](POST_sites_site_id_maps_map_id_auto_geofences.md) — Per-map geofences
- [GET_sites_site_id_maps.md](GET_sites_site_id_maps.md) — List maps

## MistHelper Notes

Not currently used by MistHelper directly.
