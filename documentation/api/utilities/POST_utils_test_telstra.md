# testSiteWlanTelstraSetup

> testSiteWlanTelstraSetup

## HTTP

`POST /api/v1/utils/test_telstra`

## Description

Allows validation of Telstra sms gateway credentials.

In case of success, a text message confirming successful setup should be received. In case of error, telstra error message are returned.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "telstra_client_id": {
      "type": "string",
      "description": "Telstra client id",
      "examples": [
        "123456"
      ]
    },
    "telstra_client_secret": {
      "type": "string",
      "description": "Telstra client secret",
      "examples": [
        "abcdef"
      ]
    },
    "to": {
      "type": "string",
      "description": "Phone number of the recipient of SMS with country code",
      "examples": [
        "+911122334455"
      ]
    }
  },
  "required": [
    "telstra_client_id",
    "telstra_client_secret",
    "to"
  ]
}
```

## Response

### 200

OK

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

`mistapi.api.v1.utilities.wi-fi.testSiteWlanTelstraSetup()`

## Usage Context

Tests Telstra SMS gateway integration. Sends a test SMS message to verify the WLAN guest portal SMS configuration for Telstra-based deployments (Australia/Asia-Pacific).

## Gotchas

- Requires valid Telstra API credentials configured in the WLAN settings.
- Test messages consume SMS credits.

## Related Endpoints

- [POST_utils_test_smsglobal.md](POST_utils_test_smsglobal.md) — Test SMSGlobal gateway
- [POST_utils_test_twilio.md](POST_utils_test_twilio.md) — Test Twilio gateway

## MistHelper Notes

Not currently used by MistHelper directly.
