# clearSiteMlOverwriteForDevice

> clearSiteMlOverwriteForDevice

## HTTP

`DELETE /api/v1/sites/{site_id}/location/ml/device/{device_id}`

## Description

Clear ML Overwrite for Device

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| device_id | string | Yes |  |

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

`mistapi.api.v1.sites.location.clearSiteMlOverwriteForDevice()`

## Usage Context

Deletes location ML (Machine Learning) data for a specific device at a site. Resets the indoor location model training data for that device.

## Gotchas

- Location accuracy may degrade until the ML model re-trains.

## Related Endpoints

- [PUT_sites_site_id_location_ml_device_device_id.md](PUT_sites_site_id_location_ml_device_device_id.md) — Update device ML data
- [GET_sites_site_id_location_ml_current.md](GET_sites_site_id_location_ml_current.md) — View current ML model

## MistHelper Notes

Not currently used by MistHelper directly.
