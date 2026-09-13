# reprovisionSiteAllDevices

> reprovisionSiteAllDevices

## HTTP

`POST /api/v1/sites/{site_id}/devices/reprovision`

## Description

To force all Devices to reprovision itself again.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

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

`mistapi.api.v1.utilities.wi-fi.reprovisionSiteAllDevices()`

## Usage Context

Reprovisions all devices at a site. Forces every managed device to re-apply its configuration from the cloud. Useful after bulk template changes.

## Gotchas

- Causes brief disruptions across all devices at the site as they re-apply configuration.
- Use during maintenance windows for production sites.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_reprovision.md](POST_sites_site_id_devices_device_id_reprovision.md) — Reprovision a single device

## MistHelper Notes

Not currently used by MistHelper via REST API.
