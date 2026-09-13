# listApLEslVersions

> listApLEslVersions

## HTTP

`GET /api/v1/const/ap_esl_versions`

## Description

Get Available AP ESL Versions

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of Available AP ESL Versions

```json
{
  "type": "array",
  "items": {
    "title": "const_ap_esl_version",
    "type": "object",
    "properties": {
      "esl_version": {
        "type": "string",
        "readOnly": true,
        "examples": [
          "2.5.1"
        ]
      },
      "model": {
        "type": "string",
        "readOnly": true,
        "examples": [
          "AP34"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "esl_version": "2.5.1",
        "model": "AP34"
      },
      {
        "esl_version": "2.5.0",
        "model": "AP43"
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

`mistapi.api.v1.constants.definitions.listApLEslVersions()`

## Usage Context

Returns the list of supported Electronic Shelf Label (ESL) firmware versions for APs with ESL capabilities. ESL integration allows Mist APs to communicate with electronic price tags in retail environments via BLE beacons.

## Gotchas

- ESL functionality is only available on AP models with BLE radios and ESL-specific firmware — not all APs support it.
- This is a niche retail-focused feature; most deployments will not use ESL capabilities.

## Related Endpoints

- [GET_const_device_models.md](GET_const_device_models.md) — AP models (check ESL/BLE capability)
- [GET_const_ap_channels.md](GET_const_ap_channels.md) — Channel definitions for AP radios

## MistHelper Notes

Not currently used by MistHelper directly.
