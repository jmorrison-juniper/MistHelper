# listOtherDeviceEventsDefinitions

> listOtherDeviceEventsDefinitions

## HTTP

`GET /api/v1/const/otherdevice_events`

## Description

Supported Events Type

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of Other Device Events definitions

```json
{
  "type": "array",
  "items": {
    "title": "const_event",
    "required": [
      "display",
      "key"
    ],
    "type": "object",
    "properties": {
      "description": {
        "type": "string"
      },
      "display": {
        "type": "string"
      },
      "example": {
        "type": "object"
      },
      "group": {
        "type": "string"
      },
      "key": {
        "type": "string"
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "display": "Connected to NCM",
        "example": {
          "device_mac": "5c5b351e13b5",
          "mac": "0030447771c0",
          "org_id": "c080ce4d-4e35-4373-bdc4-08df15d257f5",
          "site_id": "1df889ad-9111-4c0e-a00b-8a008b83eb68",
          "text": "Connected to NCM",
          "timestamp": 1675827825.765,
          "type": "CELLULAR_EDGE_CONNECTED_TO_NCM",
          "vendor": "cradlepoint"
        },
        "key": "CELLULAR_EDGE_CONNECTED_TO_NCM"
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

`mistapi.api.v1.constants.events.listOtherDeviceEventsDefinitions()`

## Usage Context

Returns definitions of event types for non-Juniper devices ("other devices") monitored by the Mist platform, such as third-party switches, routers, or IoT gateways. Use this to interpret events from devices managed via SNMP or other monitoring protocols.

## Gotchas

- "Other devices" are non-Juniper devices adopted into Mist monitoring — their event types differ from native Juniper device events.
- No known gotchas with the endpoint itself; the response is a static reference list.

## Related Endpoints

- [GET_const_device_events.md](GET_const_device_events.md) — Native Juniper device event definitions
- [GET_const_otherdevice_models.md](GET_const_otherdevice_models.md) — Supported third-party device models

## MistHelper Notes

Not currently used by MistHelper directly.
