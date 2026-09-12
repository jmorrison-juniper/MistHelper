# stopInstallerLocateDevice

> stopInstallerLocateDevice

## HTTP

`POST /api/v1/installer/orgs/{org_id}/devices/{device_mac}/unlocate`

## Description

Stop it

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| device_mac | string | Yes |  |

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

`mistapi.api.v1.installer.installer.stopInstallerLocateDevice()`

## Usage Context

Use this endpoint to stop a device's LED from blinking after a locate operation. Common use cases:

- Turning off the LED blink after positively identifying the physical device
- Cleaning up locate state when moving on to the next installation task

## Gotchas

- Must be called explicitly to stop the LED blinking -- it does not time out automatically
- Only works on devices that are currently in locate mode

## Related Endpoints

- [POST_installer_orgs_org_id_devices_device_mac_locate.md](POST_installer_orgs_org_id_devices_device_mac_locate.md) -- Start the LED blinking
- [../utilities/POST_sites_site_id_devices_device_id_unlocate.md](../utilities/POST_sites_site_id_devices_device_id_unlocate.md) -- Full admin unlocate endpoint

## MistHelper Notes

Not currently used by MistHelper.
