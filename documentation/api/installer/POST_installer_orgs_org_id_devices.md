# claimInstallerDevices

> claimInstallerDevices

## HTTP

`POST /api/v1/installer/orgs/{org_id}/devices`

## Description

This mirrors `POST /api/v1/orgs/{org_id}/inventory` (see Inventory API)

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "uniqueItems": true,
  "type": "array",
  "items": {
    "type": "string"
  },
  "description": "Request Body",
  "examples": [
    [
      "6JG8E-PTFV2-A9Z2N",
      "DVH4V-SNMSZ-PDXBR"
    ]
  ]
}
```

## Response

### 200

OK - if any of entries are valid or there’s no errors

```json
{
  "type": "object",
  "properties": {
    "added": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "duplicated": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "error": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "inventory_added": {
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "response_inventory_inventory_added_items",
        "required": [
          "mac",
          "magic",
          "model",
          "serial",
          "type"
        ],
        "type": "object",
        "properties": {
          "mac": {
            "type": "string",
            "examples": [
              "5c5b35000018"
            ]
          },
          "magic": {
            "type": "string",
            "examples": [
              "6JG8EPTFV2A9Z2N"
            ]
          },
          "model": {
            "type": "string",
            "examples": [
              "AP41"
            ]
          },
          "serial": {
            "type": "string",
            "examples": [
              "FXLH2015150025"
            ]
          },
          "type": {
            "type": "string",
            "examples": [
              "ap"
            ]
          }
        }
      },
      "description": ""
    },
    "inventory_duplicated": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "response_inventory_inventory_duplicated_items",
        "required": [
          "mac",
          "magic",
          "model",
          "serial",
          "type"
        ],
        "type": "object",
        "properties": {
          "mac": {
            "type": "string",
            "examples": [
              "5c5b35000012"
            ]
          },
          "magic": {
            "type": "string",
            "examples": [
              "DVH4VSNMSZPDXBR"
            ]
          },
          "model": {
            "type": "string",
            "examples": [
              "AP41"
            ]
          },
          "serial": {
            "type": "string",
            "examples": [
              "FXLH2015150027"
            ]
          },
          "type": {
            "type": "string",
            "examples": [
              "ap"
            ]
          }
        }
      },
      "description": ""
    },
    "reason": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    }
  }
}
```

## Errors

| Status | Description |
|--------|-------------|
| 400 | OK - if any of entries are valid or there’s no errors |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.installer.installer.claimInstallerDevices()`

## Usage Context

Use this endpoint to claim a device to the organization. Common use cases:

- Claiming APs, switches, or gateways during field installation via the Mist mobile app
- Adding newly shipped devices to the organization inventory

## Gotchas

- This mirrors `POST /api/v1/orgs/{org_id}/inventory` -- the same operation is available through the full admin API
- Requires the device claim code or MAC address
- Devices must be unclaimed or released from a previous org before claiming

## Related Endpoints

- [GET_installer_orgs_org_id_devices.md](GET_installer_orgs_org_id_devices.md) -- List claimed devices after adding
- [PUT_installer_orgs_org_id_devices_device_mac.md](PUT_installer_orgs_org_id_devices_device_mac.md) -- Provision the claimed device
- [../orgs/POST_orgs_org_id_inventory.md](../orgs/POST_orgs_org_id_inventory.md) -- Full admin inventory claim API

## MistHelper Notes

Not currently used by MistHelper. MistHelper uses the full admin-level inventory APIs instead.
