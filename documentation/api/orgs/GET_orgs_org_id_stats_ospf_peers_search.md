# searchOrgOspfStats

> searchOrgOspfStats

## HTTP

`GET /api/v1/orgs/{org_id}/stats/ospf_peers/search`

## Description

Search OSPF Neighbor Stats

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
| site_id | string | No |  |  |  |
| mac | string | No |  |  |  |
| vrf_name | string | No |  |  |  |
| peer_ip | string | No |  |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
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
  "title": "ospf_peer_stats_search_result",
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1711035686
      ]
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        10
      ]
    },
    "next": {
      "type": "string"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "ospf_peer_stats_search_results_items",
        "type": "object",
        "properties": {
          "dead_time": {
            "type": "integer",
            "description": "Activity timer",
            "contentEncoding": "int32"
          },
          "mac": {
            "type": "string",
            "description": "Router MAC address"
          },
          "org_id": {
            "type": "string",
            "description": "Router org ID",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "peer_ip": {
            "type": "string",
            "description": "Neighbor address (IP)"
          },
          "port_id": {
            "type": "string",
            "description": "Interface name"
          },
          "priority": {
            "maximum": 255.0,
            "minimum": 0.0,
            "type": "integer",
            "description": "Neighbor priority, 0-255",
            "contentEncoding": "int32"
          },
          "site_id": {
            "type": "string",
            "description": "Router site ID",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "state": {
            "type": "string",
            "description": "Eg. full, down, 2way, init, exstart, exchange, loading"
          },
          "timestamp": {
            "type": "number",
            "description": "Sampling time (in epoch seconds)",
            "readOnly": true
          },
          "up": {
            "type": "boolean",
            "description": "True if state is full"
          },
          "vrf_name": {
            "type": "string",
            "description": "Instance name, e.g. master"
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1710949286
      ]
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        232
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

`mistapi.api.v1.orgs.stats_-_ospf.searchOrgOspfStats()`

## Usage Context

Searches for OSPF peer statistics across the organization.

## Gotchas

- Can filter by state (full, init, 2way, etc.).

## Related Endpoints

- [GET_orgs_org_id_stats_ospf_peers_count.md](GET_orgs_org_id_stats_ospf_peers_count.md) — Count OSPF peers
- [GET_orgs_org_id_stats_devices.md](GET_orgs_org_id_stats_devices.md) — Device stats

## MistHelper Notes

Not currently used by MistHelper directly.
