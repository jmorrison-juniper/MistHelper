# deleteSiteApAutoOrientation

> deleteSiteApAutoOrientation

## HTTP

`DELETE /api/v1/sites/{site_id}/maps/{map_id}/auto_orient`

## Description

This API is called to force stop auto placement for a given map

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

Auto orient process has stopped for this map

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

`mistapi.api.v1.sites.maps_-_auto-placement.deleteSiteApAutoOrientation()`

## Usage Context

Deletes auto-orientation results for a map. Clears the automatically calculated AP orientation data.

## Gotchas

- Auto-orient must be re-run if AP placement accuracy is needed.

## Related Endpoints

- [GET_sites_site_id_maps_map_id_auto_orient.md](GET_sites_site_id_maps_map_id_auto_orient.md) — View auto-orient results
- [POST_sites_site_id_maps_map_id_auto_orient.md](POST_sites_site_id_maps_map_id_auto_orient.md) — Re-run auto-orient

## MistHelper Notes

Not currently used by MistHelper directly. Menu **112** (`MapsManagerLauncher`) handles map operations.
