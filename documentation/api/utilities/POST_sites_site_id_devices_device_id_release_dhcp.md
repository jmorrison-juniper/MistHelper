# releaseSiteSsrDhcpLease

> releaseSiteSsrDhcpLease

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/release_dhcp`

## Description

Releases an active DHCP lease.


The output will be available through websocket.

As there can be multiple command issued  against the same Device at the same
time and the output all goes through the same websocket stream, session is
introduced for demux.



#### Subscribe to Device Command outputs


`WS /api-ws/v1/stream`


```json

{ "subscribe": "/sites/{site_id}/devices/{device_id}/cmd" }

```



#### Example output from ws stream


```json
{
    "event": "data",
    "channel": "/sites/d6fb4f96-3ba4-4cf5-8af2-a8d7b85087ac/devices/00000000-0000-0000-1000-0200010edbca/cmd",
    "data": "{\"event\": \"data\", \"channel\": \"/sites/d6fb4f96-xxxx-xxxx-xxxx-a8d7b85087ac/devices/0200010edbca/cmd\",\"data\": {\"session\": \"356b2150-7307-4165-8411-52794c1ee8b0\",\"raw\": \"Releasing dhcp...\"}}"
}
{
    "event": "data",
    "channel": "/sites/d6fb4f96-3ba4-4cf5-8af2-a8d7b85087ac/devices/00000000-0000-0000-1000-0200010edbca/cmd",
    "data": "{\"event\": \"data\", \"channel\": \"/sites/d6fb4f96-xxxx-xxxx-xxxx-a8d7b85087ac/devices/0200010edbca/cmd\",\"data\": {\"session\": \"356b2150-7307-4165-8411-52794c1ee8b0\",\"raw\": \"Successfully released DHCP lease.\"}}"
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

`mistapi.api.v1.utilities.wan.releaseSiteSsrDhcpLease()`

## Usage Context

Releases all DHCP leases on a device acting as a DHCP server. Clears the entire lease table, forcing all clients to re-request addresses.

## Gotchas

- All DHCP clients on the device will temporarily lose their IP addresses.
- Use `release_dhcp_leases` for targeted lease release instead.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_release_dhcp_leases.md](POST_sites_site_id_devices_device_id_release_dhcp_leases.md) — Release specific leases
- [POST_sites_site_id_devices_device_id_show_dhcp_leases.md](POST_sites_site_id_devices_device_id_show_dhcp_leases.md) — View current leases

## MistHelper Notes

Not currently used by MistHelper via REST API.
