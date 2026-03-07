# startSiteLocateDevice

> startSiteLocateDevice

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/locate`

## Description

### Access Points
Locate an Access Point by blinking it's LED.
It is a persisted state that has to be stopped by calling Stop Locating API

### Switches
Locate a Switch by blinking all port LEDs. 
By default, request is sent to `master` switch and LEDs will keep flashing for 5 minutes.
In case of virtual chassis (VC) the desired member mac has to be passed in the request payload. 
At anypoint, only one VC member can be requested to flash the LED. 
To stop LED flashing before the duration ends /unlocate API request can be made. 
If /unlocate API is not called LED will continue to flash on device for the given duration. 
Default duration is 5 minutes and 120 minutes is the maximum.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| device_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "title": "locate_switch",
  "type": "object",
  "properties": {
    "duration": {
      "maximum": 120.0,
      "minimum": 1.0,
      "type": "integer",
      "description": "Minutes the leds should keep flashing",
      "contentEncoding": "int32",
      "default": 5
    },
    "mac": {
      "type": "string",
      "description": "For virtual chassis, the MAC of the member",
      "examples": [
        "f01c2d4ff760"
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

`mistapi.api.v1.utilities.common.startSiteLocateDevice()`

## Usage Context

Activates the locator LED/beacon on a device. Useful for identifying a specific AP or switch in a rack, closet, or ceiling amid many devices.

## Gotchas

- The LED stays on until explicitly stopped with `unlocate`.
- Only works on devices that support LED locator (most Juniper APs and switches).

## Related Endpoints

- [POST_sites_site_id_devices_device_id_unlocate.md](POST_sites_site_id_devices_device_id_unlocate.md) — Stop the locator LED

## MistHelper Notes

Not currently used by MistHelper via REST API.
