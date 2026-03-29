# listInstallerDeviceProfiles

> listInstallerDeviceProfiles

## HTTP

`GET /api/v1/installer/orgs/{org_id}/deviceprofiles`

## Description

Get List of Device Profiles

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| type | string | No |  |  |  |

## Request Body

None.

## Response

### 200

Installer List of Device Profiles

```json
{
  "type": "array",
  "items": {
    "title": "installers_item",
    "type": "object",
    "properties": {
      "id": {
        "type": "string",
        "description": "Unique ID of the object instance in the Mist Organization",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "53f10664-3ce8-4c27-b382-0ef66432349f"
        ]
      },
      "name": {
        "type": "string",
        "examples": [
          "Entry #1"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "id": "6f4bf402-45f9-2a56-6c8b-7f83d3bc98e9",
        "name": "DeviceProfile 1"
      }
    ]
  ]
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

`mistapi.api.v1.installer.installer.listInstallerDeviceProfiles()`

## Usage Context

Use this endpoint to list device profiles available in the organization. Common use cases:

- Selecting a device profile to apply during AP or switch provisioning
- Checking available device configurations before assigning to devices

## Gotchas

- Read-only endpoint -- device profiles cannot be created or modified through the installer API
- Device profiles contain configuration templates that are applied when a device is assigned to the profile

## Related Endpoints

- [PUT_installer_orgs_org_id_devices_device_mac.md](PUT_installer_orgs_org_id_devices_device_mac.md) -- Provision device with a profile
- [../orgs/GET_orgs_org_id_deviceprofiles.md](../orgs/GET_orgs_org_id_deviceprofiles.md) -- Full admin device profiles list

## MistHelper Notes

Not currently used by MistHelper. MistHelper accesses device profiles through the full admin API (Menu **35**, **109**, **110**).
