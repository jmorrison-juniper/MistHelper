# showSiteDeviceBgpSummary

> showSiteDeviceBgpSummary

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/show_bgp_summary`

## Description

Get BGP Summary from SSR, SRX and Switch.


The output will be available through websocket. As there can be multiple command issued against the same device at the same time and the output all goes through the same websocket stream, `session` is introduced for demux.

#### Subscribe to Device Command outputs
`WS /api-ws/v1/stream`

```json
{
    "subscribe": "/sites/{site_id}/devices/{device_id}/cmd"

}
```

##### Example output from ws stream
```
Tue 2024-04-23 16:36:06 UTC
Retrieving bgp entries...
BGP table version is 354, local router ID is 10.224.8.16, vrf id 0
Default local pref 100, local AS 65000
Status codes:  s suppressed, d damped, h history, * valid, > best, = multipath,
              i internal, r RIB_failure, S Stale, R Removed
Nexthop codes: @NNN nexthop's vrf id, < announce-nh-self
Origin codes:  i - IGP, e - EGP, ? - incomplete
RPKI validation codes: V valid, I invalid, N Not found

  Network                                      Next Hop                                  Metric LocPrf Weight Path
*> 161.161.161.0/24
```"

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

`mistapi.api.v1.utilities.common.showSiteDeviceBgpSummary()`

## Usage Context

Executes a `show bgp summary` command on a gateway via the Mist cloud. Returns BGP neighbor states, prefixes received, and session uptime.

## Gotchas

- Only works on gateways (SRX/SSR) with BGP configured.
- Returns an empty result if the device has no BGP peers.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_clear_bgp.md](POST_sites_site_id_devices_device_id_clear_bgp.md) — Clear BGP sessions
- [POST_sites_site_id_devices_device_id_show_route.md](POST_sites_site_id_devices_device_id_show_route.md) — Routing table entries

## MistHelper Notes

Not currently used by MistHelper via REST API. BGP-related operations are available through WebSocket commands.
