# kickSiteDeviceZigbeeClients

> kickSiteDeviceZigbeeClients

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/zigbee_kick`

## Description

Kick one or more Zigbee clients from a Zigbee-enabled AP. The AP must be connected.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "additionalProperties": false,
  "description": "Request body for kicking one or more Zigbee clients from an AP",
  "properties": {
    "macs": {
      "description": "One or more Zigbee EUI-64 (8-byte) MACs. Accepts colon-separated (`00:17:7a:01:06:0c:ae:9f`) or plain hex (`00177a01060cae9f`). Must be non-empty.",
      "examples": [
        [
          "00177a01060cae9f",
          "00177a01060caea1"
        ]
      ],
      "items": {
        "type": "string"
      },
      "minItems": 1,
      "type": "array"
    }
  },
  "required": [
    "macs"
  ],
  "type": "object"
}
```

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

`mistapi.api.v1.sites.devices.kickSiteDeviceZigbeeClients()`

## Usage Context

Use this endpoint to start or create the resource at
`/api/v1/sites/{site_id}/devices/{device_id}/zigbee_kick`.
Common use cases:

- Use it when you need to kick one or more Zigbee clients from a Zigbee-enabled AP.
- Use it only after you read the related resource and confirm the planned change.
- Treat this endpoint as a state-changing request.
- The installed `mistapi` 0.64.0 signature is `kickSiteDeviceZigbeeClients(mist_session: mistapi.__api_session.APISession, site_id: str, device_id: str, body: dict | list) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `site_id`, `device_id`. Use identifiers from a trusted Mist read.
- The JSON body requires `macs`. Missing required fields return a 400 response.
- This endpoint can change Mist state. Keep a recovery record before you call it.

## Related Endpoints

- [DELETE_sites_site_id_devices_device_id_ha.md](DELETE_sites_site_id_devices_device_id_ha.md) -- deleteSiteDeviceHaCluster uses `DELETE /api/v1/sites/{site_id}/devices/{device_id}/ha`.
- [DELETE_sites_site_id_devices_device_id_image_image_number.md](DELETE_sites_site_id_devices_device_id_image_image_number.md) -- deleteSiteDeviceImage uses `DELETE /api/v1/sites/{site_id}/devices/{device_id}/image/{image_number}`.
- [DELETE_sites_site_id_devices_device_id_local_port_config.md](DELETE_sites_site_id_devices_device_id_local_port_config.md) -- deleteSiteLocalSwitchPortConfig uses `DELETE /api/v1/sites/{site_id}/devices/{device_id}/local_port_config`.

## MistHelper Notes

MistHelper does not currently call `kickSiteDeviceZigbeeClients`.
Verification source: `git grep -n "kickSiteDeviceZigbeeClients" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
