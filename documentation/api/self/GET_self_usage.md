# getSelfApiUsage

> getSelfApiUsage

## HTTP

`GET /api/v1/self/usage`

## Description

Get the status of the API usage for the current user or API Token

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
    "request_limit": {
      "type": "integer",
      "description": "max number of request permitted",
      "contentEncoding": "int32",
      "readOnly": true
    },
    "requests": {
      "type": "integer",
      "description": "num of request made in the current hour",
      "contentEncoding": "int32",
      "readOnly": true
    },
    "seconds": {
      "type": "number"
    }
  },
  "required": [
    "request_limit",
    "requests"
  ]
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

`mistapi.api.v1.self.account.getSelfApiUsage()`

## Usage Context

Use this endpoint to retrieve API usage statistics for the current admin. Common use cases:

- Monitoring API consumption against rate limits
- Tracking usage patterns over time for capacity planning
- Implementing adaptive rate limiting based on current usage

## Gotchas

- Returns usage data for the currently authenticated admin/token only
- Usage counters may have a slight delay in updating after API calls
- Rate limits are enforced per-token, so usage stats help predict when throttling may occur

## Related Endpoints

- [GET_self.md](GET_self.md) -- View current admin profile
- [GET_self_apitokens.md](GET_self_apitokens.md) -- List API tokens (usage is tracked per-token)

## MistHelper Notes

Used internally by MistHelper for **adaptive rate limiting**. MistHelper calls `getSelfApiUsage()` to monitor API consumption and dynamically adjust request pacing to avoid rate limit errors. This is not a user-facing menu operation but is critical to MistHelper's rate limiting subsystem (see `delay_metrics.json` and `tuning_data.json`).
