# deleteInstallerDeviceImage

> deleteInstallerDeviceImage

## HTTP

`DELETE /api/v1/installer/orgs/{org_id}/devices/{device_mac}/{image_name}`

## Description

Delete image

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| image_name | string | Yes |  |
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

`mistapi.api.v1.installer.installer.deleteInstallerDeviceImage()`

## Usage Context

Use this endpoint to delete a previously uploaded device image. Common use cases:

- Removing an incorrect or outdated installation photo
- Cleaning up images before uploading replacements

## Gotchas

- The `{image_name}` must match the exact filename used during upload
- Deletion is permanent -- the image cannot be recovered after deletion

## Related Endpoints

- [POST_installer_orgs_org_id_devices_device_mac_image_name.md](POST_installer_orgs_org_id_devices_device_mac_image_name.md) -- Upload a replacement image
- [GET_installer_orgs_org_id_devices.md](GET_installer_orgs_org_id_devices.md) -- List devices

## MistHelper Notes

Not currently used by MistHelper.
