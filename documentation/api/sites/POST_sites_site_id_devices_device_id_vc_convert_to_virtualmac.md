# convertSiteVirtualChassisToVirtualMac

> convertSiteVirtualChassisToVirtualMac

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/vc/convert_to_virtualmac`

## Description

Converts an FPC0-based VC to a Virtualmac VC, removing the limitation where the device ID must change whenever FPC0 is renumbered or removed.


HTTP400 Error possible reasons:
  - The device is not an OC device
  - Virtualmac VC is disabled in the Org Knob settings
  - The VC is already a Virtualmac VC
  - The VC is currently disconnected
  - The device is standalone
  - A new FPC0 exists with its own device config, causing ambiguity.

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

`mistapi.api.v1.sites.devices_-_wired_-_virtual_chassis.convertSiteVirtualChassisToVirtualMac()`

## Usage Context

Converts a Virtual Chassis switch to use virtual MAC addressing. Part of VC setup workflow.

## Gotchas

- Destructive operation: causes a reboot of all VC members. Requires explicit confirmation.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_vc.md](POST_sites_site_id_devices_device_id_vc.md) — VC operations
- [POST_sites_site_id_devices_device_id_set_vc_port_mode.md](POST_sites_site_id_devices_device_id_set_vc_port_mode.md) — Set VC port mode

## MistHelper Notes

Used by Menu **94** (VC Conversion) for converting switches to virtual MAC mode.
