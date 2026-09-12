# verifyRegistration

> verifyRegistration

## HTTP

`POST /api/v1/register/verify/{token}`

## Description

Verify registration

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| token | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "detail": {
      "type": "string"
    },
    "invite_not_applied": {
      "type": "boolean"
    },
    "min_length": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "return_to": {
      "type": "string"
    }
  }
}
```

## Errors

| Status | Description |
|--------|-------------|
| 400 | Response if verification expired or already registered |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Response if secret is invalid |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.admins.admins.verifyRegistration()`

## Usage Context

Use this endpoint to verify the registration token from the confirmation email and activate a new admin account. Common use cases:

- Completing the registration flow by confirming the email address
- Activating a newly registered admin account

## Gotchas

- The `{token}` is single-use and time-limited -- it expires if not used promptly after registration
- Must match the token sent to the email address provided during `POST /api/v1/register`
- After successful verification, the admin account is activated and can log in

## Related Endpoints

- [POST_register.md](POST_register.md) -- Register a new admin account (sends the verification email)
- [GET_register_recaptcha.md](GET_register_recaptcha.md) -- Get reCAPTCHA site key for registration
- [POST_login.md](POST_login.md) -- Log in after account verification is complete

## MistHelper Notes

Not currently used by MistHelper. MistHelper does not implement admin registration workflows.
