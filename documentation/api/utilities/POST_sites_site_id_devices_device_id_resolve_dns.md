# testSiteSsrDnsResolution

> testSiteSsrDnsResolution

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/resolve_dns`

## Description

DNS resolutions are performed on the Device.

The output will be available through websocket. As there can be multiple command issued against the same SSR at the same time and the output all goes through the same websocket stream, `session` is used for demux.
 
 #### Subscribe to Device Command outputs
`WS /api-ws/v1/stream`

```json
{
    "subscribe": "/sites/{site_id}/devices/{device_id}/cmd"
}
```
##### Example output from ws stream
```
 Router      | Hostname               | Resolved | Last Resolved        | Expiration
-------------|------------------------|----------|----------------------|---------------------
 test-device | xxx.yyy.net            | Y        | 2022-03-28T03:56:49Z | 2022-03-28T03:57:49Z
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

`mistapi.api.v1.utilities.wan.testSiteSsrDnsResolution()`

## Usage Context

Tests DNS resolution from an SSR device. Verifies the device can resolve hostnames, helpful for diagnosing application-level connectivity issues.

## Gotchas

- Only works on SSR devices.
- Output is delivered asynchronously via WebSocket channel.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_ping.md](POST_sites_site_id_devices_device_id_ping.md) — Verify IP reachability after DNS resolves
- [POST_sites_site_id_devices_device_id_traceroute.md](POST_sites_site_id_devices_device_id_traceroute.md) — Path analysis

## MistHelper Notes

Not currently used by MistHelper via REST API.
