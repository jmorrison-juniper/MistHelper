# loginOauth2

> loginOauth2

## HTTP

`POST /api/v1/login/oauth/{provider}`

## Description

Login via OAuth2

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| provider | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "code": {
      "type": "string"
    }
  },
  "required": [
    "code"
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

`mistapi.api.v1.admins.login_-_oauth2.loginOauth2()`

## Usage Context

Use this endpoint to complete OAuth2 login after the user authorizes via the OAuth2 provider. Common use cases:

- Finalizing login after the OAuth2 authorization callback returns an authorization code
- Linking an OAuth2 provider to an existing Mist account during the login flow

## Gotchas

- Requires the authorization code from the OAuth2 provider callback URL
- The `{provider}` path parameter must match the provider used in `GET /api/v1/login/oauth/{provider}`
- If the OAuth2 account is not yet linked to a Mist account, the API may return instructions for account linking

## Related Endpoints

- [GET_login_oauth_provider.md](GET_login_oauth_provider.md) -- Get the OAuth2 authorization URL to start the flow
- [DELETE_login_oauth_provider.md](DELETE_login_oauth_provider.md) -- Unlink an OAuth2 provider from the account
- [POST_login.md](POST_login.md) -- Alternative password-based login

## MistHelper Notes

Not currently used by MistHelper. MistHelper uses API token authentication and does not implement OAuth2 login flows.
