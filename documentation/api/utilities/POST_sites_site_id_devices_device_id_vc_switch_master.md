# toogleSiteDeviceVcRoutingEnginesRole

> toogleSiteDeviceVcRoutingEnginesRole

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/vc/switch_master`

## Description

In a pre-provisioned VC, mastership is system-determined. This command allows manual toggling between primary and backup Routing Engines.

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
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.utilities.lan.toogleSiteDeviceVcRoutingEnginesRole()`

## Usage Context

Toggles the routing engine role in a Virtual Chassis (VC). Switches the master/backup roles between VC members for maintenance or failover testing.

## Gotchas

- Causes a brief traffic disruption during role switchover.
- Requires the VC to be in a healthy dual-RE state before toggling.
- Only works on EX switches in Virtual Chassis configuration.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_restart.md](POST_sites_site_id_devices_device_id_restart.md) — Restart individual VC member
- [POST_sites_site_id_devices_device_id_snapshot.md](POST_sites_site_id_devices_device_id_snapshot.md) — Snapshot config before role change

## MistHelper Notes

Used by Menu **94-96** for VC conversion and routing engine role operations.
