# releaseSiteDeviceDhcpLease

> releaseSiteDeviceDhcpLease

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/release_dhcp_leases`

## Description

Releases an active DHCP lease.

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
    "mac": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "A list of client macs to be released",
      "examples": [
        [
          "90ec77aabbcc",
          "90ec77aabbdd"
        ]
      ]
    },
    "network": {
      "type": "string",
      "description": "The network for the leases IPs to be released",
      "examples": [
        "guest"
      ]
    },
    "node": {
      "type": "string",
      "description": "only for HA. enum: `node0`, `node1`"
    },
    "port_id": {
      "minLength": 1,
      "type": "string",
      "description": "The network interface on which to release the current DHCP release",
      "examples": [
        "ge-0/0/1.10"
      ]
    }
  },
  "required": [
    "port_id"
  ],
  "description": "Note: \n  * valid combinations for Junos: \n    * `port_id` \n    * `macs` + `network`\n  * valid combinations for SSR: \n    * `port_id` \n    * `macs` + `network`\n    * `port_id` + `network`\n    * `network`\n  * if network or port_id is specified and macs is empty, it means all clients under network or port_id"
}
```

## Response

### 200

OK

## Errors

| Status | Description |
|--------|-------------|
| 400 | Parameter `port ` absent |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.utilities.common.releaseSiteDeviceDhcpLease()`

## Usage Context

Releases specific DHCP leases on a device acting as a DHCP server. Frees up IP addresses and forces clients to request new leases.

## Gotchas

- Clients will lose their current IP until they renew.
- Only works on devices running a local DHCP server.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_release_dhcp.md](POST_sites_site_id_devices_device_id_release_dhcp.md) — Release all DHCP leases
- [POST_sites_site_id_devices_device_id_show_dhcp_leases.md](POST_sites_site_id_devices_device_id_show_dhcp_leases.md) — View current leases first

## MistHelper Notes

Not currently used by MistHelper via REST API.
