# lookup

> lookup

## HTTP

`POST /api/v1/login/lookup`

## Description

Login Lookup

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
      "type": "string"
    }
  },
  "required": [
    "email"
  ],
  "description": "Request Body"
}
```

## Response

### 200

Account exists

```json
{
  "type": "object",
  "properties": {
    "sso_url": {
      "type": "string"
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
| 404 | User does not exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.admins.lookup.lookup()`

## Usage Context

Use this endpoint to determine the correct authentication method for an email address before login. Common use cases:

- Checking whether an account uses password login, SSO, or OAuth2 before presenting the appropriate login form
- Discovering the SSO provider URL for accounts configured with SAML/OAuth2 SSO

## Gotchas

- Always call this endpoint before `POST /api/v1/login` to determine the correct authentication flow
- The response indicates whether the account uses SSO and which provider, preventing unnecessary password login attempts
- Returns login method info even if the email is not registered (to prevent email enumeration)

## Related Endpoints

- [POST_login.md](POST_login.md) -- Log in with email/password after lookup confirms password authentication
- [POST_login_oauth_provider.md](POST_login_oauth_provider.md) -- Log in via OAuth2 if lookup indicates OAuth2 provider
- [POST_login_two_factor.md](POST_login_two_factor.md) -- Complete 2FA after password login

## MistHelper Notes

Not currently used by MistHelper. MistHelper uses API token authentication via the `mistapi` SDK.
