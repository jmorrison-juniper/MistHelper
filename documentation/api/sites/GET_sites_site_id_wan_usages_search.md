# searchSiteWanUsage

> searchSiteWanUsage

## HTTP

`GET /api/v1/sites/{site_id}/wan_usages/search`

## Description

Search Site WAN Usages

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| mac | string | No |  |  | MAC address |
| peer_mac | string | No |  |  | Peer MAC address |
| port_id | string | No |  |  | Port ID for the device |
| peer_port_id | string | No |  |  | Peer Port ID for the device |
| policy | string | No |  |  | Policy for the wan path |
| tenant | string | No |  |  | Tenant network in which the packet is sent |
| path_type | string | No |  |  | path_type of the port |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |

## Request Body

None.

## Response

### 200

OK

```json
{
  "title": "search_wan_usage",
  "type": "object",
  "properties": {
    "end": {
      "type": "number"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "wan_usages",
        "type": "object",
        "properties": {
          "mac": {
            "type": "string",
            "examples": [
              "5c5b35000001"
            ]
          },
          "path_type": {
            "type": "string",
            "examples": [
              "vpn"
            ]
          },
          "path_weight": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              10
            ]
          },
          "peer_mac": {
            "type": "string",
            "examples": [
              "0200018c95e1"
            ]
          },
          "peer_port_id": {
            "type": "string",
            "examples": [
              "ge-0/0/3"
            ]
          },
          "policy": {
            "type": "string",
            "examples": [
              "policy1"
            ]
          },
          "port_id": {
            "type": "string",
            "examples": [
              "ge-0/0/0.0"
            ]
          },
          "tenant": {
            "type": "string",
            "examples": [
              "tenant1"
            ]
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "number"
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

`mistapi.api.v1.sites.wan_usages.searchSiteWanUsage()`

## Usage Context

Searches WAN usage data at a site. Returns bandwidth utilization, application breakdown, and traffic flow data.

## Gotchas

- Uses cursor-based pagination. Time range filters are recommended for manageable result sets.

## Related Endpoints

- [GET_sites_site_id_wan_usages_count.md](GET_sites_site_id_wan_usages_count.md) — Usage count
- [GET_sites_site_id_wan_clients_search.md](GET_sites_site_id_wan_clients_search.md) — WAN clients

## MistHelper Notes

Not currently used by MistHelper directly.
