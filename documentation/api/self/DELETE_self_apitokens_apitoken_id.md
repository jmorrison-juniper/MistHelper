# deleteApiToken

> deleteApiToken

## HTTP

`DELETE /api/v1/self/apitokens/{apitoken_id}`

## Description

Delete an API Token

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

`mistapi.api.v1.self.api_token.deleteApiToken()`

## Usage Context

Use this endpoint to revoke and permanently delete a specific API token. Common use cases:

- Revoking a compromised or leaked token immediately
- Cleaning up unused tokens during security audits
- Rotating tokens by deleting old ones after creating replacements

## Gotchas

- Deletion is immediate and irreversible -- any automation using this token will lose access instantly
- Returns 404 if the token ID does not exist or belongs to another admin

## Related Endpoints

- [GET_self_apitokens.md](GET_self_apitokens.md) -- List all tokens to find the one to delete
- [POST_self_apitokens.md](POST_self_apitokens.md) -- Create a replacement token
- [GET_self_apitokens_apitoken_id.md](GET_self_apitokens_apitoken_id.md) -- Verify token details before deletion

## MistHelper Notes

Not currently used by MistHelper.
