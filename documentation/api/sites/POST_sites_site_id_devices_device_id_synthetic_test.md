# triggerSiteDeviceSyntheticTest

> triggerSiteDeviceSyntheticTest

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/synthetic_test`

## Description

Trigger Device Synthetic Test

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
  "title": "synthetictest_device",
  "required": [
    "type"
  ],
  "type": "object",
  "properties": {
    "host": {
      "type": "string",
      "description": "If `type`==`lan_connectivity`",
      "examples": [
        "www.example.com"
      ]
    },
    "hostname": {
      "type": "string",
      "description": "If `type`==`dns`",
      "examples": [
        "google.com\""
      ]
    },
    "ip": {
      "type": "string",
      "description": "If `type`==`arp`",
      "examples": [
        "192.168.3.5"
      ]
    },
    "password": {
      "type": "string",
      "description": "If `type`==`radius`",
      "examples": [
        "test123"
      ]
    },
    "ping_count": {
      "maximum": 60.0,
      "minimum": 10.0,
      "type": "integer",
      "description": "If `type`==`lan_connectivity`",
      "contentEncoding": "int32",
      "default": 10
    },
    "ping_details": {
      "type": "boolean",
      "description": "If `type`==`lan_connectivity`",
      "default": false
    },
    "ping_size": {
      "maximum": 65535.0,
      "minimum": 56.0,
      "type": "integer",
      "description": "If `type`==`lan_connectivity`",
      "contentEncoding": "int32",
      "default": 56
    },
    "port_id": {
      "type": "string",
      "description": "If `type`==`speedtest`, required for ssr",
      "examples": [
        "wan0"
      ]
    },
    "protocol": {
      "type": "string",
      "description": "if `type`==`lan_connectivity`. enum: `ping`, `traceroute`, `ping+traceroute`"
    },
    "tenant": {
      "type": "string",
      "description": "If `type`==`curl` or `type`==`lan_connectivity`",
      "examples": [
        "lan_network1"
      ]
    },
    "timeout": {
      "maximum": 120.0,
      "minimum": 30.0,
      "type": "integer",
      "description": "If `type`==`curl`",
      "contentEncoding": "int32",
      "default": 60,
      "examples": [
        60
      ]
    },
    "traceroute_udp_port": {
      "maximum": 65535.0,
      "minimum": 0.0,
      "type": "integer",
      "description": "SRX only, traceroute udp port",
      "contentEncoding": "int32",
      "default": 33434
    },
    "type": {
      "type": "string",
      "description": "enum: `arp`, `curl`, `dhcp`, `dhcp6`, `dns`, `lan_connectivity`, `radius`, `speedtest`"
    },
    "url": {
      "type": "string",
      "description": "If `type`==`curl`",
      "examples": [
        "https://www.example.com"
      ]
    },
    "username": {
      "type": "string",
      "description": "If `type`==`radius`",
      "examples": [
        "user"
      ]
    },
    "vlan_id": {
      "type": "object",
      "description": "Required for AP"
    }
  }
}
```

## Response

### 200

Scheduled

## Errors

| Status | Description |
|--------|-------------|
| 400 | Device not online / Device not supported / Already in progress |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.synthetic_tests.triggerSiteDeviceSyntheticTest()`

## Usage Context

Triggers an on-demand synthetic test on a specific device (AP connectivity check, speed test, etc.).

## Gotchas

- Test results are asynchronous. Poll the results endpoint for completion.

## Related Endpoints

- [GET_sites_site_id_devices_device_id_synthetic_test.md](GET_sites_site_id_devices_device_id_synthetic_test.md) — Get test results
- [GET_sites_site_id_synthetic_test_search.md](GET_sites_site_id_synthetic_test_search.md) — Search test results

## MistHelper Notes

Not currently used by MistHelper directly.
