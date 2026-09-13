# countSiteWanUsage

> countSiteWanUsage

## HTTP

`GET /api/v1/sites/{site_id}/wan_usages/count`

## Description

Count Site WAN Usages

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
| distinct | string | No |  |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| limit | integer | No | 100 |  |  |

## Request Body

None.

## Response

### 200

Result of Count

```json
{
  "type": "object",
  "properties": {
    "distinct": {
      "type": "string"
    },
    "end": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "count_result",
        "required": [
          "count"
        ],
        "type": "object",
        "properties": {
          "count": {
            "type": "integer",
            "contentEncoding": "int32"
          }
        },
        "additionalProperties": {
          "type": "string"
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
      "contentEncoding": "int32"
    }
  },
  "required": [
    "distinct",
    "end",
    "limit",
    "results",
    "start",
    "total"
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

`mistapi.api.v1.sites.wan_usages.countSiteWanUsage()`

## Usage Context

Returns the count of WAN usage records at a site.

## Gotchas

- Count only; use search endpoint for usage details.

## Related Endpoints

- [GET_sites_site_id_wan_usages_search.md](GET_sites_site_id_wan_usages_search.md) — Search WAN usage
- [GET_sites_site_id_wan_clients_search.md](GET_sites_site_id_wan_clients_search.md) — WAN clients

## MistHelper Notes

Not currently used by MistHelper directly.
