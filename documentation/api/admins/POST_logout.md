# logout

> logout

## HTTP

`POST /api/v1/logout`

## Description

Logout

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "forward_url": {
      "type": "string",
      "description": "If configured in SSO as custom_logout_url"
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

`mistapi.api.v1.admins.logout.logout()`

## Usage Context

Use this endpoint to end the current authenticated session and invalidate the session cookie. Common use cases:

- Logging out after completing interactive API operations
- Invalidating a session for security purposes

## Gotchas

- Only invalidates the current session cookie. API tokens are not affected by logout
- After logout, all subsequent requests using the same session cookie will receive 401 Unauthorized

## Related Endpoints

- [POST_login.md](POST_login.md) -- Log in to create a session
- [POST_login_oauth_provider.md](POST_login_oauth_provider.md) -- Alternative OAuth2 login

## MistHelper Notes

Not currently used by MistHelper. MistHelper uses API token authentication and does not manage interactive sessions.
