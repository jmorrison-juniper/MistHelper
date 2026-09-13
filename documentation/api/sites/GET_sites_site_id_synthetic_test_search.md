# searchSiteSyntheticTest

> searchSiteSyntheticTest

## HTTP

`GET /api/v1/sites/{site_id}/synthetic_test/search`

## Description

Search Site Synthetic Testing

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| mac | string | No |  |  | Device MAC Address |
| port_id | string | No |  |  | Port_id used to run the test (for SSR only) |
| vlan_id | string | No |  |  | VLAN ID |
| by | string | No |  |  | Entity who triggers the test |
| reason | string | No |  |  | Test failure reason |
| type | string | No |  |  | Synthetic test type |
| protocol | string | No |  |  | Connectivity protocol |
| tenant | string | No |  |  | Tenant network in which lan_connectivity test was run |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

## Request Body

None.

## Response

### 200

Synthetic Test Search Result

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "next": {
      "type": "string"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "synthetictest_info",
        "type": "object",
        "properties": {
          "by": {
            "type": "string",
            "examples": [
              "user"
            ]
          },
          "device_type": {
            "type": "string",
            "description": "enum: `ap`, `gateway`, `switch`"
          },
          "failed": {
            "type": "boolean",
            "examples": [
              false
            ]
          },
          "latency": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              40
            ]
          },
          "mac": {
            "type": "string"
          },
          "port_id": {
            "type": "string",
            "examples": [
              "ge-0/0/2"
            ]
          },
          "reason": {
            "type": "string",
            "examples": [
              "interface not ready to perform test"
            ]
          },
          "rx_mbps": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              322
            ]
          },
          "start_time": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              1675718807
            ]
          },
          "status": {
            "type": "string"
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "tx_mbps": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              199
            ]
          },
          "type": {
            "type": "string",
            "description": "enum: `arp`, `curl`, `dhcp`, `dhcp6`, `dns`, `lan_connectivity`, `radius`, `speedtest`"
          },
          "vlan_id": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              20
            ]
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "end",
    "limit",
    "results",
    "start",
    "total"
  ]
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.synthetic_tests.searchSiteSyntheticTest()`

## Usage Context

Searches synthetic test results at a site. Synthetic tests are automated connectivity/performance tests run by APs.

## Gotchas

- Synthetic tests must be configured in site settings before results appear.

## Related Endpoints

- [GET_sites_site_id_devices_device_id_synthetic_test.md](GET_sites_site_id_devices_device_id_synthetic_test.md) — Per-device synthetic test
- [GET_sites_site_id_setting.md](GET_sites_site_id_setting.md) — Site settings (synthetic test config)

## MistHelper Notes

Not currently used by MistHelper directly.
