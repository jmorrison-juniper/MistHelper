# startSiteSwitchRadiusSyntheticTest

> startSiteSwitchRadiusSyntheticTest

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/check_radius_server`

## Description

Ping test from the AP to confirm 'reachability' of the Radius server. 

Utilize Juniper EX switch(to which an AP is connected to) radius test capabilities to get details on the Radius Server 'availability'.



#### Subscribe to Device Command outputs

`WS /api-ws/v1/stream`


```json
{
    "subscribe": "/sites/{site_id}/devices/{device_id}/cmd"
}
```

#### Example output from ws stream

```json
{
  "event": "data",
  "channel": "/sites/d6fb4f96-3ba4-4cf5-8af2-a8d7b85087ac/devices/00000000-0000-0000-1000-2093390b3580/cmd",
  "data": "{\"event\": \"data\", \"channel\": \"/sites/d6fb4f96-3ba4-4cf5-8af2-a8d7b85087ac/devices/2093390b3580/cmd\", \"data\": {\"session\": \"6043daff-884e-48bc-aa9a-810d268aceb1\", \"raw\": \"    Reason : fail\"}}"
}
{
  "event": "data",
  "channel": "/sites/d6fb4f96-3ba4-4cf5-8af2-a8d7b85087ac/devices/00000000-0000-0000-1000-2093390b3580/cmd",
  "data": "{\"event\": \"data\", \"channel\": \"/sites/d6fb4f96-3ba4-4cf5-8af2-a8d7b85087ac/devices/2093390b3580/cmd\", \"data\": {\"session\": \"6043daff-884e-48bc-aa9a-810d268aceb1\", \"raw\": \"    Test complete. Exiting\"}}"
}
```

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
  "type": "object",
  "properties": {
    "password": {
      "type": "string",
      "description": "Specify the password associated with the username"
    },
    "profile": {
      "type": "string",
      "description": "Specify the access profile associated with the subscriber",
      "default": "dot1x"
    },
    "user": {
      "type": "string",
      "description": "Specify the subscriber username to test"
    }
  },
  "required": [
    "password",
    "user"
  ]
}
```

## Response

### 200

OK

```json
{
  "title": "websocket_session",
  "required": [
    "session"
  ],
  "type": "object",
  "properties": {
    "session": {
      "type": "string",
      "examples": [
        "19e73828-937f-05e6-f709-e29efdb0a82b"
      ]
    }
  }
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

`mistapi.api.v1.sites.synthetic_tests.startSiteSwitchRadiusSyntheticTest()`

## Usage Context

Tests RADIUS server connectivity from a specific device. Validates that the AP/switch can reach the configured RADIUS server.

## Gotchas

- Test uses the RADIUS configuration from the device's WLAN or port profile.

## Related Endpoints

- [GET_sites_site_id_devices_device_id.md](GET_sites_site_id_devices_device_id.md) — Device config
- [GET_sites_site_id_setting.md](GET_sites_site_id_setting.md) — Site settings

## MistHelper Notes

Not currently used by MistHelper directly.
