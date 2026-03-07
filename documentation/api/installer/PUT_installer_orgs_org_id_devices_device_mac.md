# provisionInstallerDevices

> provisionInstallerDevices

## HTTP

`PUT /api/v1/installer/orgs/{org_id}/devices/{device_mac}`

## Description

Provision or Replace a device 

If replacing_mac is in the request payload, other attributes are ignored, we attempt to replace existing device (with mac replacing_mac) with the inventory device being configured. The replacement device must be in the inventory but not assigned, and the replacing_mac device must be assigned to a site, and satisfy grace period requirements. The Device replaced will become unassigned.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| device_mac | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "deviceprofile_name": {
      "type": "string",
      "examples": [
        "SJ1"
      ]
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "height": {
      "type": "number",
      "examples": [
        2.7
      ]
    },
    "map_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "examples": [
        "845a23bf-bed9-e43c-4c86-6fa474be7ae5"
      ]
    },
    "name": {
      "type": "string",
      "examples": [
        "SJ1-AP1"
      ]
    },
    "orientation": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        90
      ]
    },
    "replacing_mac": {
      "type": "string",
      "description": "Onlif this is to replace an existing device",
      "examples": [
        "5c5b3500003"
      ]
    },
    "role": {
      "type": "string",
      "description": "Optional role for switch / gateway"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "examples": [
        "72771e6a-6f5e-4de4-a5b9-1266c4197811"
      ]
    },
    "site_name": {
      "type": "string",
      "examples": [
        "SJ1"
      ]
    },
    "x": {
      "type": "number",
      "examples": [
        150
      ]
    },
    "y": {
      "type": "number",
      "examples": [
        300
      ]
    }
  },
  "required": [
    "name"
  ],
  "description": "Request Body"
}
```

## Response

### 200

OK

## Errors

| Status | Description |
|--------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not Found |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.installer.installer.provisionInstallerDevices()`

## Usage Context

Use this endpoint to provision or replace a device during field installation. Common use cases:

- Assigning a claimed device to a specific site and map position
- Replacing a failed device with a new unit while preserving the configuration

## Gotchas

- The `{device_mac}` must match a device already claimed to the organization
- Device replacement preserves the site assignment and configuration from the original device
- This is the primary endpoint used by the Mist mobile app for device provisioning

## Related Endpoints

- [GET_installer_orgs_org_id_devices.md](GET_installer_orgs_org_id_devices.md) -- List devices to find the MAC address
- [POST_installer_orgs_org_id_devices.md](POST_installer_orgs_org_id_devices.md) -- Claim a device first
- [DELETE_installer_orgs_org_id_devices_device_mac.md](DELETE_installer_orgs_org_id_devices_device_mac.md) -- Unassign the device
- [PUT_installer_orgs_org_id_sites_site_name.md](PUT_installer_orgs_org_id_sites_site_name.md) -- Assign device to a site

## MistHelper Notes

Not currently used by MistHelper.
