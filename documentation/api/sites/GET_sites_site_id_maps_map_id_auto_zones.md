# getSiteMapAutoZoneStatus

> getSiteMapAutoZoneStatus

## HTTP

`GET /api/v1/sites/{site_id}/maps/{map_id}/auto_zones`

## Description

This API provides the current status of the auto zones service for a given map

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

Status of Auto-Zone request

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "description": "The status for the auto zones service for a given map. enum:\n  * not_started: The auto zones service has not been run on this map or the results were cleared by the user\n  * in_progress: The auto zones service is currently in progress\n  * awaiting_review: The auto zones service has completed and suggested location zones to be added to the map\n  * error: There was an error with the auto zones service"
    },
    "zones": {
      "type": "array",
      "items": {
        "title": "response_auto_zone_zone",
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "description": "The name of the suggested zone",
            "examples": [
              "zone1"
            ]
          },
          "vertices": {
            "type": "array",
            "items": {
              "title": "response_auto_zone_zone_vertex",
              "type": "object",
              "properties": {
                "x": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    10
                  ]
                },
                "y": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    42
                  ]
                }
              }
            },
            "description": "A list of of points comprising the zones map location in pixels"
          }
        },
        "description": "A list of suggested zones to review and accept for a given map"
      },
      "description": ""
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

`mistapi.api.v1.sites.maps_-_auto-zone.getSiteMapAutoZoneStatus()`

## Usage Context

Retrieves auto-generated zone boundaries for a map. Shows zones created from RF coverage analysis.

## Gotchas

- Results are only meaningful after auto-zones has been run via POST.

## Related Endpoints

- [POST_sites_site_id_maps_map_id_auto_zones.md](POST_sites_site_id_maps_map_id_auto_zones.md) — Generate zones
- [DELETE_sites_site_id_maps_map_id_auto_zones.md](DELETE_sites_site_id_maps_map_id_auto_zones.md) — Clear zones

## MistHelper Notes

Not currently used by MistHelper directly. Menu **112** (`MapsManagerLauncher`) handles map operations.
