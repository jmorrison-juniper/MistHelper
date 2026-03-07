# createApiToken

> createApiToken

## HTTP

`POST /api/v1/self/apitokens`

## Description

Create API Token
Note that the key is only available during creation time.

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
}
```

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

`mistapi.api.v1.self.api_token.createApiToken()`

## Usage Context

Use this endpoint to create a new API token for programmatic access. Common use cases:

- Generating a token for automation scripts or CI/CD pipelines
- Creating a dedicated token for MistHelper or other tools
- Setting up service accounts with specific privilege scopes

## Gotchas

- The token secret is only returned once in the creation response -- store it securely immediately
- Token privileges are inherited from the admin's current privileges unless explicitly scoped
- There may be a maximum number of active tokens per admin account

## Related Endpoints

- [GET_self_apitokens.md](GET_self_apitokens.md) -- List all existing tokens
- [GET_self_apitokens_apitoken_id.md](GET_self_apitokens_apitoken_id.md) -- Get details of the created token
- [PUT_self_apitokens_apitoken_id.md](PUT_self_apitokens_apitoken_id.md) -- Update the token
- [DELETE_self_apitokens_apitoken_id.md](DELETE_self_apitokens_apitoken_id.md) -- Revoke the token

## MistHelper Notes

Not directly called as a menu operation, but MistHelper relies on API tokens created through this endpoint for all authentication. The token is configured via the `.env` file or `mistapi` SDK login flow.
