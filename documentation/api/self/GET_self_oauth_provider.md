# getOauth2UrlForLinking

> getOauth2UrlForLinking

## HTTP

`GET /api/v1/self/oauth/{provider}`

## Description

Obtain Authorization URL for Linking

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
| forward | string | No |  |  |  |

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
    "linked": {
      "type": "boolean"
    }
  },
  "required": [
    "authorization_url",
    "linked"
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

`mistapi.api.v1.self.oauth2.getOauth2UrlForLinking()`

## Usage Context

Use this endpoint to get the OAuth2 authorization URL for linking an OAuth2 provider to the current admin account. Common use cases:

- Setting up OAuth2-based login (Google, Azure AD) for an existing password-based account
- Adding a second OAuth2 provider for alternative login methods

## Gotchas

- This is for linking an OAuth2 provider to an existing account, not for login. For login, use the admins OAuth2 endpoints
- The `{provider}` path parameter must match a supported provider name
- The returned URL redirects the browser to the provider for authorization

## Related Endpoints

- [POST_self_oauth_provider.md](POST_self_oauth_provider.md) -- Complete the OAuth2 linking after authorization
- [../admins/GET_login_oauth_provider.md](../admins/GET_login_oauth_provider.md) -- OAuth2 login flow (different from account linking)
- [GET_self.md](GET_self.md) -- Check current account details and linked providers

## MistHelper Notes

Not currently used by MistHelper.
