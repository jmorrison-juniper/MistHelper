# clearBpduErrorsFromPortsOnSwitch

> clearBpduErrorsFromPortsOnSwitch

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/clear_bpdu_error`

## Description

Clear bridge protocol data unit (BPDU) error condition caused by the detection of a possible bridging loop from Spanning Tree Protocol (STP) operation that renders the port unoperational.

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
  "title": "utils_clear_bpdu",
  "type": "object",
  "properties": {
    "port": {
      "type": "string",
      "description": "Port on which to clear the detected BPDU error, or `all` for all ports"
    }
  }
}
```

## Response

### 200

OK

## Errors

| Status | Description |
|--------|-------------|
| 400 | Port not specified |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.utilities.lan.clearBpduErrorsFromPortsOnSwitch()`

## Usage Context

Clears BPDU error state on switch ports that have been shut down due to BPDU guard violations. Re-enables the affected ports.

## Gotchas

- Investigate the root cause of BPDU errors before clearing — may indicate unauthorized switch/AP with spanning tree.
- Ports will re-enter error state if the problem device is still connected.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_bounce_port.md](POST_sites_site_id_devices_device_id_bounce_port.md) — Bounce individual ports
- [POST_sites_site_id_devices_device_id_show_mac_table.md](POST_sites_site_id_devices_device_id_show_mac_table.md) — Check what is connected to the port

## MistHelper Notes

Not currently used by MistHelper via REST API.
