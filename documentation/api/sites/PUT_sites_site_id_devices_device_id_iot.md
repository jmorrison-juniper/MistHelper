# setSiteDeviceIotPort

> setSiteDeviceIotPort

## HTTP

`PUT /api/v1/sites/{site_id}/devices/{device_id}/iot`

## Description

**Note**: For each IoT pin referenced:
 * The pin must be enabled using the Device `iot_config` API
 * The pin must support the output direction

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
  "additionalProperties": {
    "type": "integer",
    "format": "int32"
  },
  "description": "Request Body"
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "additionalProperties": {
    "type": "integer",
    "format": "int32"
  },
  "description": "Property key is the IoT port name (e.g. \"A1\")",
  "examples": [
    {
      "A1": 1,
      "DO": 0
    }
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.devices_-_wireless.setSiteDeviceIotPort()`

## Usage Context

Updates IoT configuration for a device, such as BLE/IoT output settings.

## Gotchas

- Only supported on APs with IoT capabilities (e.g., AP43/AP63).

## Related Endpoints

- [PUT_sites_site_id_devices_device_id.md](PUT_sites_site_id_devices_device_id.md) — Update device
- [GET_sites_site_id_devices_device_id.md](GET_sites_site_id_devices_device_id.md) — Device details

## MistHelper Notes

Not currently used by MistHelper directly.
