# getSiteDeviceSyntheticTest

> getSiteDeviceSyntheticTest

## HTTP

`GET /api/v1/sites/{site_id}/devices/{device_id}/synthetic_test`

## Description

Get Device Synthetic Test

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

Synthetic Test Status

```json
{
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
}
```

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

`mistapi.api.v1.sites.synthetic_tests.getSiteDeviceSyntheticTest()`

## Usage Context

Retrieves synthetic test configuration for a device. Synthetic tests validate network paths (DHCP, DNS, web connectivity, etc.) from the device.

## Gotchas

- Only APs support synthetic testing. Switches and gateways do not run synthetic tests.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_synthetic_test.md](POST_sites_site_id_devices_device_id_synthetic_test.md) — Run synthetic test
- [GET_sites_site_id_synthetic_test.md](GET_sites_site_id_synthetic_test_search.md) — Site-level synthetic test config

## MistHelper Notes

Not currently used by MistHelper directly.
