# createSiteVirtualChassis

> createSiteVirtualChassis

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/vc`

## Description

For models (e.g. EX3400 and up) having dedicated VC ports, it is easier to form a VC by just connecting cables with the dedicated VC ports. Cloud will detect the new VC and update the inventory.  
In case that the user would like to choose the dedicated switch as a VC master or for EX2300-C-12P and EX2300-C-12T which doesn't have dedicated VC ports, below are procedures to automate the VC creation:
1. Power on the switch that is chosen as the VC master first, and then powering on the other member switches.
2. Claim or adopt all these switches under the same organization's Inventory
3. Assign these switches into the same Site
4. Wait for all the switches to be connected to Mist
5. Invoke vc command on the switch chosen to be the VC master. For EX2300-C-12P, VC ports will be created automatically.
6. Connect the cables to the VC ports for these switches
7. Wait for the VC to be formed. The Org's inventory will be updated for the new VC.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| device_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "locating": {
      "type": "boolean",
      "readOnly": true
    },
    "members": {
      "type": "array",
      "items": {
        "title": "virtual_chassis_config_member",
        "required": [
          "mac",
          "vc_role"
        ],
        "type": "object",
        "properties": {
          "locating": {
            "type": "boolean",
            "readOnly": true
          },
          "mac": {
            "type": "string",
            "description": "fpc0, same as the mac of device_id"
          },
          "member_id": {
            "type": "integer",
            "description": "For preprovisionned virtual chassis",
            "contentEncoding": "int32"
          },
          "vc_ports": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          },
          "vc_role": {
            "type": "string",
            "description": "enum: `backup`, `linecard`, `master`"
          }
        }
      },
      "description": ""
    },
    "preprovisioned": {
      "type": "boolean",
      "description": "To create the Virtual Chassis in Pre-Provisioned mode",
      "default": false
    }
  },
  "description": "Request Body"
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

`mistapi.api.v1.sites.devices_-_wired_-_virtual_chassis.createSiteVirtualChassis()`

## Usage Context

Performs Virtual Chassis operations on a switch (form VC, add/remove members, set roles).

## Gotchas

- VC operations are destructive and cause switch reboots. Requires explicit user confirmation.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_vc_convert_to_virtualmac.md](POST_sites_site_id_devices_device_id_vc_convert_to_virtualmac.md) — Convert to VMAC
- [GET_sites_site_id_devices_device_id_vc.md](GET_sites_site_id_devices_device_id_vc.md) — Get VC status

## MistHelper Notes

Used by Menus **94, 95, 96** (VC Conversion) for forming and managing virtual chassis.
