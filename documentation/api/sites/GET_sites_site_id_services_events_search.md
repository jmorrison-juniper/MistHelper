# searchSiteServicePathEvents

> searchSiteServicePathEvents

## HTTP

`GET /api/v1/sites/{site_id}/services/events/search`

## Description

Search Service Path Events

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
| type | string | No |  |  | Event type, e.g. GW_SERVICE_PATH_DOWN |
| text | string | No |  |  | Description of the event including the reason it is triggered |
| peer_port_id | string | No |  |  | Port ID of the peer gateway |
| peer_mac | string | No |  |  | MAC address of the peer gateway |
| vpn_name | string | No |  |  | Peer name |
| vpn_path | string | No |  |  | Peer path name |
| policy | string | No |  |  | Service policy associated with that specific path |
| port_id | string | No |  |  | Network interface |
| model | string | No |  |  | Device model |
| version | string | No |  |  | Device firmware version |
| timestamp | number | No |  |  | Start time, in epoch |
| mac | string | No |  |  | MAC address |
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
      "contentEncoding": "int32",
      "examples": [
        1697096379
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
        "title": "service_path_event",
        "type": "object",
        "properties": {
          "mac": {
            "type": "string",
            "examples": [
              "90ec7734b374"
            ]
          },
          "model": {
            "type": "string",
            "examples": [
              "SSR120"
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
          "policy": {
            "type": "string",
            "examples": [
              "INTERNET"
            ]
          },
          "port_id": {
            "type": "string",
            "examples": [
              "ge-1/0/6"
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
          "text": {
            "type": "string",
            "examples": [
              "Peer Path Down"
            ]
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "type": {
            "type": "string",
            "examples": [
              "GW_SERVICE_PATH_REMOVE"
            ]
          },
          "version": {
            "type": "string",
            "examples": [
              "6.1.5-14.lts"
            ]
          },
          "vpn_name": {
            "type": "string",
            "examples": [
              "Syracuse_HUB"
            ]
          },
          "vpn_path": {
            "type": "string",
            "examples": [
              "Syracuse_HUB-Wan0"
            ]
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1697009979
      ]
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        2
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

`mistapi.api.v1.sites.services.searchSiteServicePathEvents()`

## Usage Context

Searches service/application events at a site (policy hits, application classification events).

## Gotchas

- Uses cursor-based pagination.

## Related Endpoints

- [GET_sites_site_id_services_events_count.md](GET_sites_site_id_services_events_count.md) — Count events
- [GET_sites_site_id_servicepolicies_derived.md](GET_sites_site_id_servicepolicies_derived.md) — Derived policies

## MistHelper Notes

Not currently used by MistHelper directly.
