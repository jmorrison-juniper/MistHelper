# clearSiteMlOverwriteForMap

> clearSiteMlOverwriteForMap

## HTTP

`DELETE /api/v1/sites/{site_id}/location/ml/map/{map_id}`

## Description

Clear ML Overwrite for Map

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

`mistapi.api.v1.sites.location.clearSiteMlOverwriteForMap()`

## Usage Context

Deletes location ML data for a specific map at a site. Resets indoor location model training for the entire floor/map.

## Gotchas

- All calibration data for the map is lost. Location services need to re-calibrate.

## Related Endpoints

- [PUT_sites_site_id_location_ml_map_map_id.md](PUT_sites_site_id_location_ml_map_map_id.md) — Update map ML data
- [POST_sites_site_id_location_ml_reset_map_map_id.md](POST_sites_site_id_location_ml_reset_map_map_id.md) — Reset ML for the map

## MistHelper Notes

Not currently used by MistHelper directly.
