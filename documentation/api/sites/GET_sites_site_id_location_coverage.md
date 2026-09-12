# getSiteBeamCoverageOverview

> getSiteBeamCoverageOverview

## HTTP

`GET /api/v1/sites/{site_id}/location/coverage`

## Description

Get Beam Coverage Overview

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| map_id | string | No |  |  | Map_id (filter by map_id) |
| type | string | No |  |  |  |
| client_type | string | No |  |  | Client_type (as filter. optional) |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| resolution | string | No |  |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "beams_means": {
      "type": "array",
      "items": {
        "type": "array",
        "items": {
          "type": "number"
        }
      },
      "description": "List of [x, y, mean]s, x/y are in meters (UI would need to use map.ppm to calculate the pixel location from top-left)."
    },
    "end": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "gridsize": {
      "type": "number",
      "description": "Size of grid, in meter"
    },
    "result_def": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of names annotating the fields in results"
    },
    "results": {
      "type": "array",
      "items": {
        "type": "array",
        "items": {
          "type": "number"
        }
      },
      "description": "List of results, see result_def."
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "beams_means",
    "end",
    "gridsize",
    "result_def",
    "results",
    "start"
  ]
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

`mistapi.api.v1.sites.location.getSiteBeamCoverageOverview()`

## Usage Context

Retrieves location service coverage data for a site, showing which areas have sufficient AP density for accurate indoor positioning.

## Gotchas

- Coverage quality depends on AP density, placement accuracy, and map calibration.

## Related Endpoints

- [GET_sites_site_id_location_ml_current.md](GET_sites_site_id_location_ml_current.md) — Current ML model
- [GET_sites_site_id_maps.md](GET_sites_site_id_maps.md) — Maps for coverage context

## MistHelper Notes

Not currently used by MistHelper directly.
