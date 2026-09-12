# verifyRecoverPassword

> verifyRecoverPassword

## HTTP

`POST /api/v1/recover/verify/{token}`

## Description

Verify Recover Password
With correct verification, the user will be authenticated. UI can then prompt for new password

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

`mistapi.api.v1.admins.recover_password.verifyRecoverPassword()`

## Usage Context

Use this endpoint to verify the password recovery token and set a new password. Common use cases:

- Completing the password reset flow after clicking the recovery link from email
- Setting a new password using the recovery token

## Gotchas

- The `{token}` is single-use and time-limited -- it expires if not used promptly
- Must match the token sent to the email address via `POST /api/v1/recover`
- After successful verification and password reset, log in with the new password via `POST /api/v1/login`

## Related Endpoints

- [POST_recover.md](POST_recover.md) -- Initiate password recovery (sends the recovery email)
- [POST_login.md](POST_login.md) -- Log in after password recovery is complete

## MistHelper Notes

Not currently used by MistHelper. MistHelper does not implement password recovery workflows.
