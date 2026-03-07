# deleteSiteVirtualChassis

> deleteSiteVirtualChassis

## HTTP

`DELETE /api/v1/sites/{site_id}/devices/{device_id}/vc`

## Description

When all the member switches of VC are removed and only member ID 0 is left, the cloud would detect this situation and automatically changes the single switch to non-VC role.

For some unexpected cases that the VC is gone and disconnected, the API below could be used to change the state of VC’s switches to be standalone. After it is executed, all the switches will be shown as standalone switches under Inventory.

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

`mistapi.api.v1.sites.devices_-_wired_-_virtual_chassis.deleteSiteVirtualChassis()`

## Usage Context

Deletes the Virtual Chassis (VC) configuration for a device. Removes VC membership and inter-member connections.

## Gotchas

- **DESTRUCTIVE**: Disbanding a VC disrupts all traffic through the virtual chassis.
- Member switches become standalone devices and need individual configuration.

## Related Endpoints

- [GET_sites_site_id_devices_device_id_vc.md](GET_sites_site_id_devices_device_id_vc.md) — Get VC configuration
- [POST_sites_site_id_devices_device_id_vc.md](POST_sites_site_id_devices_device_id_vc.md) — Create VC

## MistHelper Notes

Used by Menu **92-93** (`VirtualChassisManager`) for VC conversion operations.
