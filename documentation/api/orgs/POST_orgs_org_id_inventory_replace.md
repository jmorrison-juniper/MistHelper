# replaceOrgDevices

> replaceOrgDevices

## HTTP

`POST /api/v1/orgs/{org_id}/inventory/replace`

## Description

It’s a common request we get from the customers. When a AP HW has problem and need a replacement, they would want to copy the existing attributes (Device Config) of this old AP to the new one. It can be done by providing the MAC of a device that’s currently in the inventory but not assigned. The Device replaced will become unassigned.

This API also supports replacement of Mist Edges. This API copies device agnostic attributes from old Mist edge to new one.
Mist manufactured Mist Edges will be reset to factory settings but will still be in Inventory.Brownfield or VM’s will be
deleted from Inventory

**Note:** For Gateway devices only like-for-like replacements (can only replace a SRX320 with a SRX320 and not some other model) are allowed.

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
    "discard": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Attributes that you don\u2019t want to copy"
    },
    "inventory_mac": {
      "type": "string",
      "description": "MAC Address of the inventory that will be replacing the old one. It has to be claimed and unassigned",
      "examples": [
        "5c5b35000301"
      ]
    },
    "mac": {
      "type": "string",
      "description": "MAC Address of the device to replace",
      "examples": [
        "5c5b35000101"
      ]
    },
    "site_id": {
      "type": "string",
      "description": "Site_id of the device to be replaced",
      "examples": [
        "4ac1dcf4-9d8b-7211-65c4-057819f0862b"
      ]
    },
    "tunterm_port_config": {
      "type": "object",
      "properties": {
        "downstream_ports": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of ports to be used for downstream (to AP) purpose",
          "examples": [
            [
              "2",
              "3"
            ]
          ]
        },
        "separate_upstream_downstream": {
          "type": "boolean",
          "description": "Whether to separate upstream / downstream ports. default is false where all ports will be used.",
          "default": false
        },
        "upstream_port_vlan_id": {
          "type": "object",
          "description": "Native VLAN id for upstream ports"
        },
        "upstream_ports": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of ports to be used for upstream purpose (to LAN)",
          "examples": [
            [
              "0",
              "1"
            ]
          ]
        }
      },
      "description": "Ethernet port configurations"
    }
  },
  "description": "Request Body"
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

`mistapi.api.v1.orgs.inventory.replaceOrgDevices()`

## Usage Context

Replaces a device in the inventory with a new one, transferring configuration.

## Gotchas

- The replacement device must be claimed first.
- Configuration is copied from the old device to the new one.

## Related Endpoints

- [POST_orgs_org_id_claim.md](POST_orgs_org_id_claim.md) — Claim devices
- [GET_orgs_org_id_inventory.md](GET_orgs_org_id_inventory.md) — Inventory

## MistHelper Notes

Not currently used by MistHelper directly.
