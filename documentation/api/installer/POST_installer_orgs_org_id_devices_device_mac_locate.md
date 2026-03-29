# startInstallerLocateDevice

> startInstallerLocateDevice

## HTTP

`POST /api/v1/installer/orgs/{org_id}/devices/{device_mac}/locate`

## Description

Locate a Device by blinking it’s LED, it’s a persisted state that has to be stopped by calling Stop Locating API

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

`mistapi.api.v1.installer.installer.startInstallerLocateDevice()`

## Usage Context

Use this endpoint to locate a device by making its LED blink. Common use cases:

- Finding a specific AP or switch in a crowded rack or ceiling during installation
- Confirming which physical device corresponds to a given MAC address

## Gotchas

- The LED blinking is a persistent state -- it does not stop automatically. You must call the unlocate endpoint to stop it
- The device must be powered on and connected to the cloud for the locate command to work

## Related Endpoints

- [POST_installer_orgs_org_id_devices_device_mac_unlocate.md](POST_installer_orgs_org_id_devices_device_mac_unlocate.md) -- Stop the LED blinking
- [GET_installer_orgs_org_id_devices.md](GET_installer_orgs_org_id_devices.md) -- List devices to find MAC addresses
- [../utilities/POST_sites_site_id_devices_device_id_locate.md](../utilities/POST_sites_site_id_devices_device_id_locate.md) -- Full admin locate endpoint

## MistHelper Notes

Not currently used by MistHelper. MistHelper uses the full admin-level site device APIs instead.
