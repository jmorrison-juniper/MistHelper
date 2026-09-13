# searchSiteAssets

> searchSiteAssets

## HTTP

`GET /api/v1/sites/{site_id}/stats/assets/search`

## Description

Assets Search

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
| mac | string | No |  |  |  |
| map_id | string | No |  |  |  |
| ibeacon_uuid | string | No |  |  |  |
| ibeacon_major | integer | No |  |  |  |
| ibeacon_minor | integer | No |  |  |  |
| eddystone_uid_namespace | string | No |  |  |  |
| eddystone_uid_instance | string | No |  |  |  |
| eddystone_url | string | No |  |  |  |
| device_name | string | No |  |  |  |
| by | string | No |  |  |  |
| name | string | No |  |  |  |
| ap_mac | string | No |  |  |  |
| beam | string | No |  |  |  |
| rssi | string | No |  |  |  |
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

OK

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

`mistapi.api.v1.sites.stats_-_assets.searchSiteAssets()`

## Usage Context

Searches BLE asset statistics at a site with filtering by name, MAC, zone, map, and time range.

## Gotchas

- Uses cursor-based pagination. Check `next` for additional pages.
- Asset stats include position, RSSI, and battery level — requires BLE scanning enabled on APs.

## Related Endpoints

- [GET_sites_site_id_assets.md](GET_sites_site_id_assets.md) — List asset records
- [GET_sites_site_id_assetfilters.md](GET_sites_site_id_assetfilters.md) — Asset filter config

## MistHelper Notes

Not currently used by MistHelper directly.
