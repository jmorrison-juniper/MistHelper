# searchOrgAssets

> searchOrgAssets

## HTTP

`GET /api/v1/orgs/{org_id}/stats/assets/search`

## Description

Search for Org Assets

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
| device_name | string | No |  |  |  |
| name | string | No |  |  |  |
| map_id | string | No |  |  |  |
| ibeacon_uuid | string | No |  |  |  |
| ibeacon_major | string | No |  |  |  |
| ibeacon_minor | string | No |  |  |  |
| eddystone_uid_namespace | string | No |  |  |  |
| eddystone_uid_instance | string | No |  |  |  |
| eddystone_url | string | No |  |  |  |
| ap_mac | string | No |  |  |  |
| beam | integer | No |  |  |  |
| rssi | integer | No |  |  |  |
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

`mistapi.api.v1.orgs.stats_-_assets.searchOrgAssets()`

## Usage Context

Searches for asset statistics across the organization.

## Gotchas

- Uses BLE-based asset tracking data.

## Related Endpoints

- [GET_orgs_org_id_stats_assets_count.md](GET_orgs_org_id_stats_assets_count.md) — Count assets
- [GET_orgs_org_id_stats_assets.md](GET_orgs_org_id_stats_assets.md) — List asset stats

## MistHelper Notes

Not currently used by MistHelper directly.
