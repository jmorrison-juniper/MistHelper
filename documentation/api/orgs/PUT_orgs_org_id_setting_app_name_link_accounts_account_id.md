# updateOrgOauthAppAccount

> updateOrgOauthAppAccount

## HTTP

`PUT /api/v1/orgs/{org_id}/setting/{app_name}/link_accounts/{account_id}`

## Description

Update Zoom, Teams, Intune Authorization.

Request Payload, These Field And Values Will Be Specific To Each Of The Third Party Apps Accounts.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| app_name | string | Yes | OAuth application name |
| account_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "account_id": {
      "type": "string",
      "description": "Linked app(zoom/teams/intune) account id",
      "examples": [
        "iojzXIJWEuiD73ZvydOfg"
      ]
    },
    "discard_guest_info": {
      "type": "boolean",
      "description": "Optional, for Zoom/Teams. Whether to redact identifying information for call participants that are not part of the Zoom/Teams account identified by `account_id`"
    },
    "max_daily_api_requests": {
      "type": "integer",
      "description": "Zoom daily api request quota, https://developers.zoom.us/docs/api/rest/rate-limits/",
      "contentEncoding": "int32",
      "examples": [
        5000
      ]
    }
  },
  "required": [
    "account_id"
  ],
  "description": "OAuth linked apps (zoom/teams/intune) account details"
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

`mistapi.api.v1.orgs.linked_applications.updateOrgOauthAppAccount()`

## Usage Context

Updates a linked third-party application account.

## Gotchas

- The account_id identifies the specific linked integration.

## Related Endpoints

- [POST_orgs_org_id_setting_app_name_link_accounts.md](POST_orgs_org_id_setting_app_name_link_accounts.md) — Link account
- [DELETE_orgs_org_id_setting_app_name_link_accounts.md](DELETE_orgs_org_id_setting_app_name_link_accounts.md) — Unlink

## MistHelper Notes

Not currently used by MistHelper directly.
