# getSiteSdkStatsByMap

> getSiteSdkStatsByMap

## HTTP

`GET /api/v1/sites/{site_id}/stats/maps/{map_id}/sdkclients`

## Description

Get SdkClient Stats By Map

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| map_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "array",
  "items": {
    "title": "stats_sdkclient",
    "required": [
      "id",
      "network_connection",
      "uuid"
    ],
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
      "map_id": {
        "type": [
          "string",
          "null"
        ],
        "description": "Map_id of the sdk client (if known), or null",
        "contentEncoding": "uuid",
        "examples": [
          "845a23bf-bed9-e43c-4c86-6fa474be7ae5"
        ]
      },
      "name": {
        "type": "string",
        "description": "Name of the sdk client (if provided)",
        "examples": [
          "John's iPhone"
        ]
      },
      "network_connection": {
        "type": "object",
        "properties": {
          "mac": {
            "type": "string"
          },
          "rssi": {
            "type": "number"
          },
          "signal_level": {
            "type": "number"
          },
          "type": {
            "type": "string"
          }
        },
        "required": [
          "mac",
          "rssi",
          "signal_level",
          "type"
        ],
        "description": "Various network connection info for the SDK client (if known, else omitted), with RSSI in dBm, and signal level as"
      },
      "uuid": {
        "type": "string",
        "description": "UUID of the sdk client",
        "contentEncoding": "uuid",
        "examples": [
          "ada72f8f-1643-e5c6-94db-f2a5636f1a64"
        ]
      },
      "x": {
        "type": "number",
        "description": "X (in pixels) of user location on the map (if known)",
        "examples": [
          60
        ]
      },
      "y": {
        "type": "number",
        "description": "Y (in pixels) of user location on the map (if known)",
        "examples": [
          80
        ]
      }
    },
    "description": "SDK Client statistics"
  },
  "description": ""
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

`mistapi.api.v1.sites.stats_-_clients_sdk.getSiteSdkStatsByMap()`

## Usage Context

Retrieves SDK client (mobile app) locations on a specific map/floor.

## Gotchas

- Requires Mist SDK integration in the mobile application.

## Related Endpoints

- [GET_sites_site_id_stats_maps_map_id_clients.md](GET_sites_site_id_stats_maps_map_id_clients.md) — Wi-Fi clients on map
- [GET_sites_site_id_stats_sdkclients_sdkclient_id.md](GET_sites_site_id_stats_sdkclients_sdkclient_id.md) — SDK client stats

## MistHelper Notes

Not currently used by MistHelper directly.
