# getOauth2AuthorizationUrlForLogin

> getOauth2AuthorizationUrlForLogin

## HTTP

`GET /api/v1/login/oauth/{provider}`

## Description

Obtain Authorization URL for Login

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| provider | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| forward | string | No |  |  | Callback URL |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "authorization_url": {
      "type": "string"
    },
    "client_id": {
      "type": "string"
    }
  },
  "required": [
    "authorization_url",
    "client_id"
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

`mistapi.api.v1.admins.login_-_oauth2.getOauth2AuthorizationUrlForLogin()`

## Usage Context

Use this endpoint to obtain the OAuth2 authorization URL for a specific provider to initiate OAuth2-based login. Common use cases:

- Getting the redirect URL for Google, Microsoft Azure AD, or other configured OAuth2 providers
- Building a login page that supports SSO via OAuth2 alongside password authentication

## Gotchas

- The `{provider}` path parameter must match a supported OAuth2 provider name (e.g., `google`, `azure`)
- The returned URL is a redirect target -- the browser should navigate to it, not call it as an API
- After the OAuth2 flow completes, the callback redirects to `POST /api/v1/login/oauth/{provider}` to finalize login

## Related Endpoints

- [POST_login_oauth_provider.md](POST_login_oauth_provider.md) -- Complete OAuth2 login after authorization callback
- [DELETE_login_oauth_provider.md](DELETE_login_oauth_provider.md) -- Unlink an OAuth2 provider from the account
- [POST_login_lookup.md](POST_login_lookup.md) -- Determine if OAuth2 is the login method for an email

## MistHelper Notes

Not currently used by MistHelper. MistHelper uses API token authentication and does not implement OAuth2 login flows.
