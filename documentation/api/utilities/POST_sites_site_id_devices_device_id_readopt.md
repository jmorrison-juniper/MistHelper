# readoptSiteOctermDevice

> readoptSiteOctermDevice

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/readopt`

## Description

For the octerm devices, the device ID must come from fpc0. However, for a VC, the users may change the original fpc0 from CLI. To fix the issue, the readopt API could be used to trigger the readopt process so the device would get the correct device ID to connect the cloud.

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

`mistapi.api.v1.utilities.common.readoptSiteOctermDevice()`

## Usage Context

Re-adopts an Octerm (virtual chassis member) device. Forces the device to rejoin the cloud management plane and re-synchronize its configuration.

## Gotchas

- The device may be briefly unreachable during re-adoption.
- Should only be used on devices showing adoption issues.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_reprovision.md](POST_sites_site_id_devices_device_id_reprovision.md) — Push full configuration
- [POST_sites_site_id_devices_device_id_restart.md](POST_sites_site_id_devices_device_id_restart.md) — Full device restart

## MistHelper Notes

Not currently used by MistHelper via REST API.
