# deleteSiteDeviceHaCluster

> deleteSiteDeviceHaCluster

## HTTP

`DELETE /api/v1/sites/{site_id}/devices/{device_id}/ha`

## Description

Delete HA Cluster

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

`mistapi.api.v1.sites.devices_-_wan_cluster.deleteSiteDeviceHaCluster()`

## Usage Context

Deletes the HA (High Availability) cluster configuration for a device. Removes the device from its HA pair.

## Gotchas

- Breaking an HA pair may cause traffic failover. Ensure the remaining node can handle full load.
- Device may need reprovisioning after HA removal.

## Related Endpoints

- [GET_sites_site_id_devices_device_id_ha.md](GET_sites_site_id_devices_device_id_ha.md) — Get current HA status
- [POST_sites_site_id_devices_device_id_ha.md](POST_sites_site_id_devices_device_id_ha.md) — Create HA cluster

## MistHelper Notes

Not currently used by MistHelper directly.
