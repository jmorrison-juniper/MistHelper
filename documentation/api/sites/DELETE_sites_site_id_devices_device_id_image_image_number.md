# deleteSiteDeviceImage

> deleteSiteDeviceImage

## HTTP

`DELETE /api/v1/sites/{site_id}/devices/{device_id}/image/{image_number}`

## Description

Delete image from a device

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| device_id | string | Yes |  |
| image_number | integer | Yes |  |

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

`mistapi.api.v1.sites.devices.deleteSiteDeviceImage()`

## Usage Context

Deletes a specific image associated with a device (e.g., AP photo for documentation purposes).

## Gotchas

- Image numbering is positional; deleting images may shift remaining image indices.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_image_image_number.md](POST_sites_site_id_devices_device_id_image_image_number.md) — Upload device image
- [GET_sites_site_id_devices_device_id.md](GET_sites_site_id_devices_device_id.md) — Get full device details

## MistHelper Notes

Not currently used by MistHelper directly.
