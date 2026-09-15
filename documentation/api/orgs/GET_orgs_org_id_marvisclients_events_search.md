# searchOrgMarvisClientEvents

> searchOrgMarvisClientEvents

## HTTP

`GET /api/v1/orgs/{org_id}/marvisclients/events/search`

## Description

Search Marvis Client events across the organization.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| type | string | No |  |  | Filter by event type |
| device_id | string | No |  |  | Filter by Marvis Client installation device UUID |
| wifi_mac | string | No |  |  | Filter by device Wi-Fi MAC address |
| wifi_ip | string | No |  |  | Filter by device Wi-Fi IP address |
| hostname | string | No |  |  | Filter by device hostname |
| ssid | string | No |  |  | Filter by SSID involved in roam events |
| bssid | string | No |  |  | Filter by BSSID the client roamed to |
| channel | string | No |  |  | Filter by channel the client roamed to |
| pre_bssid | string | No |  |  | Filter by BSSID the client roamed from |
| pre_channel | string | No |  |  | Filter by channel the client roamed from |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |

## Request Body

None.

## Response

### 200

Paginated Marvis Client events search results

```json
{
  "additionalProperties": false,
  "description": "Paginated list of Marvis Client events",
  "properties": {
    "limit": {
      "description": "Maximum number of results requested",
      "type": "integer"
    },
    "results": {
      "description": "List of Marvis Client events",
      "items": {
        "additionalProperties": false,
        "description": "A Marvis Client event record",
        "properties": {
          "band": {
            "description": "Wi-Fi band at the time of the event",
            "type": "string"
          },
          "bssid": {
            "description": "BSSID the client roamed to (for roam events)",
            "type": "string"
          },
          "channel": {
            "description": "Channel the client roamed to (for roam events)",
            "type": "integer"
          },
          "device_id": {
            "description": "UUID of the device the Marvis Client is installed on",
            "format": "uuid",
            "type": "string"
          },
          "hostname": {
            "description": "Device hostname",
            "type": "string"
          },
          "location": {
            "additionalProperties": false,
            "description": "Last known location fix for a Marvis Client device",
            "properties": {
              "map_id": {
                "description": "UUID of the floor-plan map",
                "format": "uuid",
                "type": "string"
              },
              "site_id": {
                "description": "UUID of the site the device was located in",
                "format": "uuid",
                "type": "string"
              },
              "timestamp": {
                "description": "Timestamp of the location fix, in epoch seconds",
                "type": "integer"
              },
              "x": {
                "description": "X coordinate on the floor-plan map, in pixels",
                "type": "number"
              },
              "y": {
                "description": "Y coordinate on the floor-plan map, in pixels",
                "type": "number"
              }
            },
            "type": "object"
          },
          "neighbor_ap_report": {
            "description": "List of neighboring APs observed at the time of the event",
            "items": {
              "additionalProperties": false,
              "description": "A neighboring AP observed in a Marvis Client event",
              "properties": {
                "band": {
                  "description": "Wi-Fi band the AP is operating on",
                  "type": "string"
                },
                "bssid": {
                  "description": "BSSID of the neighboring AP",
                  "type": "string"
                },
                "channel": {
                  "description": "Channel the neighboring AP is on",
                  "type": "integer"
                },
                "rssi": {
                  "description": "RSSI of the neighboring AP signal, in dBm",
                  "type": "integer"
                }
              },
              "type": "object"
            },
            "type": "array"
          },
          "org_id": {
            "description": "Organization UUID",
            "format": "uuid",
            "type": "string"
          },
          "percent": {
            "description": "Battery level percentage at the time of the event (for battery events)",
            "type": "integer"
          },
          "pre_bssid": {
            "description": "BSSID the client roamed from (for roam events)",
            "type": "string"
          },
          "pre_channel": {
            "description": "Channel the client roamed from (for roam events)",
            "type": "integer"
          },
          "pre_rssi": {
            "description": "RSSI before the roam event, in dBm",
            "type": "integer"
          },
          "rssi": {
            "description": "Wi-Fi RSSI at the time of the event, in dBm",
            "type": "integer"
          },
          "ssid": {
            "description": "SSID the client was connected to",
            "type": "string"
          },
          "timestamp": {
            "description": "Event timestamp, in epoch seconds",
            "type": "integer"
          },
          "type": {
            "description": "Event type",
            "type": "string"
          },
          "wifi_ip": {
            "description": "Device Wi-Fi IP address at the time of the event",
            "type": "string"
          },
          "wifi_mac": {
            "description": "Device Wi-Fi MAC address",
            "type": "string"
          }
        },
        "type": "object"
      },
      "type": "array"
    },
    "total": {
      "description": "Total number of matching results",
      "type": "integer"
    }
  },
  "type": "object"
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

`mistapi.api.v1.orgs.clients_-_marvis.searchOrgMarvisClientEvents()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
