# listApLedDefinition

> listApLedDefinition

## HTTP

`GET /api/v1/const/ap_led_status`

## Description

Get List of AP LED definition

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of AP Led Status

```json
{
  "type": "array",
  "items": {
    "title": "const_ap_led",
    "required": [
      "code",
      "description",
      "key",
      "name"
    ],
    "type": "object",
    "properties": {
      "code": {
        "type": "string",
        "examples": [
          "01"
        ]
      },
      "description": {
        "type": "string",
        "examples": [
          "LED not working"
        ]
      },
      "key": {
        "type": "string",
        "examples": [
          "LED_FAILURE"
        ]
      },
      "name": {
        "type": "string",
        "examples": [
          "LED Failure"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "code": "01",
        "description": "LED not working",
        "key": "LED_FAILURE",
        "name": "LED Failure"
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

`mistapi.api.v1.constants.definitions.listApLedDefinition()`

## Usage Context

Returns the list of AP LED color/pattern definitions and their meanings (e.g., solid green = connected, blinking amber = upgrading). Use this as a reference for field technicians interpreting AP status from LED behavior during installation or troubleshooting.

## Gotchas

- LED behavior varies by AP model generation — some older APs may have fewer LED states.
- No known gotchas with the endpoint itself; the response is a static reference list.

## Related Endpoints

- [GET_const_device_models.md](GET_const_device_models.md) — AP hardware models (LED capabilities vary by model)
- [../installer/POST_installer_orgs_org_id_devices_device_mac_locate.md](../installer/POST_installer_orgs_org_id_devices_device_mac_locate.md) — Trigger LED locate/blink on a specific AP

## MistHelper Notes

Not currently used by MistHelper directly.
