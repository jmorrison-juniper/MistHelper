# listSiteUnconnectedClientStats

> listSiteUnconnectedClientStats

## HTTP

`GET /api/v1/sites/{site_id}/stats/maps/{map_id}/unconnected_clients`

## Description

Get List of Site Unconnected Client Location

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
    "title": "stats_unconnected_client",
    "required": [
      "ap_mac",
      "mac",
      "manufacture",
      "rssi",
      "y"
    ],
    "type": "object",
    "properties": {
      "ap_mac": {
        "type": "string",
        "description": "MAC address of the AP that heard the client"
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
        "description": "MAC address of the (unconnected) client"
      },
      "manufacture": {
        "type": "string",
        "description": "Device manufacture, through fingerprinting or OUI"
      },
      "map_id": {
        "type": [
          "string",
          "null"
        ],
        "description": "Map_id of the client (if known), or null",
        "contentEncoding": "uuid"
      },
      "rssi": {
        "type": "integer",
        "description": "Client RSSI observed by the AP that heard the client (in dBm)",
        "contentEncoding": "int32"
      },
      "x": {
        "type": "number",
        "description": "X (in pixels) of user location on the map (if known)"
      },
      "y": {
        "type": "number",
        "description": "Y (in pixels) of user location on the map (if known)"
      }
    },
    "description": "Unconnected clients statistics"
  },
  "description": "",
  "examples": [
    [
      {
        "ap_mac": "5c5b350e0410",
        "last_seen": 1428939600,
        "mac": "5684dae9ac8b",
        "manufacture": "Apple",
        "rssi": -75,
        "x": 60,
        "y": 80
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

`mistapi.api.v1.sites.stats_-_clients_wireless.listSiteUnconnectedClientStats()`

## Usage Context

Retrieves unconnected (probing) client positions on a specific map/floor. Shows devices that are near APs but not associated.

## Gotchas

- Unconnected client positions are less accurate than connected clients due to limited data.

## Related Endpoints

- [GET_sites_site_id_stats_maps_map_id_clients.md](GET_sites_site_id_stats_maps_map_id_clients.md) — Connected clients on map
- [GET_sites_site_id_stats_maps_map_id_sdkclients.md](GET_sites_site_id_stats_maps_map_id_sdkclients.md) — SDK clients on map

## MistHelper Notes

Not currently used by MistHelper directly.
