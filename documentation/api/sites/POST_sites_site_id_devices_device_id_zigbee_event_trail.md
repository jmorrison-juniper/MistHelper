# startSiteDeviceZigbeeEventTrail

> startSiteDeviceZigbeeEventTrail

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/zigbee_event_trail`

## Description

Start a Zigbee event trail session on an AP. Returns a `session` that the UI can use to stream results.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Response containing the session identifier for a Zigbee event or packet trail operation",
  "properties": {
    "session": {
      "description": "Session ID the UI can use to stream trail results",
      "examples": [
        "7a5f7796-83ee-11e5-95c6-1258369c38a9"
      ],
      "format": "uuid",
      "type": "string"
    }
  },
  "type": "object"
}
```

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

`mistapi.api.v1.sites.devices.startSiteDeviceZigbeeEventTrail()`

## Usage Context

Use this endpoint to start or create the resource at
`/api/v1/sites/{site_id}/devices/{device_id}/zigbee_event_trail`.
Common use cases:

- Use it when you need to start a Zigbee event trail session on an AP.
- Use it only after you read the related resource and confirm the planned change.
- Treat this endpoint as a state-changing request.
- The installed `mistapi` 0.64.0 signature is `startSiteDeviceZigbeeEventTrail(mist_session: mistapi.__api_session.APISession, site_id: str, device_id: str) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `site_id`, `device_id`. Use identifiers from a trusted Mist read.
- This endpoint can change Mist state. Keep a recovery record before you call it.

## Related Endpoints

- [DELETE_sites_site_id_devices_device_id_ha.md](DELETE_sites_site_id_devices_device_id_ha.md) -- deleteSiteDeviceHaCluster uses `DELETE /api/v1/sites/{site_id}/devices/{device_id}/ha`.
- [DELETE_sites_site_id_devices_device_id_image_image_number.md](DELETE_sites_site_id_devices_device_id_image_image_number.md) -- deleteSiteDeviceImage uses `DELETE /api/v1/sites/{site_id}/devices/{device_id}/image/{image_number}`.
- [DELETE_sites_site_id_devices_device_id_local_port_config.md](DELETE_sites_site_id_devices_device_id_local_port_config.md) -- deleteSiteLocalSwitchPortConfig uses `DELETE /api/v1/sites/{site_id}/devices/{device_id}/local_port_config`.

## MistHelper Notes

MistHelper does not currently call `startSiteDeviceZigbeeEventTrail`.
Verification source: `git grep -n "startSiteDeviceZigbeeEventTrail" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
