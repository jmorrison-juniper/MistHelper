# enableSiteDeviceZigbeeJoin

> enableSiteDeviceZigbeeJoin

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/zigbee_join`

## Description

Allow Zigbee end devices to join the network for a configurable duration. After the duration expires, new joins will be blocked (unless `allow_join`==`always` is configured on the device).

#### Subscribe to Zigbee Join Events
`WS /api-ws/v1/stream`

```json
{
    "subscribe": "/sites/{site_id}/devices/{device_id}/zigbee_join"
}
```
##### Example output from ws stream
```json
{
    "event": "data",
    "channel": "/sites/4ac1dcf4-9d8b-7211-65c4-057819f0862b/devices/00000000-0000-0000-1000-5c5b350e0060/cmd",
    "data": {
        "session": "19e73828-937f-05e6-f709-e29efdb0a82b",
        "zigbee_mac": "fd05eb86c04ac04a",
        "event_type": "associated",
        "detail": {
            "lqi": 180
        }
    }
}
```

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "additionalProperties": false,
  "description": "Request body for temporarily allowing Zigbee end-device joins",
  "properties": {
    "duration": {
      "default": 600,
      "description": "Number of seconds to permit new Zigbee end-device joins; range is 60-600",
      "maximum": 600,
      "minimum": 60,
      "type": "integer"
    }
  },
  "type": "object"
}
```

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Response containing the session identifier for a Zigbee join operation",
  "properties": {
    "session_id": {
      "description": "Session ID for the Zigbee join operation",
      "examples": [
        "19e73828-937f-05e6-f709-e29efdb0a82b"
      ],
      "format": "uuid",
      "type": "string"
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

`mistapi.api.v1.sites.devices_-_wireless.enableSiteDeviceZigbeeJoin()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
