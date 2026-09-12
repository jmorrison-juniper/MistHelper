# updateApiToken

> updateApiToken

## HTTP

`PUT /api/v1/self/apitokens/{apitoken_id}`

## Description

Update User API Token

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| apitoken_id | string | Yes |  |

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

`mistapi.api.v1.self.api_token.updateApiToken()`

## Usage Context

Use this endpoint to update an existing API token's name or properties. Common use cases:

- Renaming a token for better identification
- Updating token metadata without regenerating the secret

## Gotchas

- Cannot change the token secret itself -- delete and recreate the token if a new secret is needed
- Only the fields included in the request body are updated; omitted fields remain unchanged

## Related Endpoints

- [GET_self_apitokens_apitoken_id.md](GET_self_apitokens_apitoken_id.md) -- Get current token details before updating
- [GET_self_apitokens.md](GET_self_apitokens.md) -- List all tokens
- [DELETE_self_apitokens_apitoken_id.md](DELETE_self_apitokens_apitoken_id.md) -- Delete the token instead

## MistHelper Notes

Not currently used by MistHelper.
