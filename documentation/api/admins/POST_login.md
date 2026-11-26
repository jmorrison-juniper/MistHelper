# login

> login

## HTTP

`POST /api/v1/login`

## Description

Log in with email/password.
When 2FA is enabled, there are two ways to login:
1. login with two_factor token (with Google Authenticator, etc) 
2. login with email/password, generate the token, and use /login/two_factor with the token

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
      "type": "string",
      "examples": [
        "operator@example.invalid"
      ]
    },
    "password": {
      "type": "string",
      "examples": [
        "foryoureyesonly"
      ]
    },
    "two_factor": {
      "type": "string",
      "examples": [
        "123456"
      ]
    }
  },
  "required": [
    "email",
    "password"
  ]
}
```

## Response

### 200

Login Success

```json
{
  "type": "object",
  "properties": {
    "email": {
      "type": "string"
    },
    "two_factor_passed": {
      "type": "boolean"
    },
    "two_factor_required": {
      "type": "boolean"
    }
  }
}
```

## Errors

| Status | Description |
|--------|-------------|
| 400 | Login Failed |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.admins.login.login()`

## Usage Context

Use this endpoint to authenticate with email and password to obtain a session. Common use cases:

- Logging in to the Mist API for interactive session-based access
- Initiating a two-factor authentication flow when 2FA is enabled on the account
- Programmatic login when API token authentication is not available

## Gotchas

- If 2FA is enabled, the response includes `two_factor_required: true` and you must follow up with `POST /api/v1/login/two_factor` to complete authentication
- Call `POST /api/v1/login/lookup` first to determine whether the account uses password, SSO, or OAuth2 login before calling this endpoint
- Returns a session cookie, not an API token. For long-lived programmatic access, use API tokens instead

## Related Endpoints

- [POST_login_lookup.md](POST_login_lookup.md) -- Determine login method before authentication
- [POST_login_two_factor.md](POST_login_two_factor.md) -- Complete 2FA after initial login
- [POST_logout.md](POST_logout.md) -- End the authenticated session
- [GET_login_oauth_provider.md](GET_login_oauth_provider.md) -- Alternative OAuth2 login flow

## MistHelper Notes

MistHelper calls this endpoint through the `mistapi` SDK in two places. The interactive login (`--login`, or menu 143) asks for the cloud, the email, and the password in the terminal. The upgrade capture portal (port 8056) offers the same login on a browser page. A run with an API token never calls this endpoint. The operations portal (port 8055) has no sign-in page, so start it with `--login --web-portal` or with a token. See [Sign in for an MSP run](../../operator-guide.md#sign-in-for-an-msp-run).
