# deleteSelf

> deleteSelf

## HTTP

`DELETE /api/v1/self`

## Description

To delete ones account and every associated with it. The effects:

the account would be deleted
any orphaned Org (that only has this account as admin) will be deleted
along with all data with Org (sites, wlans, devices) will be gone.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

OK

## Errors

| Status | Description |
|--------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.self.account.deleteSelf()`

## Usage Context

Use this endpoint to permanently delete the current admin account. Common use cases:

- Removing an admin account that is no longer needed
- Self-service account deletion for compliance or offboarding

## Gotchas

- This action is irreversible -- the account and all associated data will be permanently deleted
- If this admin is the sole owner of an organization, the organization may become inaccessible
- Ensure another admin has sufficient privileges before deleting your account

## Related Endpoints

- [GET_self.md](GET_self.md) -- Check current account details before deletion
- [../orgs/GET_orgs_org_id_admins.md](../orgs/GET_orgs_org_id_admins.md) -- Verify other admins exist before self-deletion

## MistHelper Notes

Not currently used by MistHelper.
