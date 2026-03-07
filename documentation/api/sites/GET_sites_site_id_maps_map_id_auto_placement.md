# getSiteApAutoPlacement

> getSiteApAutoPlacement

## HTTP

`GET /api/v1/sites/{site_id}/maps/{map_id}/auto_placement`

## Description

This API is called to view the current status of auto placement for a given map.


#### Status Descriptions

| Status | Description |
| --- | --- |
| `pending` | Autoplacement has not been requested for this map |
| `inprogress` | Autoplacement is currently processing |
| `done` | The autoplacement process has completed |
| `data_needed` | Additional position data is required for autoplacement. Users should verify the requested anchor APs have a position on the map |
| `invalid_model` | Autoplacement is not supported on the model of the APs on the map |
| `invalid_version` | Autoplacement is not supported with the APs current firmware version |
| `error` | There was an error in the autoplacement process |

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

```json
{
  "type": "object",
  "properties": {
    "end_time": {
      "type": "number",
      "description": "Time when autoplacement completed or was manually stopped"
    },
    "est_time_left": {
      "type": "number",
      "description": "(Only when inprogress) estimate of the time to completion"
    },
    "start_time": {
      "type": "integer",
      "description": "Time when autoplacement process was last queued for this map",
      "contentEncoding": "int32"
    },
    "status": {
      "type": "string",
      "description": "the status of autoplacement for a given map. enum: `done`, `error`, `inprogress`, `pending`"
    }
  }
}
```

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

`mistapi.api.v1.sites.maps_-_auto-placement.getSiteApAutoPlacement()`

## Usage Context

Retrieves auto-placement results for a map. Shows calculated AP positions based on RF neighbor data.

## Gotchas

- Results are only meaningful after auto-placement has been run via POST.

## Related Endpoints

- [POST_sites_site_id_maps_map_id_auto_placement.md](POST_sites_site_id_maps_map_id_auto_placement.md) — Run auto-placement
- [DELETE_sites_site_id_maps_map_id_auto_placement.md](DELETE_sites_site_id_maps_map_id_auto_placement.md) — Clear results

## MistHelper Notes

Not currently used by MistHelper directly. Menu **112** (`MapsManagerLauncher`) handles map operations.
