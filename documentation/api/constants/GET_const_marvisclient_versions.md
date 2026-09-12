# listMarvisClientVersions

> listMarvisClientVersions

## HTTP

`GET /api/v1/const/marvisclient_versions`

## Description

Get List of the available Marvis Client Versions.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of Webhook Topics

```json
{
  "type": "array",
  "items": {
    "title": "const_marvis_client_version",
    "type": "object",
    "properties": {
      "label": {
        "type": "string",
        "examples": [
          "default"
        ]
      },
      "notes": {
        "type": "string"
      },
      "os": {
        "type": "string",
        "description": "Client OS",
        "examples": [
          "windows"
        ]
      },
      "url": {
        "type": "string",
        "description": "Client download url",
        "examples": [
          "https://mobile.mist.com/installers/marvisclient/..."
        ]
      },
      "version": {
        "type": "string",
        "description": "Client version",
        "examples": [
          "0.100.29"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "label": "default",
        "notes": "",
        "os": "android",
        "url": "https://mobile.mist.com/installers/marvisclient/android/1.1.9/marvisclient-installer.apk",
        "version": "1.1.9"
      },
      {
        "label": "default",
        "notes": "",
        "os": "macos",
        "url": "https://mobile.mist.com/installers/marvisclient/macos/0.100.29/marvisclient-installer.dmg",
        "version": "0.100.29"
      },
      {
        "label": "default",
        "notes": "",
        "os": "windows",
        "url": "https://mobile.mist.com/installers/marvisclient/windows/0.100.26/marvisclient-installer.zip",
        "version": "0.100.26"
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

`mistapi.api.v1.constants.definitions.listMarvisClientVersions()`

## Usage Context

Returns the list of available Marvis Client agent versions. The Marvis Client is an endpoint agent that provides enhanced telemetry (wired/wireless experience metrics, synthetic testing) from end-user devices. Use this to check for client agent updates or validate deployed versions.

## Gotchas

- Marvis Client is available for Windows, macOS, iOS, and Android — version availability may differ by platform.
- Requires a Marvis license for full functionality.

## Related Endpoints

- [GET_const_device_models.md](GET_const_device_models.md) — Device models (Marvis Client runs on endpoints, not network devices)
- [GET_const_license_types.md](GET_const_license_types.md) — License types including Marvis subscriptions

## MistHelper Notes

Not currently used by MistHelper directly.
