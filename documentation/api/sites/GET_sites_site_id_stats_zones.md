# listSiteZonesStats

> listSiteZonesStats

## HTTP

`GET /api/v1/sites/{site_id}/stats/zones`

## Description

Get List of Site Zones Stats

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
| map_id | string | No |  |  |  |
| min_duration | integer | No |  |  |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "array",
  "items": {
    "title": "stats_zone",
    "required": [
      "id",
      "map_id",
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
      "map_id": {
        "type": "string",
        "description": "Map_id of the zone",
        "contentEncoding": "uuid",
        "examples": [
          "123449d4-d12f-4feb-b40f-5be0e2ae1234"
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
      },
      "vertices": {
        "type": "array",
        "items": {
          "title": "zone_vertex",
          "required": [
            "x",
            "y"
          ],
          "type": "object",
          "properties": {
            "x": {
              "type": "number",
              "description": "X in pixel"
            },
            "y": {
              "type": "number",
              "description": "Y in pixel"
            }
          }
        },
        "description": "Vertices used to define an area. It\u2019s assumed that the last point connects to the first point and forms an closed area",
        "examples": [
          [
            {
              "x": 732,
              "y": 1821
            },
            {
              "x": 732.5,
              "y": 1731
            },
            {
              "x": 837.5,
              "y": 1731.5
            },
            {
              "x": 839,
              "y": 1821
            }
          ]
        ]
      },
      "vertices_m": {
        "type": "array",
        "items": {
          "title": "zone_vertex_m",
          "required": [
            "x",
            "y"
          ],
          "type": "object",
          "properties": {
            "x": {
              "type": "number",
              "description": "X in pixel"
            },
            "y": {
              "type": "number",
              "description": "Y in pixel"
            }
          }
        },
        "description": "",
        "examples": [
          [
            {
              "x": 24.1983341951072,
              "y": 60.198314985369144
            },
            {
              "x": 24.21486311190714,
              "y": 57.22310996138056
            },
            {
              "x": 27.685935639893827,
              "y": 57.23963887818049
            },
            {
              "x": 27.73552239029364,
              "y": 60.198314985369144
            }
          ]
        ]
      }
    },
    "description": "Zone statistics"
  },
  "description": "",
  "examples": [
    "[{\"assets_wait\":{\"avg\":0,\"max\":0,\"min\":0,\"p95\":0},\"clients_wait\":{\"avg\":1200,\"max\":3610,\"min\":600,\"p95\":2800},\"created_time\":1616625211,\"id\":\"123470c7-5d9d-424a-8475-8b344c621234\",\"map_id\":\"123449d4-d12f-4feb-b40f-5be0e2ae1234\",\"modified_time\":1616625211,\"name\":\"Zone A\",\"num_assets\":0,\"num_clients\":80,\"num_sdkclients\":10,\"occupancy_limit\":4,\"org_id\":\"1234c1a0-6ef6-11e6-8bbf-02e208b21234\",\"sdkclients_wait\":{\"avg\":1200,\"max\":3610,\"min\":600,\"p95\":2800},\"site_id\":\"123448e6-6ef6-11e6-8bbf-02e208b21234\",\"vertices\":[{\"x\":732,\"y\":1821},{\"x\":732.5,\"y\":1731},{\"x\":837.5,\"y\":1731.5},{\"x\":839,\"y\":1821}],\"vertices_m\":[{\"x\":24.1983341951072,\"y\":60.198314985369144},{\"x\":24.21486311190714,\"y\":57.22310996138056},{\"x\":27.685935639893827,\"y\":57.23963887818049},{\"x\":27.73552239029364,\"y\":60.198314985369144}]}]",
    "[{\"created_time\":1616625211,\"id\":\"123470c7-5d9d-424a-8475-8b344c621234\",\"map_id\":\"123449d4-d12f-4feb-b40f-5be0e2ae1234\",\"modified_time\":1616625211,\"name\":\"Zone A\",\"occupancy_limit\":4,\"org_id\":\"1234c1a0-6ef6-11e6-8bbf-02e208b21234\",\"site_id\":\"123448e6-6ef6-11e6-8bbf-02e208b21234\",\"vertices\":[{\"x\":732,\"y\":1821},{\"x\":732.5,\"y\":1731},{\"x\":837.5,\"y\":1731.5},{\"x\":839,\"y\":1821}],\"vertices_m\":[{\"x\":24.1983341951072,\"y\":60.198314985369144},{\"x\":24.21486311190714,\"y\":57.22310996138056},{\"x\":27.685935639893827,\"y\":57.23963887818049},{\"x\":27.73552239029364,\"y\":60.198314985369144}]}]"
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

`mistapi.api.v1.sites.stats_-_zones.listSiteZonesStats()`

## Usage Context

Retrieves statistics for all zones at a site, including current occupancy counts and visit data.

## Gotchas

- Zone stats depend on location services being enabled and calibrated.

## Related Endpoints

- [GET_sites_site_id_stats_zones_zone_id.md](GET_sites_site_id_stats_zones_zone_id.md) — Specific zone stats
- [GET_sites_site_id_zones.md](GET_sites_site_id_zones.md) — Zone configuration

## MistHelper Notes

Not currently used by MistHelper directly.
