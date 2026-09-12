# bounceDevicePort

> bounceDevicePort

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/bounce_port`

## Description

Port Bounce can be performed from Switch/Gateway.

 **Note:** Ports starting with vme, ae, irb, and HA control ports (for SSR only) are not supported

The output will be available through websocket. As there can be multiple command issued against the same AP at the same time and the output all goes through the same websocket stream, session is introduced for demux.

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
        "raw": "Port bounce complete."
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
    "ports": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of ports to bounce"
    }
  },
  "description": "Request Body"
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

`mistapi.api.v1.utilities.common.bounceDevicePort()`

## Usage Context

Bounces (disables then re-enables) a specific switch port. Useful for forcing client re-negotiation, clearing port-level errors, or restarting a connected device without physical access.

## Gotchas

- Connected devices will lose link briefly — PoE-powered devices like APs or phones will also power-cycle.
- Specify the correct port identifier; port naming varies by switch model.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_cable_test.md](POST_sites_site_id_devices_device_id_cable_test.md) — Test cable integrity
- [POST_sites_site_id_devices_device_id_clear_bpdu_error.md](POST_sites_site_id_devices_device_id_clear_bpdu_error.md) — Clear BPDU errors on ports

## MistHelper Notes

Not currently used by MistHelper via REST API.
