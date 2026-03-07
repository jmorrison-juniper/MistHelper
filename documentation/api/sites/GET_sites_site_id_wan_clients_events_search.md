# searchSiteWanClientEvents

> searchSiteWanClientEvents

## HTTP

`GET /api/v1/sites/{site_id}/wan_clients/events/search`

## Description

Search Site WAN Client Events

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
| type | string | No |  |  | See [List Device Events Definitions]($e/Constants%20Events/listDeviceEventsDefinitions) |
| mac | string | No |  |  | Partial / full MAC address |
| hostname | string | No |  |  | Partial / full hostname |
| ip | string | No |  |  | Client IP |
| mfg | string | No |  |  | Manufacture |
| nacrule_id | string | No |  |  | nacrule_id |
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
      "title": "events_client_wan",
      "type": "object",
      "properties": {
        "When": {
          "type": "string",
          "examples": [
            "2022-12-31 23:59:59.293000+00:00"
          ]
        },
        "ev_type": {
          "type": "string",
          "examples": [
            "CLIENT_IP_ASSIGNED"
          ]
        },
        "metadata": {
          "type": "object"
        },
        "org_id": {
          "type": "string",
          "contentEncoding": "uuid",
          "readOnly": true,
          "examples": [
            "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
          ]
        },
        "random_mac": {
          "type": "boolean"
        },
        "site_id": {
          "type": "string",
          "contentEncoding": "uuid",
          "readOnly": true,
          "examples": [
            "441a1214-6928-442a-8e92-e1d34b8ec6a6"
          ]
        },
        "text": {
          "type": "string",
          "examples": [
            "DHCP Ack IP 192.168.88.216"
          ]
        },
        "wcid": {
          "type": "string",
          "contentEncoding": "uuid",
          "examples": [
            "62bbfb75-10d8-49d1-dec7-d2df91624287"
          ]
        }
      }
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

`mistapi.api.v1.sites.clients_-_wan.searchSiteWanClientEvents()`

## Usage Context

Searches WAN client events at a site. Shows session creation, teardown, and policy events for LAN-side clients.

## Gotchas

- Uses cursor-based pagination.

## Related Endpoints

- [GET_sites_site_id_wan_client_events_count.md](GET_sites_site_id_wan_client_events_count.md) — Event count
- [GET_sites_site_id_wan_clients_search.md](GET_sites_site_id_wan_clients_search.md) — Search WAN clients

## MistHelper Notes

Not currently used by MistHelper directly.
