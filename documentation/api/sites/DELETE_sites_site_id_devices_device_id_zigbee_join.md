# stopSiteDeviceZigbeeJoin

> stopSiteDeviceZigbeeJoin

## HTTP

`DELETE /api/v1/sites/{site_id}/devices/{device_id}/zigbee_join`

## Description

Stop allowing new Zigbee end devices to join the network through the specified AP.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

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

`mistapi.api.v1.sites.devices.stopSiteDeviceZigbeeJoin()`

## Usage Context

Use this endpoint to remove or stop the resource at
`/api/v1/sites/{site_id}/devices/{device_id}/zigbee_join`.
Common use cases:

- Use it when you need to stop allowing new Zigbee end devices to join the network through the specified AP.
- Use it only after you read the related resource and confirm the planned change.
- Treat this endpoint as a state-changing request.
- The installed `mistapi` 0.64.0 signature is `stopSiteDeviceZigbeeJoin(mist_session: mistapi.__api_session.APISession, site_id: str, device_id: str) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `site_id`, `device_id`. Use identifiers from a trusted Mist read.
- This endpoint can change Mist state. Keep a recovery record before you call it.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_zigbee_join.md](POST_sites_site_id_devices_device_id_zigbee_join.md) -- enableSiteDeviceZigbeeJoin uses `POST /api/v1/sites/{site_id}/devices/{device_id}/zigbee_join`.
- [DELETE_sites_site_id_devices_device_id_ha.md](DELETE_sites_site_id_devices_device_id_ha.md) -- deleteSiteDeviceHaCluster uses `DELETE /api/v1/sites/{site_id}/devices/{device_id}/ha`.
- [DELETE_sites_site_id_devices_device_id_image_image_number.md](DELETE_sites_site_id_devices_device_id_image_image_number.md) -- deleteSiteDeviceImage uses `DELETE /api/v1/sites/{site_id}/devices/{device_id}/image/{image_number}`.

## MistHelper Notes

MistHelper does not currently call `stopSiteDeviceZigbeeJoin`.
Verification source: `git grep -n "stopSiteDeviceZigbeeJoin" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
