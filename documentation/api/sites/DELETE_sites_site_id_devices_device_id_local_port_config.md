# deleteSiteLocalSwitchPortConfig

> deleteSiteLocalSwitchPortConfig

## HTTP

`DELETE /api/v1/sites/{site_id}/devices/{device_id}/local_port_config`

## Description

API Calls delete all the existing port config local overrides, and reapply the configured planed at the device level 
(with site / template heritance).

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

`mistapi.api.v1.sites.devices_-_wired.deleteSiteLocalSwitchPortConfig()`

## Usage Context

Deletes the local port configuration override for a device. Reverts port settings to the template/profile defaults.

## Gotchas

- Device reverts to template-defined port config immediately after deletion.

## Related Endpoints

- [PUT_sites_site_id_devices_device_id_local_port_config.md](PUT_sites_site_id_devices_device_id_local_port_config.md) — Set local port config
- [GET_sites_site_id_devices_device_id.md](GET_sites_site_id_devices_device_id.md) — Get device details

## MistHelper Notes

Not currently used by MistHelper directly.
