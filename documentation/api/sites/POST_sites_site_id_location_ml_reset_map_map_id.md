# resetSiteMlStatsByMap

> resetSiteMlStatsByMap

## HTTP

`POST /api/v1/sites/{site_id}/location/ml/reset/map/{map_id}`

## Description

Reset ML Stats by Map

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

`mistapi.api.v1.sites.location.resetSiteMlStatsByMap()`

## Usage Context

Resets the machine learning location model for a specific map. Clears learned positioning data.

## Gotchas

- Destructive: location accuracy will degrade until the model is retrained.

## Related Endpoints

- [GET_sites_site_id_location_ml_current.md](GET_sites_site_id_location_ml_current.md) — Current ML location data
- [GET_sites_site_id_location_ml_defaults.md](GET_sites_site_id_location_ml_defaults.md) — ML defaults

## MistHelper Notes

Not currently used by MistHelper directly.
