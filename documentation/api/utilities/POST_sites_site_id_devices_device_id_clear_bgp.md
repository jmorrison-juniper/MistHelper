# clearSiteSsrBgpRoutes

> clearSiteSsrBgpRoutes

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/clear_bgp`

## Description

Clear routes associated with one or all BGP neighbors

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
    "neighbor": {
      "type": "string",
      "description": "Neighbor ip-address or 'all'"
    },
    "node": {
      "type": "string",
      "description": "only for HA. enum: `node0`, `node1`"
    },
    "type": {
      "type": "string",
      "description": "enum: `hard`, `in`, `out`, `soft`"
    },
    "vrf": {
      "type": "string",
      "description": "VRF name"
    }
  },
  "required": [
    "neighbor",
    "type"
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
| 400 | Parameter neighbor absent |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.utilities.wan.clearSiteSsrBgpRoutes()`

## Usage Context

Clears BGP sessions on a gateway. Forces BGP neighbor re-establishment and route re-advertisement. Useful after routing policy changes.

## Gotchas

- Causes temporary routing convergence — may briefly disrupt WAN traffic.
- Use soft-reset options if available to avoid full session teardown.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_show_bgp_summary.md](POST_sites_site_id_devices_device_id_show_bgp_summary.md) — View BGP neighbor states

## MistHelper Notes

Not currently used by MistHelper via REST API.
