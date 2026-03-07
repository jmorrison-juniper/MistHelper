# generateSecretFor2faVerification

> generateSecretFor2faVerification

## HTTP

`GET /api/v1/self/two_factor/token`

## Description

Generate Secret Key for 2FA verification

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| by | string | No |  |  | If `by`==`qrcode`, returns the secret as a qrcode image |

## Request Body

None.

## Response

### 200

Two Factor configuration Token

```json
{
  "type": "object",
  "properties": {
    "two_factor_secret": {
      "type": "string",
      "examples": [
        "NRMTSTRWNBVECY3GJVYEY3DDJFRGSNCZGJUDO4RVN5FDM3DUMJSA"
      ]
    }
  }
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

`mistapi.api.v1.self.mfa.generateSecretFor2faVerification()`

## Usage Context

Use this endpoint to generate the secret key and QR code for setting up two-factor authentication. Common use cases:

- Configuring a TOTP authenticator app (Google Authenticator, Authy, etc.) for the first time
- Regenerating the 2FA secret if the authenticator app is lost

## Gotchas

- The secret is only valid until verified via `POST /api/v1/self/two_factor/verify` -- generate and verify in the same session
- After successful verification, 2FA becomes required for all future logins
- Store the secret or recovery codes securely; losing access to the authenticator app without recovery codes may lock out the account

## Related Endpoints

- [POST_self_two_factor_verify.md](POST_self_two_factor_verify.md) -- Verify the 2FA setup with a TOTP code
- [../admins/POST_login_two_factor.md](../admins/POST_login_two_factor.md) -- Submit 2FA code during login
- [GET_self.md](GET_self.md) -- Check if 2FA is already enabled on the account

## MistHelper Notes

Not currently used by MistHelper.
