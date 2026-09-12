# listSiteRssiZonesStats

> listSiteRssiZonesStats

## HTTP

`GET /api/v1/sites/{site_id}/stats/rssizones`

## Description

Get List of Site RSSI Zones Stats

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "array",
  "items": {
    "title": "stats_rssi_zone",
    "required": [
      "devices",
      "id",
      "name"
    ],
    "type": "object",
    "properties": {
      "assets_wait": {
        "type": "object",
        "properties": {
          "avg": {
            "type": "number",
            "description": "Average wait time in seconds",
            "examples": [
              0
            ]
          },
          "max": {
            "type": "number",
            "description": "Longest wait time in seconds",
            "examples": [
              0
            ]
          },
          "min": {
            "type": "number",
            "description": "Shortest wait time in seconds",
            "examples": [
              0
            ]
          },
          "p95": {
            "type": "number",
            "description": "95th percentile of all the wait time(s)",
            "examples": [
              0
            ]
          }
        },
        "description": "BLE asset wait time right now"
      },
      "clients_wait": {
        "type": "object",
        "properties": {
          "avg": {
            "type": "number",
            "description": "Average wait time in seconds",
            "examples": [
              1200
            ]
          },
          "max": {
            "type": "number",
            "description": "Longest wait time in seconds",
            "examples": [
              3610
            ]
          },
          "min": {
            "type": "number",
            "description": "Shortest wait time in seconds",
            "examples": [
              600
            ]
          },
          "p95": {
            "type": "number",
            "description": "95th percentile of all the wait time(s)",
            "examples": [
              2800
            ]
          }
        },
        "description": "Client wait time right now"
      },
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "devices": {
        "type": "array",
        "items": {
          "title": "stats_rssi_zones_device",
          "type": "object",
          "properties": {
            "device_id": {
              "type": "string",
              "contentEncoding": "uuid"
            },
            "rssi": {
              "type": "integer",
              "contentEncoding": "int32"
            }
          }
        },
        "description": ""
      },
      "discovered_assets_wait": {
        "type": "object",
        "properties": {
          "avg": {
            "type": "number",
            "description": "Average wait time in seconds",
            "examples": [
              0
            ]
          },
          "max": {
            "type": "number",
            "description": "Longest wait time in seconds",
            "examples": [
              0
            ]
          },
          "min": {
            "type": "number",
            "description": "Shortest wait time in seconds",
            "examples": [
              0
            ]
          },
          "p95": {
            "type": "number",
            "description": "95th percentile of all the wait time(s)",
            "examples": [
              0
            ]
          }
        },
        "description": "Discovered asset wait time right now"
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
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "name": {
        "type": "string",
        "description": "Name of the zone",
        "examples": [
          "Zone A"
        ]
      },
      "num_assets": {
        "type": "integer",
        "description": "Number of assets",
        "contentEncoding": "int32",
        "examples": [
          0
        ]
      },
      "num_clients": {
        "type": "integer",
        "description": "Number of Wi-Fi clients (unconnected + connected)",
        "contentEncoding": "int32",
        "examples": [
          80
        ]
      },
      "num_discovered_assets": {
        "type": "integer",
        "description": "Number of discoveredassets",
        "contentEncoding": "int32",
        "examples": [
          0
        ]
      },
      "num_sdkclients": {
        "type": "integer",
        "description": "Number of sdk clients",
        "contentEncoding": "int32",
        "examples": [
          10
        ]
      },
      "num_unconnected_clients": {
        "type": "integer",
        "description": "Number of unconnected Wi-Fi clients",
        "contentEncoding": "int32",
        "examples": [
          80
        ]
      },
      "occupancy_limit": {
        "type": "integer",
        "contentEncoding": "int32",
        "examples": [
          4
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
      "sdkclients_wait": {
        "type": "object",
        "properties": {
          "avg": {
            "type": "number",
            "description": "Average wait time in seconds",
            "examples": [
              0
            ]
          },
          "max": {
            "type": "number",
            "description": "Longest wait time in seconds",
            "examples": [
              0
            ]
          },
          "min": {
            "type": "number",
            "description": "Shortest wait time in seconds",
            "examples": [
              0
            ]
          },
          "p95": {
            "type": "number",
            "description": "95th percentile of all the wait time(s)",
            "examples": [
              0
            ]
          }
        },
        "description": "SDK client wait time right now"
      },
      "site_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "441a1214-6928-442a-8e92-e1d34b8ec6a6"
        ]
      },
      "unconnected_clients_wait": {
        "type": "object",
        "properties": {
          "avg": {
            "type": "number",
            "description": "Average wait time in seconds",
            "examples": [
              0
            ]
          },
          "max": {
            "type": "number",
            "description": "Longest wait time in seconds",
            "examples": [
              0
            ]
          },
          "min": {
            "type": "number",
            "description": "Shortest wait time in seconds",
            "examples": [
              0
            ]
          },
          "p95": {
            "type": "number",
            "description": "95th percentile of all the wait time(s)",
            "examples": [
              0
            ]
          }
        },
        "description": "Unconnected Wi-Fi client wait time right now"
      }
    },
    "description": "Zone statistics"
  },
  "description": "",
  "examples": [
    [
      {
        "assets_wait": {
          "avg": 0,
          "max": 0,
          "min": 0,
          "p95": 0
        },
        "clients_wait": {
          "avg": 39259.333333333336,
          "max": 58361,
          "min": 12376,
          "p95": 58361
        },
        "created_time": 1733864928,
        "devices": [
          {
            "device_id": "00000000-0000-0000-1000-c8786708bb5d",
            "rssi": -70
          }
        ],
        "discovered_assets_wait": {
          "avg": 0,
          "max": 0,
          "min": 0,
          "p95": 0
        },
        "id": "17ef7169-e000-4dcd-abc7-f721f0a8ffda",
        "modified_time": 1733864928,
        "name": "proximity openspace",
        "num_assets": 0,
        "num_clients": 3,
        "num_discovered_assets": 0,
        "num_sdkclients": 0,
        "num_unconnected_clients": 7,
        "org_id": "c5fbc9e4-12bf-436e-98c4-1c842c66ab6c",
        "sdkclients_wait": {
          "avg": 0,
          "max": 0,
          "min": 0,
          "p95": 0
        },
        "site_id": "079fafd3-ef5c-4b23-90f0-9fcebec0023a",
        "unconnected_clients_wait": {
          "avg": 37552.857142857145,
          "max": 68342,
          "min": 6649,
          "p95": 68342
        }
      }
    ]
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

`mistapi.api.v1.sites.stats_-_zones.listSiteRssiZonesStats()`

## Usage Context

Retrieves statistics for all RSSI zones at a site, including current occupancy counts.

## Gotchas

- RSSI zone stats update in near real-time based on client signal strength measurements.

## Related Endpoints

- [GET_sites_site_id_stats_rssizones_zone_id.md](GET_sites_site_id_stats_rssizones_zone_id.md) — Specific RSSI zone stats
- [GET_sites_site_id_rssizones.md](GET_sites_site_id_rssizones.md) — RSSI zone config

## MistHelper Notes

Not currently used by MistHelper directly.
