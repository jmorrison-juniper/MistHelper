# clearSiteSsrArpCache

> clearSiteSsrArpCache

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/clear_arp`

## Description

Clear ARP cache for SSR, SRX and Switch

Clear the entire ARP cache or a subset if arguments are provided.

*Note*: port_id is optional if neither vlan nor ip is specified

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
  "title": "utils_clear_arp",
  "type": "object",
  "properties": {
    "ip": {
      "type": "string",
      "description": "The IP address for which to clear an ARP entry. port_id must be specified.",
      "examples": [
        "10.1.1.1"
      ]
    },
    "node": {
      "type": "string",
      "description": "only for HA. enum: `node0`, `node1`"
    },
    "port_id": {
      "type": "string",
      "description": "The device interface on which to clear the ARP cache.",
      "examples": [
        "wan"
      ]
    },
    "vlan": {
      "type": "integer",
      "description": "The VLAN on which to clear the ARP cache. port_id must be specified.",
      "contentEncoding": "int32",
      "examples": [
        1000
      ]
    },
    "vrf": {
      "type": "string",
      "description": "The vrf for which to clear an ARP entry. applicable for switch.",
      "examples": [
        "guest"
      ]
    }
  }
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

`mistapi.api.v1.utilities.wan.clearSiteSsrArpCache()`

## Usage Context

Clears the ARP table on a switch or gateway. Forces the device to re-learn IP-to-MAC bindings. Useful when troubleshooting stale ARP entries causing connectivity issues.

## Gotchas

- Causes brief traffic disruption as the device re-learns ARP entries.
- Only clear on the specific device with stale entries, not broadly.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_show_arp.md](POST_sites_site_id_devices_device_id_show_arp.md) — View current ARP table first

## MistHelper Notes

Not currently used by MistHelper via REST API.
