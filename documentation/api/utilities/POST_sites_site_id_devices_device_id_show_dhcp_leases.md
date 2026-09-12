# showSiteDeviceDhcpLeases

> showSiteDeviceDhcpLeases

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/show_dhcp_leases`

## Description

Shows DHCP leases

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
  "title": "utils_show_dhcp_leases",
  "required": [
    "network"
  ],
  "type": "object",
  "properties": {
    "network": {
      "type": "string",
      "description": "DHCP network for the leases, returns full table if not specified",
      "examples": [
        "guest"
      ]
    },
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

`mistapi.api.v1.utilities.common.showSiteDeviceDhcpLeases()`

## Usage Context

Retrieves the DHCP lease table from a gateway acting as a DHCP server. Shows active leases with client MAC, IP, hostname, and expiry.

## Gotchas

- Only returns leases if the device runs a local DHCP server.
- External DHCP servers are not visible through this endpoint.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_release_dhcp_leases.md](POST_sites_site_id_devices_device_id_release_dhcp_leases.md) — Release DHCP leases
- [POST_sites_site_id_devices_device_id_show_arp.md](POST_sites_site_id_devices_device_id_show_arp.md) — ARP table for IP-MAC mappings

## MistHelper Notes

Not currently used by MistHelper via REST API.
