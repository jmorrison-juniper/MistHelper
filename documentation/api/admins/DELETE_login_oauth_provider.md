# unlinkOauth2Provider

> unlinkOauth2Provider

## HTTP

`DELETE /api/v1/login/oauth/{provider}`

## Description

Unlink OAuth2 Provider

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| provider | string | Yes |  |

## Request Body

None.

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

`mistapi.api.v1.admins.login_-_oauth2.unlinkOauth2Provider()`

## Usage Context

Use this endpoint to disconnect an OAuth2 provider (Google, Azure AD, etc.) from your Mist admin account. Common use cases:

- Removing a linked OAuth2 provider when switching to a different authentication method
- Cleaning up OAuth2 links when decommissioning an identity provider

## Gotchas

- Ensure you have an alternative login method (password or another OAuth2 provider) configured before unlinking, otherwise you may lose access to the account
- The `{provider}` path parameter must match the exact provider name that was previously linked

## Related Endpoints

- [GET_login_oauth_provider.md](GET_login_oauth_provider.md) -- Get the OAuth2 authorization URL for login
- [POST_login_oauth_provider.md](POST_login_oauth_provider.md) -- Log in via OAuth2
- [POST_login.md](POST_login.md) -- Alternative password-based login
- [../self/GET_self_oauth_provider.md](../self/GET_self_oauth_provider.md) -- View currently linked OAuth2 providers

## MistHelper Notes

Not currently used by MistHelper. MistHelper uses API token authentication and does not manage OAuth2 provider links.
