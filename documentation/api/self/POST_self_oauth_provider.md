# linkOauth2MistAccount

> linkOauth2MistAccount

## HTTP

`POST /api/v1/self/oauth/{provider}`

## Description

Link Mist account with an OAuth2 Provider

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

```json
{
  "type": "object",
  "properties": {
    "action": {
      "type": "string"
    },
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    }
  },
  "required": [
    "action",
    "id"
  ]
}
```

## Errors

| Status | Description |
|--------|-------------|
| 400 | Authorization Error |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.self.oauth2.linkOauth2MistAccount()`

## Usage Context

Use this endpoint to link an OAuth2 provider to the current admin's Mist account. Common use cases:

- Completing the OAuth2 linking flow after authorization via `GET /api/v1/self/oauth/{provider}`
- Enabling OAuth2-based login for an account that previously used password authentication

## Gotchas

- Requires the authorization code from the OAuth2 provider callback
- The `{provider}` must match the provider used in the initial authorization URL request
- Once linked, the OAuth2 provider can be used for login via `POST /api/v1/login/oauth/{provider}`

## Related Endpoints

- [GET_self_oauth_provider.md](GET_self_oauth_provider.md) -- Get the OAuth2 authorization URL to start linking
- [../admins/DELETE_login_oauth_provider.md](../admins/DELETE_login_oauth_provider.md) -- Unlink an OAuth2 provider
- [GET_self.md](GET_self.md) -- View account with linked providers

## MistHelper Notes

Not currently used by MistHelper.
