# addInstallerDeviceImage

> addInstallerDeviceImage

## HTTP

`POST /api/v1/installer/orgs/{org_id}/devices/{device_mac}/{image_name}`

## Description

Add image

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

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "auto_deviceprofile_assignment": {
      "type": "boolean",
      "description": "Whether to auto assign device to deviceprofile by name",
      "examples": [
        true
      ]
    },
    "csv": {
      "type": "string",
      "description": "CSV file for ap name mapping, optional",
      "contentEncoding": "base64"
    },
    "file": {
      "type": "string",
      "description": "Ekahau or ibwave file",
      "contentEncoding": "base64"
    },
    "json": {
      "title": "map_import_json",
      "required": [
        "vendor_name"
      ],
      "type": "object",
      "properties": {
        "import_all_floorplans": {
          "type": "boolean",
          "default": false
        },
        "import_height": {
          "type": "boolean",
          "default": true
        },
        "import_orientation": {
          "type": "boolean",
          "default": true
        },
        "vendor_name": {
          "type": "string",
          "description": "enum: `ekahau`, `ibwave`"
        }
      }
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

`mistapi.api.v1.installer.installer.addInstallerDeviceImage()`

## Usage Context

Use this endpoint to upload an image (photo) for a device during installation. Common use cases:

- Documenting the physical installation location of an AP or switch with a photo
- Uploading site survey photos attached to specific devices

## Gotchas

- The `{image_name}` parameter specifies the image filename/identifier
- Image upload is a multipart POST request
- Images are associated with the device MAC address and can be viewed in the Mist dashboard

## Related Endpoints

- [DELETE_installer_orgs_org_id_devices_device_mac_image_name.md](DELETE_installer_orgs_org_id_devices_device_mac_image_name.md) -- Delete a device image
- [GET_installer_orgs_org_id_devices.md](GET_installer_orgs_org_id_devices.md) -- List devices
- [PUT_installer_orgs_org_id_devices_device_mac.md](PUT_installer_orgs_org_id_devices_device_mac.md) -- Provision the device

## MistHelper Notes

Not currently used by MistHelper.
