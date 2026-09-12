# showSiteDeviceEvpnDatabase

> showSiteDeviceEvpnDatabase

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/show_evpn_database`

## Description

Get EVPN Database from the Device. The output will be available through websocket.

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
    "duration": {
      "maximum": 300.0,
      "minimum": 0.0,
      "type": "integer",
      "description": "Duration in sec for which refresh is enabled. Should be set only if interval is configured to non-zero value.",
      "contentEncoding": "int32",
      "default": 0
    },
    "interval": {
      "maximum": 10.0,
      "minimum": 0.0,
      "type": "integer",
      "description": "Rate at which output will refresh",
      "contentEncoding": "int32",
      "default": 0
    },
    "mac": {
      "type": "string",
      "description": "Client mac filter",
      "examples": [
        "f8c1165c6400"
      ]
    },
    "port_id": {
      "type": "string",
      "description": "Interface name",
      "examples": [
        "ge-0/0/0.0"
      ]
    }
  },
  "description": "All attributes are optional"
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

`mistapi.api.v1.utilities.common.showSiteDeviceEvpnDatabase()`

## Usage Context

Retrieves the EVPN database from a switch participating in an EVPN-VXLAN fabric. Shows MAC/IP routes learned via BGP EVPN.

## Gotchas

- Only returns results on switches configured for EVPN-VXLAN.
- Database can be large in campus fabrics — results may be paginated.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_show_mac_table.md](POST_sites_site_id_devices_device_id_show_mac_table.md) — Local MAC table
- [POST_sites_site_id_devices_device_id_show_bgp_summary.md](POST_sites_site_id_devices_device_id_show_bgp_summary.md) — BGP session status for EVPN underlay

## MistHelper Notes

Not currently used by MistHelper via REST API.
