# clearSiteDeviceSession

> clearSiteDeviceSession

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/clear_session`

## Description

Clear session

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
      "description": "Service name, only supported in SSR",
      "examples": [
        "internet-wan_and_lte"
      ]
    },
    "session_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "List of id of the sessions to be cleared",
      "examples": [
        [
          "88776655-0123-4567-890a-112233445566"
        ]
      ]
    }
  },
  "description": "To use five tuples to lookup the session to be cleared, all must be provided"
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

`mistapi.api.v1.utilities.wan.clearSiteDeviceSession()`

## Usage Context

Clears active sessions on an SSR device. Terminates session smart routing sessions, forcing traffic to re-establish through the session path.

## Gotchas

- Only works on SSR devices.
- Active traffic flows will be disrupted until sessions are re-established.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_show_session.md](POST_sites_site_id_devices_device_id_show_session.md) — View current sessions first
- [POST_sites_site_id_devices_device_id_show_service_path.md](POST_sites_site_id_devices_device_id_show_service_path.md) — Service path state

## MistHelper Notes

Not currently used by MistHelper via REST API.
