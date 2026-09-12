# getSiteSdkStats

> getSiteSdkStats

## HTTP

`GET /api/v1/sites/{site_id}/stats/sdkclients/{sdkclient_id}`

## Description

Get Detail Stats of a SdkClient

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| sdkclient_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
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
      "contentEncoding": "uuid"
    },
    "name": {
      "type": "string",
      "description": "Name of the sdk client (if provided)"
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
      "contentEncoding": "uuid"
    },
    "vbeacons": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "sdkstats_wireless_client_vbeacon",
        "required": [
          "id",
          "since"
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
          "since": {
            "type": "number"
          }
        }
      },
      "description": "List of beacon_id\u2019s of the sdk client is in and since when (if known)"
    },
    "x": {
      "type": "number",
      "description": "X (in pixels) of user location on the map (if known)"
    },
    "y": {
      "type": "number",
      "description": "Y (in pixels) of user location on the map (if known)"
    },
    "zones": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "sdkstats_wireless_client_zone",
        "required": [
          "id",
          "since"
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
          "since": {
            "type": "number"
          }
        }
      },
      "description": "List of zone_id\u2019s of the sdk client is in and since when (if known)"
    }
  },
  "required": [
    "id",
    "uuid"
  ],
  "description": "SDK Client Details statistics"
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

`mistapi.api.v1.sites.stats_-_clients_sdk.getSiteSdkStats()`

## Usage Context

Retrieves statistics for a specific SDK client (mobile app using Mist SDK), including location and connection data.

## Gotchas

- Requires Mist SDK integration in the mobile application.

## Related Endpoints

- [GET_sites_site_id_stats_maps_map_id_sdkclients.md](GET_sites_site_id_stats_maps_map_id_sdkclients.md) — SDK clients on map
- [GET_sites_site_id_stats_clients.md](GET_sites_site_id_stats_clients.md) — Wi-Fi client stats

## MistHelper Notes

Not currently used by MistHelper directly.
