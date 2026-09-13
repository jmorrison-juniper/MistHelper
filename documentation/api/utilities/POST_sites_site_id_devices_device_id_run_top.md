# runSiteSrxTopCommand

> runSiteSrxTopCommand

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/run_top`

## Description

Run top command on switches and SRX. The output will be available through websocket. 

As there can be multiple command issued against the same device at the same time and the output all goes through the same websocket stream, `session` is introduced for demux.

#### Subscribe to Device Command outputs
`WS /api-ws/v1/stream`

```json
{
  "subscribe": "/sites/{site_id}/devices/{device_id}/cmd"
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

None.

## Response

### 200

OK

```json
{
  "title": "websocket_session_with_url",
  "required": [
    "session",
    "url"
  ],
  "type": "object",
  "properties": {
    "session": {
      "type": "string",
      "examples": [
        "19e73828-937f-05e6-f709-e29efdb0a82b"
      ]
    },
    "url": {
      "type": "string",
      "examples": [
        "wss://api-ws.mist.com/ssh?jwt=xxxx"
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

`mistapi.api.v1.utilities.wan.runSiteSrxTopCommand()`

## Usage Context

Runs the `top` command on an SRX device to view real-time CPU and process utilization. Output delivered via WebSocket.

## Gotchas

- Only works on SRX gateways.
- Output is streaming and delivered asynchronously via WebSocket.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_shell.md](POST_sites_site_id_devices_device_id_shell.md) — Full shell session for deeper diagnostics
- [POST_sites_site_id_devices_device_id_support.md](POST_sites_site_id_devices_device_id_support.md) — Generate support file

## MistHelper Notes

Not currently used by MistHelper via REST API.
