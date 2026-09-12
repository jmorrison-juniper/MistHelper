# showSiteSsrServicePath

> showSiteSsrServicePath

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/show_service_path`

## Description

Get service path information of the Device.


The output will be available through websocket. As there can be multiple command
issued against the same device at the same time and the output all goes through
the same websocket stream, session is introduced for demux.



#### Subscribe to Device Command outputs

`WS /api-ws/v1/stream`


```json
{ "subscribe": "/sites/{site_id}/devices/{device_id}/cmd" }
```

#### Example output from ws stream

```json
{
      "channel": "/sites/d6fb4f96-xxxx-xxxx-xxxx-xxxxxxxxxxxx/devices/00000000-0000-0000-1000-xxxxxxxxxxxx/cmd",
      "event": "data",
      "data": {
              "session": "5cb8a6db-d11a-42cd-bed7-19e9f29e637",
              "raw": "{\"status\":\"SUCCESS\",\"finished\":true,\"rows\":[{\"service\":\"management\",\"type\":\"service-agent\",\"network_interface\":\"ge-0/0/0\",\"destination\":\"\",\"gateway_ip\":\"192.168.1.1\",\"vector\":\"\",\"cost\":0,\"rate\":0,\"state\":\"Up\",\"capacity\":\"0/unlimited\",\"meetsSLA\":\"Yes\"},{\"service\":\"management\",\"type\":\"service-agent\",\"network_interface\":\"ge-0/0/1\",\"destination\":\"\",\"gateway_ip\":\"192.168.0.1\",\"vector\":\"\",\"cost\":0,\"rate\":0,\"state\":\"Up\",\"capacity\":\"0/unlimited\",\"meetsSLA\":\"Yes\"}]}"
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
    "node": {
      "type": "string",
      "description": "only for HA. enum: `node0`, `node1`"
    },
    "service_name": {
      "type": "string",
      "examples": [
        "any"
      ]
    }
  },
  "description": "The exact service name for which to display the service path"
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

`mistapi.api.v1.utilities.wan.showSiteSsrServicePath()`

## Usage Context

Retrieves the session smart routing service path table from an SSR device. Shows service routes, next-hops, and tenant/service context.

## Gotchas

- Only works on SSR (Session Smart Router) devices, not SRX or switches.
- Returns SSR-specific session routing data, not standard IP routing.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_show_session.md](POST_sites_site_id_devices_device_id_show_session.md) — Active SSR sessions
- [POST_sites_site_id_devices_device_id_show_route.md](POST_sites_site_id_devices_device_id_show_route.md) — Standard routing table

## MistHelper Notes

WebSocket show commands (Menu **8**) use a similar endpoint for real-time SSR service path retrieval.
