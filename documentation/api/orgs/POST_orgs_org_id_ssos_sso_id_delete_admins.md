# deleteOrgSsoAdmins

> deleteOrgSsoAdmins

## HTTP

`POST /api/v1/orgs/{org_id}/ssos/{sso_id}/delete_admins`

## Description

Remove SSO-linked organization administrator accounts by email for this SSO profile.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "additionalProperties": false,
  "description": "Request body listing SSO admin email addresses to delete",
  "properties": {
    "emails": {
      "description": "List of admin email addresses to delete",
      "items": {
        "type": "string"
      },
      "type": "array"
    }
  },
  "required": [
    "emails"
  ],
  "type": "object"
}
```

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Result of deleting SSO admin accounts",
  "properties": {
    "deleted": {
      "description": "List of email addresses that were successfully deleted",
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "errors": {
      "description": "List of error messages for emails that could not be deleted",
      "items": {
        "type": "string"
      },
      "type": "array"
    }
  },
  "type": "object"
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

`mistapi.api.v1.orgs.sso.deleteOrgSsoAdmins()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
