# twoFactor

> twoFactor

## HTTP

`POST /api/v1/login/two_factor`

## Description

Send 2FA Code

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
    "two_factor": {
      "type": "string",
      "examples": [
        "123456"
      ]
    }
  },
  "required": [
    "two_factor"
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
| 401 | two_factor code is incorrect or the user hasn't login yet |
| 403 | Permission Denied |
| 404 | The user doesn't have 2FA enabled |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.admins.login.twoFactor()`

## Usage Context

Use this endpoint to complete two-factor authentication after initial login when 2FA is required. Common use cases:

- Submitting the TOTP code from an authenticator app (Google Authenticator, Authy, etc.) after `POST /api/v1/login` returns `two_factor_required: true`
- Completing the login flow for accounts with mandatory 2FA enabled

## Gotchas

- Must be called only after `POST /api/v1/login` returns `two_factor_required: true` in the response
- TOTP codes are time-limited (typically 30 seconds) so submit promptly
- The two_factor token can also be passed directly in the `POST /api/v1/login` request body to avoid this extra step

## Related Endpoints

- [POST_login.md](POST_login.md) -- Initial login that triggers the 2FA requirement
- [POST_login_lookup.md](POST_login_lookup.md) -- Determine login method before authentication
- [../self/GET_self_two_factor_token.md](../self/GET_self_two_factor_token.md) -- Get 2FA setup token for configuring authenticator app

## MistHelper Notes

Not currently used by MistHelper. MistHelper uses API token authentication and does not handle interactive 2FA flows.
