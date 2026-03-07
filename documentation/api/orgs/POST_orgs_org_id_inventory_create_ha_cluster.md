# createOrgGatewayHaCluster

> createOrgGatewayHaCluster

## HTTP

`POST /api/v1/orgs/{org_id}/inventory/create_ha_cluster`

## Description

Create HA Cluster from unassigned Gateways

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
      "description": "This disables the default behavior of a cloud-ready switch/gateway being managed/configured by Mist. Setting this to `true` means you want to disable the default behavior and do not want the device to be Mist-managed.",
      "deprecated": true
    },
    "managed": {
      "type": "boolean",
      "description": "An adopted switch/gateway will not be managed/configured by Mist by default. Setting this parameter to `true` enables the adopted switch/gateway to be managed/configured by Mist.",
      "deprecated": true
    },
    "mist_configured": {
      "type": "boolean",
      "description": "whether the device can be configured by Mist or not. This deprecates `managed` (for adopted device) and `disable_auto_config` for claimed device)"
    },
    "nodes": {
      "type": "array",
      "items": {
        "title": "ha_cluster_config_node",
        "maxProperties": 2,
        "type": "object",
        "properties": {
          "mac": {
            "type": "string",
            "description": "Node mac, should be unassigned",
            "examples": [
              "aff827549235"
            ]
          }
        }
      },
      "description": ""
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "examples": [
        "43e9c864-a7e4-4310-8031-d9817d2c5a43"
      ]
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

`mistapi.api.v1.orgs.inventory.createOrgGatewayHaCluster()`

## Usage Context

Creates an HA (High Availability) cluster from two gateway devices.

## Gotchas

- Both devices must be the same model and in the same site.
- This is a destructive operation that reconfigures both devices.

## Related Endpoints

- [POST_orgs_org_id_inventory_delete_ha_cluster.md](POST_orgs_org_id_inventory_delete_ha_cluster.md) — Delete HA cluster
- [GET_orgs_org_id_inventory.md](GET_orgs_org_id_inventory.md) — Inventory

## MistHelper Notes

Not currently used by MistHelper directly.
