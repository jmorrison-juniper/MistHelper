# recoverPassword

> recoverPassword

## HTTP

`POST /api/v1/recover`

## Description

Recover Password
An email will also be sent to the user with a link to https://manage.mist.com/verify/recover?token=:token

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
    "email": {
      "maxLength": 64,
      "type": "string",
      "examples": [
        "test@mistsys.com"
      ]
    },
    "recaptcha": {
      "type": "string",
      "description": "See  https://www.google.com/recaptcha/"
    },
    "recaptcha_flavor": {
      "type": "string",
      "description": "flavor of the captcha. enum: `google`, `hcaptcha`"
    }
  },
  "required": [
    "email"
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

`mistapi.api.v1.admins.recover_password.recoverPassword()`

## Usage Context

Use this endpoint to initiate password recovery by requesting a reset email. Common use cases:

- Recovering access when an admin has forgotten their password
- Initiating a forced password reset for security purposes

## Gotchas

- Always returns a success response regardless of whether the email is registered, to prevent email enumeration attacks
- The recovery link is sent to the registered email address and contains a time-limited token
- Only works for accounts using password-based authentication; SSO/OAuth2 accounts manage passwords through their identity provider

## Related Endpoints

- [POST_recover_verify_token.md](POST_recover_verify_token.md) -- Verify the recovery token and set a new password
- [POST_login.md](POST_login.md) -- Log in after password recovery is complete

## MistHelper Notes

Not currently used by MistHelper. MistHelper does not implement password recovery workflows.
