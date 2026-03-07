# uninviteOrgAdmin

> uninviteOrgAdmin

## HTTP

`DELETE /api/v1/orgs/{org_id}/invites/{invite_id}`

## Description

Delete Admin Invite

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| invite_id | string | Yes |  |

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

`mistapi.api.v1.orgs.admins.uninviteOrgAdmin()`

## Usage Context

Revokes a pending admin invitation for the organization.

## Gotchas

- Only pending (not yet accepted) invitations can be revoked.

## Related Endpoints

- [GET_orgs_org_id_invites.md](GET_orgs_org_id_invites.md) — List invitations
- [POST_orgs_org_id_invites.md](POST_orgs_org_id_invites.md) — Create invitation

## MistHelper Notes

Used by MistHelper via `listOrgInvites` in Menu 58.
