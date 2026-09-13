# getSiteApAutoOrientation

> getSiteApAutoOrientation

## HTTP

`GET /api/v1/sites/{site_id}/maps/{map_id}/auto_orient`

## Description

This API is called to view the current status of auto orient for a given map.

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

Map queued for auto orientation

```json
{
  "type": "object",
  "properties": {
    "est_time_left": {
      "type": "number",
      "description": "Only when `status`==`inprogress`, estimate of the time to completion"
    },
    "start_time": {
      "type": "number",
      "description": "time when auto orient process was last queued for this map"
    },
    "status": {
      "type": "string",
      "description": "The status of auto orient for a given map. enum:\n  * `pending`: Auto orient has not been requested for this map\n  * `inprogress`: Auto orient is currently processing\n  * `done`: The auto orient process has completed\n  * `error`: There was an error in the auto orient process"
    },
    "stop_time": {
      "type": "number",
      "description": "time when auto orient completed or was manually stopped"
    }
  }
}
```

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

`mistapi.api.v1.sites.maps_-_auto-placement.getSiteApAutoOrientation()`

## Usage Context

Retrieves auto-orientation results for a map. Shows the calculated AP antenna orientations based on RF data.

## Gotchas

- Results are only meaningful after auto-orient has been run via POST.

## Related Endpoints

- [POST_sites_site_id_maps_map_id_auto_orient.md](POST_sites_site_id_maps_map_id_auto_orient.md) — Run auto-orient
- [DELETE_sites_site_id_maps_map_id_auto_orient.md](DELETE_sites_site_id_maps_map_id_auto_orient.md) — Clear results

## MistHelper Notes

Not currently used by MistHelper directly. Menu **112** (`MapsManagerLauncher`) handles map operations.
