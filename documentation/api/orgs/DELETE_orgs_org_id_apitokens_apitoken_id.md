# deleteOrgApiToken

> deleteOrgApiToken

## HTTP

`DELETE /api/v1/orgs/{org_id}/apitokens/{apitoken_id}`

## Description

Delete Org API Token

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
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

`mistapi.api.v1.orgs.api_tokens.deleteOrgApiToken()`

## Usage Context

Revokes a specific API token for the organization.

## Gotchas

- Revoking a token immediately invalidates all API calls using it.

## Related Endpoints

- [GET_orgs_org_id_apitokens.md](GET_orgs_org_id_apitokens.md) — List tokens
- [POST_orgs_org_id_apitokens.md](POST_orgs_org_id_apitokens.md) — Create token

## MistHelper Notes

Used by MistHelper via `listOrgApiTokens` in Menu 54 (API tokens export).
