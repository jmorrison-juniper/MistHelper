# reprovisionSiteOctermDevice

> reprovisionSiteOctermDevice

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/reprovision`

## Description

To force one device to reprovision itself again.

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

`mistapi.api.v1.utilities.common.reprovisionSiteOctermDevice()`

## Usage Context

Re-pushes the full configuration to an Octerm device. Forces the device to re-apply its template, site, and device-level settings from the cloud.

## Gotchas

- Causes a brief service disruption as the configuration is re-applied.
- Should not be necessary under normal conditions — use when config drift is suspected.

## Related Endpoints

- [POST_sites_site_id_devices_reprovision.md](POST_sites_site_id_devices_reprovision.md) — Reprovision all devices at a site
- [GET_sites_site_id_devices_device_id_config_cmd.md](GET_sites_site_id_devices_device_id_config_cmd.md) — Preview rendered config

## MistHelper Notes

Not currently used by MistHelper via REST API.
