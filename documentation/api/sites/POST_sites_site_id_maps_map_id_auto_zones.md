# startSiteMapAutoZone

> startSiteMapAutoZone

## HTTP

`POST /api/v1/sites/{site_id}/maps/{map_id}/auto_zones`

## Description

This API starts the auto zones service for a specified map. This map must have an image to parse for the auto zones service. Repeated POST requests to this endpoint while the auto zones service is processing the map will be rejected.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| map_id | string | Yes |  |
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

`mistapi.api.v1.sites.maps_-_auto-zone.startSiteMapAutoZone()`

## Usage Context

Auto-generates zones on a map based on floor plan features (walls, rooms, corridors).

## Gotchas

- Auto-generated zones may need manual adjustment for accuracy.

## Related Endpoints

- [GET_sites_site_id_maps_map_id_auto_zones.md](GET_sites_site_id_maps_map_id_auto_zones.md) — Get auto-zone results
- [POST_sites_site_id_zones.md](POST_sites_site_id_zones.md) — Create zone manually

## MistHelper Notes

Not currently used by MistHelper directly.
