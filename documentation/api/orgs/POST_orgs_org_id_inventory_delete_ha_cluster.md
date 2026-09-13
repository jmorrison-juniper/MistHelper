# deleteOrgGatewayHaCluster

> deleteOrgGatewayHaCluster

## HTTP

`POST /api/v1/orgs/{org_id}/inventory/delete_ha_cluster`

## Description

Delete HA Cluster

After HA cluster deleted, both of the nodes will be unassigned.

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
  "title": "ha_cluster_delete",
  "type": "object",
  "properties": {
    "mac": {
      "type": "string",
      "description": "Node0 mac address",
      "examples": [
        "aff827549235"
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

`mistapi.api.v1.orgs.inventory.deleteOrgGatewayHaCluster()`

## Usage Context

Deletes an HA cluster, separating the two gateway devices.

## Gotchas

- This disrupts gateway redundancy. Plan for a maintenance window.

## Related Endpoints

- [POST_orgs_org_id_inventory_create_ha_cluster.md](POST_orgs_org_id_inventory_create_ha_cluster.md) — Create HA cluster
- [GET_orgs_org_id_inventory.md](GET_orgs_org_id_inventory.md) — Inventory

## MistHelper Notes

Not currently used by MistHelper directly.
