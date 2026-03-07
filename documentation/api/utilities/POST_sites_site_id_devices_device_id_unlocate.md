# stopSiteLocateDevice

> stopSiteLocateDevice

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/unlocate`

## Description

Stop Locate a Device

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

`mistapi.api.v1.utilities.common.stopSiteLocateDevice()`

## Usage Context

Deactivates the locator LED/beacon on a device. Stops the blinking LED that was activated by the `locate` command.

## Gotchas

- No known gotchas; safe to call even if locate was not active.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_locate.md](POST_sites_site_id_devices_device_id_locate.md) — Start the locator LED

## MistHelper Notes

Not currently used by MistHelper via REST API.
