# addSiteDeviceImage

> addSiteDeviceImage

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/image/{image_number}`

## Description

Attach up to 3 images to a device

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

Content-Type: `application/json`

```json
{
  "required": [
    "file"
  ],
  "type": "object",
  "properties": {
    "file": {
      "type": "string",
      "description": "Binary file",
      "contentEncoding": "base64"
    },
    "json": {
      "type": "string"
    }
  }
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

`mistapi.api.v1.sites.devices.addSiteDeviceImage()`

## Usage Context

Uploads a device image (photo of physical device installation). Used for documentation and verification.

## Gotchas

- Image must be uploaded as multipart/form-data. `image_number` is 1-3.

## Related Endpoints

- [DELETE_sites_site_id_devices_device_id_image_image_number.md](DELETE_sites_site_id_devices_device_id_image_image_number.md) — Delete device image
- [GET_sites_site_id_devices_device_id.md](GET_sites_site_id_devices_device_id.md) — Device config

## MistHelper Notes

Not currently used by MistHelper directly.
