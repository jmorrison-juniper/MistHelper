# listApiTokens

> listApiTokens

## HTTP

`GET /api/v1/self/apitokens`

## Description

Get List of Current User API Tokens

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
  "type": "array",
  "items": {
    "title": "user_apitoken",
    "type": "object",
    "properties": {
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "id": {
        "type": "string",
        "description": "Unique ID of the object instance in the Mist Organization",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "53f10664-3ce8-4c27-b382-0ef66432349f"
        ]
      },
      "key": {
        "type": "string",
        "readOnly": true,
        "examples": [
          "1qkb...QQCL"
        ]
      },
      "last_used": {
        "type": [
          "integer",
          "null"
        ],
        "contentEncoding": "int32",
        "readOnly": true,
        "examples": [
          1690115110
        ]
      },
      "name": {
        "type": "string",
        "description": "Name of the token",
        "examples": [
          "org_token_xyz"
        ]
      }
    },
    "description": "User API Token"
  },
  "description": "",
  "examples": [
    [
      {
        "created_time": 1626875902,
        "id": "864f351a-1377-4ad9-83f8-72f3fe6199ba",
        "key": "1qkb...QQCL",
        "last_used": 1690115110,
        "name": "org_token_xyz"
      }
    ]
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

`mistapi.api.v1.self.api_token.listApiTokens()`

## Usage Context

Use this endpoint to list all API tokens associated with the current admin. Common use cases:

- Auditing existing API tokens for security review
- Checking which tokens are active before creating new ones
- Identifying tokens that should be rotated or deleted

## Gotchas

- Token secrets are not returned in the list -- only metadata (name, created date, last used, privileges)
- Tokens with expired privileges may still appear in the list

## Related Endpoints

- [POST_self_apitokens.md](POST_self_apitokens.md) -- Create a new API token
- [GET_self_apitokens_apitoken_id.md](GET_self_apitokens_apitoken_id.md) -- Get details of a specific token
- [PUT_self_apitokens_apitoken_id.md](PUT_self_apitokens_apitoken_id.md) -- Update a token
- [DELETE_self_apitokens_apitoken_id.md](DELETE_self_apitokens_apitoken_id.md) -- Revoke a token

## MistHelper Notes

Used by Menu Operation **54** (Export API Tokens). MistHelper's `OrgAdminExporter.api_tokens` calls this to list and export API token metadata.
