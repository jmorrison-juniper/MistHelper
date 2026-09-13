# getApiToken

> getApiToken

## HTTP

`GET /api/v1/self/apitokens/{apitoken_id}`

## Description

Get User API Token

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| apitoken_id | string | Yes |  |

## Request Body

None.

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

`mistapi.api.v1.self.api_token.getApiToken()`

## Usage Context

Use this endpoint to retrieve details of a specific API token by its ID. Common use cases:

- Checking the privileges and scope of a specific token
- Verifying token metadata (name, creation date, last used) before modification

## Gotchas

- The token secret is not returned -- it is only shown once at creation time
- Returns 404 if the token ID does not exist or belongs to another admin

## Related Endpoints

- [GET_self_apitokens.md](GET_self_apitokens.md) -- List all API tokens
- [PUT_self_apitokens_apitoken_id.md](PUT_self_apitokens_apitoken_id.md) -- Update this token
- [DELETE_self_apitokens_apitoken_id.md](DELETE_self_apitokens_apitoken_id.md) -- Delete this token

## MistHelper Notes

Not currently used by MistHelper.
