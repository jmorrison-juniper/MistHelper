# searchOrgInventory

> searchOrgInventory

## HTTP

`GET /api/v1/orgs/{org_id}/inventory/search`

## Description

Search in the Org Inventory

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
| mac | string | No |  |  | MAC address |
| vc_mac | string | No |  |  | Virtual Chassis MAC Address |
| master_mac | string | No |  |  | Master device mac for virtual mac cluster |
| site_id | string | No |  |  | Site id if assigned, null if not assigned |
| serial | string | No |  |  | Device serial |
| master | string | No |  |  | true / false |
| sku | string | No |  |  | Device sku |
| version | string | No |  |  | Device version |
| status | string | No |  |  | Device status |
| text | string | No |  |  | Wildcards for name, mac, serial |
| limit | integer | No | 100 |  |  |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1000
      ]
    },
    "next": {
      "type": "string"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "inventory_search_result",
        "type": "object",
        "properties": {
          "mac": {
            "type": "string",
            "examples": [
              "f01c2df166e0"
            ]
          },
          "master": {
            "type": "boolean",
            "examples": [
              true
            ]
          },
          "members": {
            "type": "array",
            "items": {
              "title": "inventory_search_result_member",
              "type": "object",
              "properties": {
                "mac": {
                  "type": "string",
                  "examples": [
                    "f01c2df166e0"
                  ]
                },
                "model": {
                  "type": "string",
                  "examples": [
                    "EX4300-48P"
                  ]
                },
                "serial": {
                  "type": "string",
                  "examples": [
                    "PD3714460200"
                  ]
                }
              }
            },
            "description": ""
          },
          "model": {
            "type": "string",
            "examples": [
              "EX4300-48P"
            ]
          },
          "name": {
            "type": "string",
            "examples": [
              "mist-wa-ex4300-VC"
            ]
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
            "examples": [
              "PD3714460200"
            ]
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
            "examples": [
              "EX4300-48P"
            ]
          },
          "status": {
            "type": "string",
            "examples": [
              "disconnected"
            ]
          },
          "type": {
            "type": "string",
            "description": "enum: `ap`, `gateway`, `switch`"
          },
          "vc_mac": {
            "type": "string",
            "examples": [
              "f01c2df166e0"
            ]
          },
          "version": {
            "type": "string",
            "examples": [
              "21.4R3.5"
            ]
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1
      ]
    }
  }
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

`mistapi.api.v1.orgs.inventory.searchOrgInventory()`

## Usage Context

Searches inventory items with filtering by model, serial, MAC, site, and more.

## Gotchas

- Supports pagination with `limit` and `page`.
- Unassigned devices have no site_id.

## Related Endpoints

- [GET_orgs_org_id_inventory_count.md](GET_orgs_org_id_inventory_count.md) — Count inventory
- [GET_orgs_org_id_inventory.md](GET_orgs_org_id_inventory.md) — Full inventory

## MistHelper Notes

Used by MistHelper via `getOrgInventory` in Menus 12, 17, 21, 22, 25, 61, 90, 99, 100, 110.
