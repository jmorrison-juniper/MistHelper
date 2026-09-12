# deleteSiteApAutoplacement

> deleteSiteApAutoplacement

## HTTP

`DELETE /api/v1/sites/{site_id}/maps/{map_id}/auto_placement`

## Description

This API is called to force stop auto placement for a given map

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

Autoplacement Process has stopped for this map

## Errors

| Status | Description |
|--------|-------------|
| 400 | Autoplacement was not triggered |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.maps_-_auto-placement.deleteSiteApAutoplacement()`

## Usage Context

Deletes auto-placement results for a map. Clears automatically calculated AP positions on the floor plan.

## Gotchas

- AP positions revert to manual placement or unplaced state.

## Related Endpoints

- [GET_sites_site_id_maps_map_id_auto_placement.md](GET_sites_site_id_maps_map_id_auto_placement.md) — View auto-placement results
- [POST_sites_site_id_maps_map_id_auto_placement.md](POST_sites_site_id_maps_map_id_auto_placement.md) — Re-run auto-placement

## MistHelper Notes

Not currently used by MistHelper directly. Menu **112** (`MapsManagerLauncher`) handles map operations.
