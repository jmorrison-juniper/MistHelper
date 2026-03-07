# getSelfLoginFailures

> getSelfLoginFailures

## HTTP

`GET /api/v1/self/login_failures`

## Description

Get a list of failed login attempts across all Orgs for the current admin

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "email": {
      "type": "string",
      "description": "Email address of the user",
      "examples": [
        "admin@test.com"
      ]
    },
    "last_failure_at": {
      "type": "integer",
      "description": "Last failure time",
      "contentEncoding": "int32",
      "examples": [
        1509161968
      ]
    },
    "num_attempts": {
      "type": "integer",
      "description": "Number of failed login attempts",
      "contentEncoding": "int32",
      "examples": [
        1
      ]
    },
    "src_ips": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of up to 32 unique source IP addresses, ordered with the most recent first",
      "examples": [
        [
          "192.168.1.39",
          "192.168.1.38",
          "192.168.1.37"
        ]
      ]
    },
    "user_agents": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of up to 32 unique User-Agent strings, ordered with the most recent first",
      "examples": [
        [
          "Test UA 39",
          "Test UA 38",
          "Test UA 37"
        ]
      ]
    }
  },
  "description": "Failed login attempts"
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

`mistapi.api.v1.self.account.getSelfLoginFailures()`

## Usage Context

Use this endpoint to retrieve the current admin's failed login history. Common use cases:

- Investigating potential unauthorized access attempts against your account
- Reviewing login failures after account lockout

## Gotchas

- Only shows login failures for the currently authenticated admin's account
- Successful logins are not included -- this endpoint only tracks failures
- May be useful for detecting brute-force attempts against the account

## Related Endpoints

- [GET_self.md](GET_self.md) -- View current admin profile and account status
- [GET_self_logs.md](GET_self_logs.md) -- View admin audit log history
- [../admins/POST_login.md](../admins/POST_login.md) -- Login endpoint where failures originate

## MistHelper Notes

Not currently used by MistHelper.
