# getSiteDeviceIotPort

> getSiteDeviceIotPort

## HTTP

`GET /api/v1/sites/{site_id}/devices/{device_id}/iot`

## Description

Returns the current state of each enabled IoT pin configured as an output.

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

`mistapi.api.v1.sites.devices_-_wireless.getSiteDeviceIotPort()`

## Usage Context

Retrieves IoT (Internet of Things) configuration for a device, including BLE and IoT port settings.

## Gotchas

- Only AP models with IoT expansion ports support this endpoint.

## Related Endpoints

- [GET_sites_site_id_devices_device_id.md](GET_sites_site_id_devices_device_id.md) — Full device config
- [PUT_sites_site_id_devices_device_id.md](PUT_sites_site_id_devices_device_id.md) — Update device

## MistHelper Notes

Not currently used by MistHelper directly.
