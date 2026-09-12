# listSiteAssetsStats

> listSiteAssetsStats

## HTTP

`GET /api/v1/sites/{site_id}/stats/assets`

## Description

Get List of Site Assets Stats

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
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "array",
  "items": {
    "title": "stats_asset",
    "required": [
      "mac"
    ],
    "type": "object",
    "properties": {
      "battery_voltage": {
        "type": "number",
        "description": "Battery voltage, in mV",
        "examples": [
          2970
        ]
      },
      "beam": {
        "type": "integer",
        "contentEncoding": "int32",
        "examples": [
          6
        ]
      },
      "device_name": {
        "type": "string",
        "examples": [
          "a"
        ]
      },
      "duration": {
        "type": "integer",
        "contentEncoding": "int32",
        "examples": [
          120
        ]
      },
      "eddystone_uid_instance": {
        "type": "string",
        "examples": [
          "5c5b35000001"
        ]
      },
      "eddystone_uid_namespace": {
        "type": "string",
        "examples": [
          "2818e3868dec25629ede"
        ]
      },
      "eddystone_url_url": {
        "type": "string",
        "examples": [
          "https://www.abc.com"
        ]
      },
      "ibeacon_major": {
        "maximum": 65535.0,
        "minimum": 1.0,
        "type": [
          "integer",
          "null"
        ],
        "description": "Major number for iBeacon",
        "contentEncoding": "int32",
        "examples": [
          1234
        ]
      },
      "ibeacon_minor": {
        "maximum": 65535.0,
        "minimum": 1.0,
        "type": [
          "integer",
          "null"
        ],
        "description": "Minor number for iBeacon",
        "contentEncoding": "int32",
        "examples": [
          1234
        ]
      },
      "ibeacon_uuid": {
        "type": [
          "string",
          "null"
        ],
        "contentEncoding": "uuid",
        "examples": [
          "f3f17139-704a-f03a-2786-0400279e37c3"
        ]
      },
      "last_seen": {
        "type": [
          "number",
          "null"
        ],
        "description": "Last seen timestamp",
        "readOnly": true,
        "examples": [
          1470417522
        ]
      },
      "mac": {
        "type": "string",
        "description": "Bluetooth MAC",
        "examples": [
          "6fa474be7ae5"
        ]
      },
      "map_id": {
        "type": "string",
        "description": "Map where the device belongs to",
        "contentEncoding": "uuid",
        "examples": [
          "c45be59f-854d-4ef7-b782-dcd6309c84a9"
        ]
      },
      "name": {
        "type": "string",
        "description": "Name / label of the device",
        "examples": [
          "6fa474be7ae5"
        ]
      },
      "rssi": {
        "type": "integer",
        "contentEncoding": "int32",
        "examples": [
          -60
        ]
      },
      "rssizones": {
        "type": "array",
        "items": {
          "title": "asset_rssi_zone",
          "type": "object",
          "properties": {
            "id": {
              "type": "string",
              "description": "Unique ID of the object instance in the Mist Organization",
              "contentEncoding": "uuid",
              "readOnly": true,
              "examples": [
                "53f10664-3ce8-4c27-b382-0ef66432349f"
              ]
            },
            "since": {
              "type": "number"
            }
          }
        },
        "description": "Only send this for individual asset stat"
      },
      "temperature": {
        "type": "number",
        "examples": [
          23
        ]
      },
      "x": {
        "type": "number",
        "description": "X in pixel",
        "examples": [
          280.19918140310193
        ]
      },
      "y": {
        "type": "number",
        "description": "Y in pixel",
        "examples": [
          420.2987721046529
        ]
      },
      "zones": {
        "type": "array",
        "items": {
          "title": "asset_zone",
          "type": "object",
          "properties": {
            "id": {
              "type": "string",
              "description": "Unique ID of the object instance in the Mist Organization",
              "contentEncoding": "uuid",
              "readOnly": true,
              "examples": [
                "53f10664-3ce8-4c27-b382-0ef66432349f"
              ]
            },
            "since": {
              "type": "number"
            }
          }
        },
        "description": "Only send this for individual asset stat"
      }
    },
    "description": "Asset statistics"
  },
  "description": "",
  "examples": [
    [
      {
        "battery_voltage": 0,
        "eddystone_uid_instance": "string",
        "eddystone_uid_namespace": "string",
        "eddystone_url_url": "string",
        "ibeacon_major": 1,
        "ibeacon_minor": 1,
        "ibeacon_uuid": "1f89bc00-d0af-481b-82fe-a6629259a39f",
        "last_seen": 0,
        "mac": "string",
        "map_id": "09d2b626-2e4e-45ef-a3c4-e6aeb6c83db1",
        "name": "string",
        "rssizones": [
          {
            "id": "478f6eca-6276-4993-bfeb-5bcbbbbacf08",
            "since": 0
          }
        ],
        "x": 0,
        "y": 0,
        "zones": [
          {
            "id": "477f6eca-6276-4993-bfeb-5ccbbbbadf08",
            "since": 0
          }
        ]
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.stats_-_assets.listSiteAssetsStats()`

## Usage Context

Retrieves statistics for all BLE assets at a site, including location and signal data.

## Gotchas

- Only returns data for assets that have been detected recently.

## Related Endpoints

- [GET_sites_site_id_stats_assets_asset_id.md](GET_sites_site_id_stats_assets_asset_id.md) — Specific asset stats
- [GET_sites_site_id_stats_assets_count.md](GET_sites_site_id_stats_assets_count.md) — Asset count

## MistHelper Notes

Not currently used by MistHelper directly.
