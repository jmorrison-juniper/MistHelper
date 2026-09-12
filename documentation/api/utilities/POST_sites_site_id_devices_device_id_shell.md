# createSiteDeviceShellSession

> createSiteDeviceShellSession

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/shell`

## Description

Create Shell Session

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
  "title": "shell_node",
  "type": "object",
  "properties": {
    "node": {
      "type": "string",
      "description": "only for HA. enum: `node0`, `node1`"
    }
  }
}
```

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

`mistapi.api.v1.utilities.common.createSiteDeviceShellSession()`

## Usage Context

Creates an interactive shell session on a device via the Mist cloud. Provides direct CLI access for advanced troubleshooting. Output delivered via WebSocket.

## Gotchas

- Requires elevated permissions.
- Session is interactive and holds a WebSocket connection open.
- Commands run in the device shell have full system access — exercise extreme caution.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_run_top.md](POST_sites_site_id_devices_device_id_run_top.md) — Quick CPU check without full shell
- [POST_sites_site_id_devices_device_id_support.md](POST_sites_site_id_devices_device_id_support.md) — Generate support file (safer alternative)

## MistHelper Notes

Not currently used by MistHelper via REST API. MistHelper Menus **97-98** (SSH Runner) provide device command execution via a different mechanism.
