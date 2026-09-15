# searchOrgMarvisClientsStats

> searchOrgMarvisClientsStats

## HTTP

`GET /api/v1/orgs/{org_id}/stats/marvisclients/search`

## Description

Search Marvis Client stats records across the organization.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| device_id | string | No |  |  | Filter by Marvis Client installation device UUID |
| wifi_mac | string | No |  |  | Filter by device Wi-Fi MAC address |
| wifi_ip | string | No |  |  | Filter by device Wi-Fi IP address |
| hostname | string | No |  |  | Filter by device hostname |
| model | string | No |  |  | Filter by device model |
| mfg | string | No |  |  | Filter by device manufacturer |
| serial | string | No |  |  | Filter by device serial number |
| os_type | string | No |  |  | Filter by device OS type or platform |
| os_version | string | No |  |  | Filter by device OS version |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |

## Request Body

None.

## Response

### 200

Paginated Marvis Client stats search results

```json
{
  "additionalProperties": false,
  "description": "Paginated list of Marvis Client stats records",
  "properties": {
    "limit": {
      "description": "Maximum number of results requested",
      "type": "integer"
    },
    "results": {
      "description": "List of Marvis Client stats records",
      "items": {
        "additionalProperties": false,
        "description": "Marvis Client stats record returned by search",
        "properties": {
          "battery_charging": {
            "description": "Whether the device battery is currently charging",
            "type": "boolean"
          },
          "battery_level": {
            "description": "Battery level percentage (0\u2013100)",
            "type": "integer"
          },
          "cpu_background": {
            "description": "Background CPU utilization (0\u2013100)",
            "type": "number"
          },
          "cpu_idle": {
            "description": "Idle CPU percentage (0\u2013100)",
            "type": "number"
          },
          "cpu_system": {
            "description": "System CPU utilization (0\u2013100)",
            "type": "number"
          },
          "cpu_user": {
            "description": "User-space CPU utilization (0\u2013100)",
            "type": "number"
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
          "memory_total": {
            "description": "Total device memory, in bytes",
            "type": "integer"
          },
          "memory_usage": {
            "description": "Memory in use, in bytes",
            "type": "integer"
          },
          "mfg": {
            "description": "Device manufacturer",
            "type": "string"
          },
          "model": {
            "description": "Device model name",
            "type": "string"
          },
          "org_id": {
            "description": "Organization UUID",
            "format": "uuid",
            "type": "string"
          },
          "os_type": {
            "description": "OS type or platform (e.g. Android, iOS)",
            "type": "string"
          },
          "os_version": {
            "description": "OS version string",
            "type": "string"
          },
          "serial": {
            "description": "Device serial number",
            "type": "string"
          },
          "storage_total": {
            "description": "Total device storage, in bytes",
            "type": "integer"
          },
          "storage_usage": {
            "description": "Storage in use, in bytes",
            "type": "integer"
          },
          "timestamp": {
            "description": "Timestamp of the stats record, in epoch seconds",
            "type": "integer"
          },
          "wifi_band": {
            "description": "Wi-Fi band the device is connected on",
            "type": "string"
          },
          "wifi_bssid": {
            "description": "BSSID the device is connected to",
            "type": "string"
          },
          "wifi_channel": {
            "description": "Wi-Fi channel the device is on",
            "type": "integer"
          },
          "wifi_ip": {
            "description": "Device Wi-Fi IP address",
            "type": "string"
          },
          "wifi_mac": {
            "description": "Device Wi-Fi MAC address",
            "type": "string"
          },
          "wifi_rssi": {
            "description": "Wi-Fi RSSI, in dBm",
            "type": "integer"
          },
          "wifi_ssid": {
            "description": "SSID the device is connected to",
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

`mistapi.api.v1.orgs.stats_-_marvis_clients.searchOrgMarvisClientsStats()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
