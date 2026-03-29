# servicePingFromSsr

> servicePingFromSsr

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/service_ping`

## Description

Ping from SSR

Service Ping can be performed from the Device. The output will be available through websocket. As there can be multiple command issued against the same device at the same time and the output all goes through the same websocket stream, session is introduced for demux.

#### Subscribe to Device Command outputs
`WS /api-ws/v1/stream`

```json
{
    "subscribe": "/sites/{site_id}/devices/{device_id}/cmd"
}
```
##### Example output from ws stream
```json
{
    "event": "data",
    "channel": "/sites/4ac1dcf4-9d8b-7211-65c4-057819f0862b/devices/00000000-0000-0000-1000-5c5b350e0060/cmd",
    "data": {
        "session": "session_id",
        "raw": "64 bytes from 23.211.0.110: seq=8 ttl=58 time=12.323 ms\n"
    }
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
    "count": {
      "type": "integer",
      "contentEncoding": "int32",
      "default": 10
    },
    "host": {
      "type": "string"
    },
    "node": {
      "type": "string",
      "description": "only for HA. enum: `node0`, `node1`"
    },
    "service": {
      "type": "string",
      "description": "Ping packet takes the same path as the service"
    },
    "size": {
      "maximum": 65535.0,
      "minimum": 56.0,
      "type": "integer",
      "contentEncoding": "int32",
      "default": 56
    },
    "tenant": {
      "type": "string",
      "description": "Tenant context in which the packet is sent"
    }
  },
  "required": [
    "host",
    "service"
  ],
  "description": "Request Body"
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

`mistapi.api.v1.utilities.wan.servicePingFromSsr()`

## Usage Context

Executes a service ping from an SSR device. Tests connectivity through a specific session smart routing service, validating service path reachability.

## Gotchas

- Only works on SSR devices with configured services.
- Requires specifying the service name and destination.
- Output is delivered asynchronously via WebSocket channel.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_show_service_path.md](POST_sites_site_id_devices_device_id_show_service_path.md) — View available service paths
- [POST_sites_site_id_devices_device_id_ping.md](POST_sites_site_id_devices_device_id_ping.md) — Standard ping

## MistHelper Notes

Not currently used by MistHelper via REST API.
