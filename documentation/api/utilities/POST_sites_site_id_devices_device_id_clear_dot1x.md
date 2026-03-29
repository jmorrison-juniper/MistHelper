# clearSiteDeviceDot1xSession

> clearSiteDeviceDot1xSession

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/clear_dot1x`

## Description

Clear Dot1x Session. The output will be available through websocket.

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
    "port_id": {
      "type": "string",
      "description": "ID of the port where the dot1x session must be cleared. If not provided, the sessions on all the port will be cleared.",
      "examples": [
        "ge-0/0/0"
      ]
    }
  },
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

`mistapi.api.v1.utilities.lan.clearSiteDeviceDot1xSession()`

## Usage Context

Clears 802.1X authentication sessions on switch ports. Forces clients to re-authenticate. Useful after NAC policy changes or when clients are stuck in a wrong VLAN.

## Gotchas

- All authenticated clients on affected ports must re-authenticate — brief connectivity disruption expected.
- Consider targeting specific ports if possible rather than clearing all sessions.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_show_dot1x.md](POST_sites_site_id_devices_device_id_show_dot1x.md) — View current 802.1X state
- [POST_sites_site_id_wired_clients_client_mac_coa.md](POST_sites_site_id_wired_clients_client_mac_coa.md) — CoA for individual clients

## MistHelper Notes

Not currently used by MistHelper via REST API.
