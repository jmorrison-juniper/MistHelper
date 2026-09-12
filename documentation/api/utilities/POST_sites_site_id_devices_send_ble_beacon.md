# sendSiteDevicesArbitraryBleBeacon

> sendSiteDevicesArbitraryBleBeacon

## HTTP

`POST /api/v1/sites/{site_id}/devices/send_ble_beacon`

## Description

Send arbitrary BLE Beacon for a period of time

Note that only the devices that are connected will be restarted.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "beacon_frame": {
      "type": "string",
      "examples": [
        "68b329da9893e34099c7d8ad5cb9c940"
      ]
    },
    "beacon_freq": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        100
      ]
    },
    "duration": {
      "maximum": 60.0,
      "minimum": 1.0,
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        10
      ]
    },
    "macs": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "examples": [
        [
          "5c5b35584a6f",
          "5c5b350ea3b3"
        ]
      ]
    },
    "map_ids": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "examples": [
        [
          "845a23bf-bed9-e43c-4c86-6fa474be7ae5"
        ]
      ]
    }
  }
}
```

## Response

### 200

OK

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

`mistapi.api.v1.utilities.location.sendSiteDevicesArbitraryBleBeacon()`

## Usage Context

Sends an arbitrary BLE (Bluetooth Low Energy) beacon from APs at a site. Used for BLE asset tracking, indoor location services, or testing BLE infrastructure.

## Gotchas

- Only works on APs with BLE radios enabled.
- BLE beacon content must conform to expected advertisement format.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_locate.md](POST_sites_site_id_devices_device_id_locate.md) — LED locate uses a different mechanism

## MistHelper Notes

Not currently used by MistHelper via REST API.
