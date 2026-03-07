# testSiteWlanTwilioSetup

> testSiteWlanTwilioSetup

## HTTP

`POST /api/v1/utils/test_twilio`

## Description

Allows validation of twilio setup
In case of success, a text message confirming successful setup should be received. In case of error, twilio error code and message are returned.

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
    "from": {
      "type": "string",
      "description": "One of the numbers you have in your Twilio account",
      "examples": [
        "+185051234567"
      ]
    },
    "to": {
      "type": "string",
      "description": "Phone number of the recipient of SMS",
      "examples": [
        "+19999999999"
      ]
    },
    "twilio_auth_token": {
      "type": "string",
      "description": "Auth Token associated with twilio account",
      "examples": [
        "2135be04736a1a0a314bce432d61721a"
      ]
    },
    "twilio_sid": {
      "type": "string",
      "description": "Twilio Account SID",
      "examples": [
        "AC5f4366878d193fb4865ab151739999eb"
      ]
    }
  },
  "required": [
    "from",
    "to",
    "twilio_auth_token",
    "twilio_sid"
  ],
  "description": "Request Body"
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

`mistapi.api.v1.utilities.wi-fi.testSiteWlanTwilioSetup()`

## Usage Context

Tests Twilio SMS gateway integration. Sends a test SMS message to verify the WLAN guest portal SMS configuration for Twilio-based deployments.

## Gotchas

- Requires valid Twilio Account SID and Auth Token configured in the WLAN settings.
- Test messages consume Twilio SMS credits.

## Related Endpoints

- [POST_utils_test_smsglobal.md](POST_utils_test_smsglobal.md) — Test SMSGlobal gateway
- [POST_utils_test_telstra.md](POST_utils_test_telstra.md) — Test Telstra gateway

## MistHelper Notes

Not currently used by MistHelper directly.
