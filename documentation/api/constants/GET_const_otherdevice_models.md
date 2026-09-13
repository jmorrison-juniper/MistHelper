# listSupportedOtherDeviceModels

> listSupportedOtherDeviceModels

## HTTP

`GET /api/v1/const/otherdevice_models`

## Description

Supported OtherDevice Models

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "array",
  "items": {
    "title": "const_other_device_model",
    "type": "object",
    "properties": {
      "_vendor_model_id": {
        "type": "string"
      },
      "display": {
        "type": "string"
      },
      "model": {
        "type": "string"
      },
      "type": {
        "type": "string"
      },
      "vendor": {
        "type": "string"
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "_vendor_model_id": "65",
        "display": "W1850",
        "model": "W1850",
        "type": "router",
        "vendor": "cradlepoint"
      }
    ]
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

`mistapi.api.v1.constants.models.listSupportedOtherDeviceModels()`

## Usage Context

Returns the list of supported third-party (non-Juniper) device models that can be monitored by the Mist platform via SNMP or similar protocols. Use this to determine which vendor devices are compatible with Mist monitoring and management.

## Gotchas

- "Other devices" have limited management capabilities compared to native Juniper devices — monitoring only, not full configuration management.
- No known gotchas with the endpoint itself; the response is a static reference list.

## Related Endpoints

- [GET_const_device_models.md](GET_const_device_models.md) — Native Juniper device models
- [GET_const_otherdevice_events.md](GET_const_otherdevice_events.md) — Event types for third-party devices

## MistHelper Notes

Not currently used by MistHelper directly.
