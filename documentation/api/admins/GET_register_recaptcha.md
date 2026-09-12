# getAdminRegistrationInfo

> getAdminRegistrationInfo

## HTTP

`GET /api/v1/register/recaptcha`

## Description

Get Registration Information

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| recaptcha_flavor | string | No |  |  |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "flavor": {
      "type": "string",
      "description": "flavor of the captcha. enum: `google`, `hcaptcha`"
    },
    "required": {
      "type": "boolean"
    },
    "sitekey": {
      "type": "string"
    }
  }
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

`mistapi.api.v1.admins.admins.getAdminRegistrationInfo()`

## Usage Context

Use this endpoint to retrieve the reCAPTCHA site key needed for the admin registration form. Common use cases:

- Building a custom registration page that needs to display a reCAPTCHA challenge
- Obtaining the reCAPTCHA configuration before calling `POST /api/v1/register`

## Gotchas

- This is a public endpoint that does not require authentication
- The reCAPTCHA site key must be used client-side to generate a reCAPTCHA token before submitting registration
- The reCAPTCHA flavor and configuration may change; always fetch this dynamically rather than hardcoding

## Related Endpoints

- [POST_register.md](POST_register.md) -- Register a new admin account (requires reCAPTCHA token)
- [POST_register_verify_token.md](POST_register_verify_token.md) -- Verify the registration confirmation email

## MistHelper Notes

Not currently used by MistHelper. MistHelper does not implement admin registration workflows.
