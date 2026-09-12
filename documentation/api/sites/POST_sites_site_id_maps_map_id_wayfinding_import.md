# importSiteWayfindings

> importSiteWayfindings

## HTTP

`POST /api/v1/sites/{site_id}/maps/{map_id}/wayfinding/import`

## Description

This imports the vendor map meta data into the Map JSON. This is required by the SDK and App in order to access/render the vendor Map properly.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| map_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "description": "Request Body"
}
```

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

`mistapi.api.v1.sites.maps.importSiteWayfindings()`

## Usage Context

Imports wayfinding data (paths, nodes) for a specific map. Used for indoor navigation.

## Gotchas

- Wayfinding requires maps with accurate scale and coordinate settings.

## Related Endpoints

- [GET_sites_site_id_maps_map_id.md](GET_sites_site_id_maps_map_id.md) — Map details
- [POST_sites_site_id_maps_map_id_set_map.md](POST_sites_site_id_maps_map_id_set_map.md) — Set map properties

## MistHelper Notes

Not currently used by MistHelper directly.
