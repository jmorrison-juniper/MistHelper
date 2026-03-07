# listInstallerListOfRecentlyClaimedDevices

> listInstallerListOfRecentlyClaimedDevices

## HTTP

`GET /api/v1/installer/orgs/{org_id}/devices`

## Description

Get List of recently claimed devices

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
| model | string | No |  |  | Device Model |
| site_name | string | No |  |  | Site Name |
| site_id | string | No |  |  | Site ID |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

List of Devices Recently Claimed

```json
{
  "type": "array",
  "items": {
    "title": "installer_device",
    "type": "object",
    "properties": {
      "connected": {
        "type": "boolean",
        "examples": [
          true
        ]
      },
      "deviceprofile_name": {
        "type": "string",
        "examples": [
          "SJ1"
        ]
      },
      "ext_ip": {
        "type": "string",
        "examples": [
          "12.34.56.78"
        ]
      },
      "height": {
        "type": "number",
        "examples": [
          2.7
        ]
      },
      "ip": {
        "type": "string",
        "examples": [
          "192.168.1.111"
        ]
      },
      "last_seen": {
        "type": [
          "number",
          "null"
        ],
        "description": "Last seen timestamp",
        "readOnly": true,
        "examples": [
          1470417522
        ]
      },
      "mac": {
        "type": "string",
        "examples": [
          "5c5b35000018"
        ]
      },
      "map_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "examples": [
          "845a23bf-bed9-e43c-4c86-6fa474be7ae5"
        ]
      },
      "model": {
        "type": "string",
        "examples": [
          "AP41"
        ]
      },
      "name": {
        "type": "string",
        "examples": [
          "hallway"
        ]
      },
      "orientation": {
        "type": "integer",
        "contentEncoding": "int32",
        "examples": [
          90
        ]
      },
      "serial": {
        "type": "string",
        "examples": [
          "FXLH2015150025"
        ]
      },
      "site_name": {
        "type": "string",
        "examples": [
          "SJ1"
        ]
      },
      "uptime": {
        "type": "integer",
        "contentEncoding": "int32",
        "examples": [
          12345
        ]
      },
      "vc_mac": {
        "type": [
          "string",
          "null"
        ]
      },
      "version": {
        "type": "string",
        "examples": [
          "0.10.24362"
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
    }
  },
  "description": "",
  "examples": [
    [
      {
        "connected": true,
        "deviceprofile_name": "SJ1",
        "height": 2.7,
        "mac": "5c5b35000018",
        "map_id": "845a23bf-bed9-e43c-4c86-6fa474be7ae5",
        "model": "AP41",
        "name": "hallway",
        "orientation": 90,
        "serial": "FXLH2015150025",
        "site_name": "SJ1",
        "x": 150,
        "y": 300
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.installer.installer.listInstallerListOfRecentlyClaimedDevices()`

## Usage Context

Use this endpoint to list recently claimed devices visible to the installer. Common use cases:

- Viewing devices that have been claimed to the organization and are ready for provisioning
- Checking device status during field installation using the Mist mobile app

## Gotchas

- This is a simplified installer-scoped API -- it only shows recently claimed devices, not the full inventory
- Installer APIs use limited privileges compared to full admin APIs
- For a complete device inventory, use the full org inventory API instead

## Related Endpoints

- [POST_installer_orgs_org_id_devices.md](POST_installer_orgs_org_id_devices.md) -- Claim a new device
- [PUT_installer_orgs_org_id_devices_device_mac.md](PUT_installer_orgs_org_id_devices_device_mac.md) -- Provision or replace a device
- [DELETE_installer_orgs_org_id_devices_device_mac.md](DELETE_installer_orgs_org_id_devices_device_mac.md) -- Unassign a device
- [../orgs/GET_orgs_org_id_inventory.md](../orgs/GET_orgs_org_id_inventory.md) -- Full org inventory (admin API)

## MistHelper Notes

Not currently used by MistHelper. MistHelper uses the full admin-level inventory APIs instead.
