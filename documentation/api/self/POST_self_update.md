# updateSelfEmail

> updateSelfEmail

## HTTP

`POST /api/v1/self/update`

## Description

Change Email
We require the user to verify that they actually own the email address they intend to change it to.

After the API call, the user will receive an email to the new email address with a link like https://manage.mist.com/verify/update?expire=:exp_time&email=:admin_email&token=:token

Upon clicking the link, the user is provided with a login page to authenticate using existing credentials. After successful login, the email address of the user gets updated

**Note**: The request parameter email can be used by UI to validate that the current session (if any) belongs to the admin or provide a login page (by pre-populating the email on login screen). UI can also use the request parameter expire to validate token expiry.

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
    "email": {
      "type": "string"
    }
  },
  "required": [
    "email"
  ],
  "description": "Request Body"
}
```

## Response

### 200

OK

## Errors

| Status | Description |
|--------|-------------|
| 400 | Invalid email address or new email address already exists |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.self.account.updateSelfEmail()`

## Usage Context

Use this endpoint to initiate an email address change for the current admin. Common use cases:

- Updating the admin's email when switching to a new corporate email address
- Correcting a typo in the registered email

## Gotchas

- Sends a verification email to the new address. The change is not applied until the token in the email is verified via `GET /api/v1/self/update/verify/{token}`
- The old email remains active until the new email is verified
- Cannot be used to change other profile fields -- use `PUT /api/v1/self` for that

## Related Endpoints

- [GET_self_update_verify_token.md](GET_self_update_verify_token.md) -- Verify the new email address
- [PUT_self.md](PUT_self.md) -- Update other profile fields (name, phone, etc.)
- [GET_self.md](GET_self.md) -- View current profile

## MistHelper Notes

Not currently used by MistHelper.
