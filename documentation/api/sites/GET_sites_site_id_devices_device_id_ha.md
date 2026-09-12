# GetSiteDeviceHaClusterNode

> GetSiteDeviceHaClusterNode

## HTTP

`GET /api/v1/sites/{site_id}/devices/{device_id}/ha`

## Description

Delete HA Cluster

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| device_id | string | Yes |  |

## Request Body

None.

## Response

### 200

Ok

```json
{
  "type": "object",
  "properties": {
    "nodes": {
      "maxItems": 2,
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "gateway_cluster_node",
        "required": [
          "mac"
        ],
        "type": "object",
        "properties": {
          "mac": {
            "type": "string",
            "description": "Gateway MAC Address. Format is `[0-9a-f]{12}` (e.g. \"5684dae9ac8b\")"
          }
        }
      },
      "description": "When replacing a node, either mac has to remain the same as existing cluster"
    }
  },
  "required": [
    "nodes"
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

`mistapi.api.v1.sites.devices_-_wan_cluster.GetSiteDeviceHaClusterNode()`

## Usage Context

Retrieves the High Availability (HA) cluster configuration for a device (typically SRX gateways). Shows primary/secondary roles and failover status.

## Gotchas

- Only applicable to gateway devices configured in HA pairs.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_ha.md](POST_sites_site_id_devices_device_id_ha.md) — Configure HA
- [DELETE_sites_site_id_devices_device_id_ha.md](DELETE_sites_site_id_devices_device_id_ha.md) — Remove HA config

## MistHelper Notes

Not currently used by MistHelper directly.
