# verifySelfEmail

> verifySelfEmail

## HTTP

`GET /api/v1/self/update/verify/{token}`

## Description

Verify Email change

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| token | string | Yes |  |

## Request Body

None.

## Response

### 200

With correct verification, the email address of the user will be updated

## Errors

| Status | Description |
|--------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.self.account.verifySelfEmail()`

## Usage Context

Use this endpoint to verify the email update token and complete an email address change. Common use cases:

- Confirming a new email address after initiating a change via `POST /api/v1/self/update`
- Clicking the verification link from the email to finalize the address change

## Gotchas

- The `{token}` is single-use and time-limited
- After successful verification, the admin's email is updated to the new address
- The old email address can no longer be used for login after verification

## Related Endpoints

- [POST_self_update.md](POST_self_update.md) -- Initiate the email change (sends verification email)
- [GET_self.md](GET_self.md) -- View updated profile after email change

## MistHelper Notes

Not currently used by MistHelper.
