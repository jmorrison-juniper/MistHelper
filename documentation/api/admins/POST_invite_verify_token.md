# verifyAdminInvite

> verifyAdminInvite

## HTTP

`POST /api/v1/invite/verify/{token}`

## Description

**Note**: another call to ```GET /api/v1/self``` is required to see the new set of privileges

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| token | string | Yes |  |

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
| 404 | Not Found |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.admins.admins.verifyAdminInvite()`

## Usage Context

Use this endpoint to verify an admin invitation token received via email. Common use cases:

- Accepting an invitation to join a Mist organization as an admin
- Completing the admin onboarding flow triggered by an org administrator

## Gotchas

- The `{token}` is single-use and time-limited -- it expires if not accepted promptly
- After successful verification, call `GET /api/v1/self` to see the new set of privileges granted by the invitation
- The invitation may grant different privilege levels (read-only, admin, super admin) depending on what was configured

## Related Endpoints

- [../orgs/POST_orgs_org_id_invites.md](../orgs/POST_orgs_org_id_invites.md) -- Create an admin invitation (org admin side)
- [../self/GET_self.md](../self/GET_self.md) -- View current privileges after accepting the invitation
- [POST_login.md](POST_login.md) -- Log in after invitation acceptance

## MistHelper Notes

Not currently used by MistHelper. MistHelper does not implement admin invitation workflows.
