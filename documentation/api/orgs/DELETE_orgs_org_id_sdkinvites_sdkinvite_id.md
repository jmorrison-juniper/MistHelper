# revokeSdkInvite

> revokeSdkInvite

## HTTP

`DELETE /api/v1/orgs/{org_id}/sdkinvites/{sdkinvite_id}`

## Description

Revoke SDK Invite

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| sdkinvite_id | string | Yes |  |

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

`mistapi.api.v1.orgs.sdk_invites.revokeSdkInvite()`

## Usage Context

Revokes an SDK invitation.

## Gotchas

- No known gotchas.

## Related Endpoints

- [GET_orgs_org_id_sdkinvites.md](GET_orgs_org_id_sdkinvites.md) — List invitations
- [POST_orgs_org_id_sdkinvites.md](POST_orgs_org_id_sdkinvites.md) — Create invitation

## MistHelper Notes

Not currently used by MistHelper directly.
