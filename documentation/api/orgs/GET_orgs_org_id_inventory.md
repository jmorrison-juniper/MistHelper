# getOrgInventory

> getOrgInventory

## HTTP

`GET /api/v1/orgs/{org_id}/inventory`

## Description

Get Org Inventory

### VC (Virtual-Chassis) Management 

Starting with the April release, Virtual Chassis devices in Mist will now use
a cloud-assigned virtual MAC address as the device ID, instead of the physical
MAC address of the FPC0 member.


**Retrieving the device ID or Site ID of a Virtual Chassis:**

1. Use this API call with the query parameters `vc=true` and `mac` set to the MAC address of the VC member.

2. In the response, check the `vc_mac` and `mac` fields:

    - If `vc_mac` is empty or not present, the device is not part of a Virtual Chassis.
    The `device_id` and `site_id` will be available in the device information.

    - If `vc_mac` differs from the `mac` field, the device is part of a Virtual Chassis
    but is not the device used to generate the Virtual Chassis ID. Use the `vc_mac` value with the [Get Org Inventory]($e/Orgs%20Inventory/getOrgInventory)
    API call to retrieve the `device_id` and `site_id`.

    - If `vc_mac` matches the `mac` field, the device is the device used to generate the Virtual Chassis ID and he `device_id` and `site_id` will be available
    in the device information.  
    This is the case if the device is the Virtual Chassis "virtual device" (MAC starting with `020003`) or if the device is the Virtual Chassis FPC0 and the Virtual Chassis is still using the FPC0 MAC address to generate the device ID.


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
| serial | string | No |  |  | Device serial |
| model | string | No |  |  | Device model |
| type | string | No |  |  |  |
| mac | string | No |  |  | MAC address |
| site_id | string | No |  |  | Site id if assigned, null if not assigned |
| vc_mac | string | No |  |  | Virtual Chassis MAC Address |
| vc | boolean | No | False |  | To display Virtual Chassis members |
| unassigned | boolean | No | True |  | To display Unassigned devices |
| modified_after | integer | No |  |  | Filter on inventory last modified time, in epoch |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "array",
  "items": {
    "title": "inventory",
    "type": "object",
    "properties": {
      "adopted": {
        "type": "boolean",
        "description": "Only if `type`==`switch` or `type`==`gateway`, whether the switch/gateway is adopted"
      },
      "chassis_mac": {
        "type": "string",
        "description": "For Virtual Chassis only, the MAC Address of the FPC0"
      },
      "chassis_serial": {
        "type": "string",
        "description": "For Virtual Chassis only, the Serial Number of the FPC0"
      },
      "connected": {
        "type": "boolean",
        "description": "Whether the device is connected"
      },
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "deviceprofile_id": {
        "type": [
          "string",
          "null"
        ],
        "description": "Deviceprofile id if assigned, null if not assigned"
      },
      "hostname": {
        "type": "string",
        "description": "Hostname reported by the device"
      },
      "hw_rev": {
        "type": "string",
        "description": "Device hardware revision number"
      },
      "id": {
        "type": "string",
        "description": "Unique ID of the object instance in the Mist Organization",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "53f10664-3ce8-4c27-b382-0ef66432349f"
        ]
      },
      "jsi": {
        "type": "boolean"
      },
      "mac": {
        "type": "string",
        "description": "Device MAC address"
      },
      "magic": {
        "type": "string",
        "description": "Device claim code"
      },
      "model": {
        "type": "string",
        "description": "Device model"
      },
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "name": {
        "type": "string",
        "description": "Device name if configured"
      },
      "org_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
        ]
      },
      "serial": {
        "type": "string",
        "description": "Device serial"
      },
      "site_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "441a1214-6928-442a-8e92-e1d34b8ec6a6"
        ]
      },
      "sku": {
        "type": "string",
        "description": "Device stock keeping unit"
      },
      "type": {
        "type": "string",
        "description": "enum: `ap`, `gateway`, `switch`"
      },
      "vc_mac": {
        "type": "string",
        "description": "If `type`==`switch` and device part of a Virtual Chassis, MAC Address of the Virtual Chassis. if `type`==`gateway` and device part of a Cluster, MAC Address of the Cluster"
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "connected": true,
        "created_time": 1542328276,
        "deviceprofile_id": "6f4bf402-45f9-2a56-6c8b-7f83d3bc98e9",
        "id": "00000000-0000-0000-0000-5c5b35000018",
        "mac": "5c5b35000018",
        "model": "AP41",
        "modified_time": 1542829778,
        "name": "hallway",
        "serial": "FXLH2015150025",
        "site_id": "4ac1dcf4-9d8b-7211-65c4-057819f0862b",
        "type": "ap"
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

`mistapi.api.v1.orgs.inventory.getOrgInventory()`

## Usage Context

Retrieves the full organization inventory of claimed devices.

## Gotchas

- Returns ALL device types (APs, switches, gateways).
- Large inventories should use search/count endpoints instead.

## Related Endpoints

- [GET_orgs_org_id_inventory_search.md](GET_orgs_org_id_inventory_search.md) — Search inventory
- [POST_orgs_org_id_inventory.md](POST_orgs_org_id_inventory.md) — Manage inventory

## MistHelper Notes

Used by MistHelper via `getOrgInventory` in Menus 12, 17, 21, 22, 25, 61, 90, 99, 100, 110.
