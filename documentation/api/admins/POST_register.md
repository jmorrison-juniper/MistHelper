# registerNewAdmin

> registerNewAdmin

## HTTP

`POST /api/v1/register`

## Description

Register a new admin and his/her org
An email will also be sent to the user with a link to `/verify/register?token={token}`

### reCAPTCHA
Google reCAPTCHA is the choice to prevent bot registration

It needs this 

&lt;script src='https://www.google.com/recaptcha/api.js' &gt;&lt;/script&gt;

and this &lt;div&gt; in the desired place
```html
<div class="g-recaptcha" data_sitekey="6LdAewsTAAAAAE25XKQhPEQ2FiMTft-WrZXQ5NUd"></div>
```

Use GET /api/v1/register/recaptcha to read the current setting.
Response example:
```json
{    
  "flavor": "google",
  "required": true,    
  "sitekey": "6LdAewsTAAAAAE25XKQhPEQ2FiMTft-WrZXQ5NUd"
}
```

### hCaptcha
Alternative to reCAPTCHA is hCaptcha to prevent bot registration

It needs this script

&lt;script src='https://js.hcaptcha.com/1/api.js' async defer &gt;&lt;/script&gt;

and this &lt;div&gt; in the desired place
```html
<div class="h-recaptcha" data_sitekey="6LdAewsTAAAAAE25XKQhPEQ2FiMTft-WrZXQ5NUd"></div>
```

Use GET /api/v1/register/recaptcha?recaptcha_flavor=hcaptcha to read the current setting for hcaptcha with reply.
Response example:
```json
{
  "flavor": "hcaptcha",
  "required": true,
  "sitekey": "6LdAewsTAAAAAE25XKQhPEQ2FiMTft-WrZXQ5NUd"
}"
```

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
    "account_only": {
      "type": "boolean",
      "description": "Skip creating initial setup if true",
      "default": false
    },
    "allow_mist": {
      "type": "boolean",
      "description": "Whether to allow Mist to look at this org",
      "default": false
    },
    "city": {
      "type": "string",
      "description": "City of registering user",
      "examples": [
        "Cupertino"
      ]
    },
    "country": {
      "type": "string",
      "description": "Country/region name or ISO code of registering user",
      "examples": [
        "United States"
      ]
    },
    "email": {
      "maxLength": 64,
      "type": "string",
      "examples": [
        "test@mistsys.com"
      ]
    },
    "first_name": {
      "type": "string",
      "examples": [
        "John"
      ]
    },
    "invite_code": {
      "type": "string",
      "description": "Required initially",
      "examples": [
        "MISTROCKS"
      ]
    },
    "last_name": {
      "type": "string",
      "examples": [
        "Smith"
      ]
    },
    "org_name": {
      "type": "string",
      "examples": [
        "Smith LLC"
      ]
    },
    "password": {
      "type": "string",
      "examples": [
        "foryoureyesonly"
      ]
    },
    "recaptcha": {
      "type": "string",
      "description": "reCAPTCHA , see https://www.google.com/recaptcha/"
    },
    "recaptcha_flavor": {
      "type": "string",
      "description": "flavor of the captcha. enum: `google`, `hcaptcha`"
    },
    "referer_invite_token": {
      "type": "string",
      "description": "Invite token to apply after account creation",
      "examples": [
        "Dm2gtT8dwMeM4Bc2E8FLIaA96VHOjPat"
      ]
    },
    "return_to": {
      "type": "string",
      "description": "URL the user should be redirected back to",
      "examples": [
        "https://mist.zendesk.com/hc/quickstart.pdf"
      ]
    },
    "state": {
      "type": "string",
      "description": "State name or ISO code of registering user, optional (depends on country/region)",
      "examples": [
        "CA"
      ]
    },
    "street_address": {
      "type": "string",
      "description": "Street address of registering user",
      "examples": [
        "1601 S De Anza Blvd Ste 248"
      ]
    },
    "street_address 2": {
      "type": "string",
      "description": "Street address 2 of registering user",
      "examples": [
        "1601 S De Anza Blvd Ste 248"
      ]
    },
    "zipcode": {
      "type": "string",
      "description": "zipcode of registering user",
      "examples": [
        "95014"
      ]
    }
  },
  "required": [
    "email",
    "first_name",
    "last_name",
    "org_name",
    "password",
    "recaptcha"
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

`mistapi.api.v1.admins.admins.registerNewAdmin()`

## Usage Context

Use this endpoint to register a new Mist admin account. Common use cases:

- Creating a new admin account for first-time Mist platform access
- Self-service registration when invitations are not required

## Gotchas

- Requires a valid reCAPTCHA token obtained from `GET /api/v1/register/recaptcha` -- the request will fail without it
- The email address must not already be registered; duplicate registrations are rejected
- A verification email is sent that must be confirmed via `POST /api/v1/register/verify/{token}` to activate the account

## Related Endpoints

- [GET_register_recaptcha.md](GET_register_recaptcha.md) -- Get reCAPTCHA site key before registration
- [POST_register_verify_token.md](POST_register_verify_token.md) -- Verify registration email to activate account
- [POST_login.md](POST_login.md) -- Log in after registration is complete

## MistHelper Notes

Not currently used by MistHelper. MistHelper does not implement admin registration workflows.
