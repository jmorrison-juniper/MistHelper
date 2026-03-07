# listAlarmSubscriptions

> listAlarmSubscriptions

## HTTP

`GET /api/v1/self/subscriptions`

## Description

Get List of all the subscriptions

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
  "uniqueItems": true,
  "type": "array",
  "items": {
    "title": "response_self_subscription",
    "required": [
      "org_id"
    ],
    "type": "object",
    "properties": {
      "org_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
        ]
      }
    }
  },
  "description": ""
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

`mistapi.api.v1.self.alarms.listAlarmSubscriptions()`

## Usage Context

Use this endpoint to list the current admin's alarm notification subscriptions. Common use cases:

- Checking which alarm types are configured to send notifications to the current admin
- Auditing notification preferences before modifying subscriptions

## Gotchas

- Subscriptions are per-admin -- each admin manages their own notification preferences independently
- This endpoint returns alarm subscriptions, not to be confused with license subscriptions

## Related Endpoints

- [../sites/POST_sites_site_id_subscriptions.md](../sites/POST_sites_site_id_subscriptions.md) -- Subscribe to site-level alarm notifications
- [../sites/DELETE_sites_site_id_subscriptions.md](../sites/DELETE_sites_site_id_subscriptions.md) -- Unsubscribe from site-level alarms
- [GET_self.md](GET_self.md) -- View current admin profile

## MistHelper Notes

Not currently used by MistHelper.
