# updateOrgInventoryAssignment

> updateOrgInventoryAssignment

## HTTP

`PUT /api/v1/orgs/{org_id}/inventory`

## Description

Update Org Inventory

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
  "type": "object",
  "properties": {
    "disable_auto_config": {
      "type": "boolean",
      "description": "If `op`==`assign`, this disables the default behavior of a cloud-ready switch/gateway being managed/configured by Mist. Setting this to `true` means you want to disable the default behavior and do not want the device to be Mist-managed.",
      "default": false,
      "deprecated": true
    },
    "macs": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "If `op`==`assign`, `op`==`unassign`, `op`==`upgrade_to_mist`or `op`==`downgrade_to_jsi` , list of MAC, e.g. [\"5c5b350e0001\"]"
    },
    "managed": {
      "type": "boolean",
      "description": "If `op`==`assign`. An adopted switch/gateway will not be managed/configured by Mist by default. Setting this parameter to `true` enables the adopted switch/gateway to be managed/configured by Mist.",
      "default": false,
      "deprecated": true
    },
    "mist_configured": {
      "type": "boolean",
      "description": "whether the device can be configured by Mist or not. This deprecates `managed` (for adopted device) and `disable_auto_config` for claimed device)"
    },
    "no_reassign": {
      "type": "boolean",
      "description": "If `op`==`assign`, if true, treat site assignment against an already assigned AP as error",
      "default": false
    },
    "op": {
      "type": "string",
      "description": "enum:\n  * `upgrade_to_mist`: Upgrade to mist-managed\n  * `downgrade_to_jsi`: Downgrade to basic monitoring. When downgrading a VC member to jsi, we will move the cloud connection of the VC to jsi-terminator and keep all VC device/inventories intact for pain-free upgrading back to mist.\n  * `assign`: Assign inventory to a site\n  * `unassign`: Unassign inventory from a site\n  * `delete`: Delete multiple inventory from org. If the device is already assigned to a site, it will be unassigned"
    },
    "serials": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "If `op`==`delete`, list of serial numbers, e.g. [\"FXLH2015150025\"]"
    },
    "site_id": {
      "type": "string",
      "description": "If `op`==`assign`, target site id",
      "contentEncoding": "uuid"
    }
  },
  "required": [
    "op"
  ]
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "error": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "op": {
      "type": "string",
      "description": "enum: `assign`, `delete`, `downgrade_to_jsi`, `unassign`, `upgrade_to_mist`"
    },
    "reason": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "success": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    }
  },
  "required": [
    "error",
    "op",
    "reason",
    "success"
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

`mistapi.api.v1.orgs.inventory.updateOrgInventoryAssignment()`

## Usage Context

Updates inventory device assignments (site, name, etc.) in bulk.

## Gotchas

- Reassigning devices to a new site triggers a config push.
- Use `type=all` to include switches and gateways.

## Related Endpoints

- [GET_orgs_org_id_inventory.md](GET_orgs_org_id_inventory.md) — Get inventory
- [POST_orgs_org_id_inventory.md](POST_orgs_org_id_inventory.md) — Claim/add inventory

## MistHelper Notes

Inventory listing uses Menu 11 (`getOrgInventory`). Update is used in device assignment operations.
