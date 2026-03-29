# searchOrgWanClients

> searchOrgWanClients

## HTTP

`GET /api/v1/orgs/{org_id}/wan_clients/search`

## Description

Search Org WAN Clients

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
| site_id | string | No |  |  | Site ID |
| mac | string | No |  |  | Partial / full MAC address |
| hostname | string | No |  |  | Partial / full hostname |
| ip | string | No |  |  | Client IP |
| network | string | No |  |  | Network |
| ip_src | string | No |  |  | IP source |
| mfg | string | No |  |  | Manufacture |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

## Request Body

None.

## Response

### 200

Example response

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
      "contentEncoding": "int32"
    },
    "next": {
      "type": "string"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "stats_wan_client",
        "type": "object",
        "properties": {
          "dhcp_expire_time": {
            "type": "number"
          },
          "dhcp_start_time": {
            "type": "number"
          },
          "hostname": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          },
          "ip": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          },
          "ip_src": {
            "type": "string",
            "examples": [
              "dhcp"
            ]
          },
          "last_hostname": {
            "type": "string",
            "examples": [
              "sonoszp"
            ]
          },
          "last_ip": {
            "type": "string",
            "examples": [
              "192.168.1.139"
            ]
          },
          "mfg": {
            "type": "string",
            "examples": [
              "Sonos"
            ]
          },
          "network": {
            "type": "string",
            "examples": [
              "lan"
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
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "wcid": {
            "type": "string",
            "examples": [
              "8bbe7389-212b-c65d-2208-00fab2017936"
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
      "contentEncoding": "int32"
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

`mistapi.api.v1.orgs.clients_-_wan.searchOrgWanClients()`

## Usage Context

Searches for WAN clients across the organization.

## Gotchas

- Can filter by hostname, ip, mac, and site_id.

## Related Endpoints

- [GET_orgs_org_id_wan_clients_count.md](GET_orgs_org_id_wan_clients_count.md) — Count WAN clients
- [GET_orgs_org_id_wan_clients_events_search.md](GET_orgs_org_id_wan_clients_events_search.md) — WAN client events

## MistHelper Notes

Not currently used by MistHelper directly.
