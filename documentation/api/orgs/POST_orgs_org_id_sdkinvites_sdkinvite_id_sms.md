# sendSdkInviteSms

> sendSdkInviteSms

## HTTP

`POST /api/v1/orgs/{org_id}/sdkinvites/{sdkinvite_id}/sms`

## Description

Send SDK Invite by SMS

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| sdkinvite_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "number": {
      "type": "string"
    }
  },
  "required": [
    "number"
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

`mistapi.api.v1.orgs.sdk_invites.sendSdkInviteSms()`

## Usage Context

Sends an SMS invitation for a specific SDK invite.

## Gotchas

- Requires SMS configuration and valid phone number.

## Related Endpoints

- [GET_orgs_org_id_sdkinvites_sdkinvite_id.md](GET_orgs_org_id_sdkinvites_sdkinvite_id.md) — Get SDK invite
- [POST_orgs_org_id_sdkinvites_sdkinvite_id_email.md](POST_orgs_org_id_sdkinvites_sdkinvite_id_email.md) — Send email

## MistHelper Notes

Not currently used by MistHelper directly.
