# getSiteZoneStats

> getSiteZoneStats

## HTTP

`GET /api/v1/sites/{site_id}/stats/zones/{zone_id}`

## Description

Get Detail Zone Stats

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| zone_id | string | Yes |  |

## Request Body

None.

## Response

### 200

Zone Stats

```json
{
  "type": "object",
  "properties": {
    "assets": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of ble assets currently in the zone and when they entered"
    },
    "client_waits": {
      "type": "object",
      "properties": {
        "avg": {
          "type": "integer",
          "description": "Average wait time in seconds",
          "contentEncoding": "int32",
          "examples": [
            1200
          ]
        },
        "max": {
          "type": "integer",
          "description": "Longest wait time in seconds",
          "contentEncoding": "int32",
          "examples": [
            3610
          ]
        },
        "min": {
          "type": "integer",
          "description": "Shortest wait time in seconds",
          "contentEncoding": "int32",
          "examples": [
            600
          ]
        },
        "p95": {
          "type": "integer",
          "description": "95th percentile of all the wait time(s)",
          "contentEncoding": "int32",
          "examples": [
            2800
          ]
        }
      },
      "required": [
        "avg",
        "max",
        "min",
        "p95"
      ],
      "description": "Client wait time right now"
    },
    "clients": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of clients currently in the zone and when they entered"
    },
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    },
    "map_id": {
      "type": "string",
      "description": "Map_id of the zone",
      "contentEncoding": "uuid",
      "examples": [
        "63eda950-c6da-11e4-a628-60f81dd250cc"
      ]
    },
    "name": {
      "type": "string",
      "description": "Name of the zone",
      "examples": [
        "Board Room"
      ]
    },
    "num_clients": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        80
      ]
    },
    "num_sdkclients": {
      "type": "integer",
      "description": "SDK client wait time right now",
      "contentEncoding": "int32",
      "examples": [
        0
      ]
    },
    "sdkclients": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of SDK Clients currently in the zone and when they entered"
    }
  },
  "required": [
    "client_waits",
    "id",
    "map_id",
    "name",
    "num_clients",
    "num_sdkclients"
  ],
  "description": "Zone details statistics"
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

`mistapi.api.v1.sites.stats_-_zones.getSiteZoneStats()`

## Usage Context

Retrieves statistics for a specific zone, including current occupancy, average dwell time, and visit counts.

## Gotchas

- No known gotchas.

## Related Endpoints

- [GET_sites_site_id_stats_zones.md](GET_sites_site_id_stats_zones.md) — All zone stats
- [GET_sites_site_id_zones_zone_id.md](GET_sites_site_id_zones_zone_id.md) — Zone config

## MistHelper Notes

Not currently used by MistHelper directly.
