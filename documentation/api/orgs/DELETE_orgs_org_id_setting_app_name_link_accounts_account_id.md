# deleteOrgOauthAppAuthorization

> deleteOrgOauthAppAuthorization

## HTTP

`DELETE /api/v1/orgs/{org_id}/setting/{app_name}/link_accounts/{account_id}`

## Description

Delete Org Level OAuth Application Authorization With Mist Portal

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

None.

## Response

### 200

Successful

## Errors

| Status | Description |
|--------|-------------|
| 400 | Unsuccessful |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.linked_applications.deleteOrgOauthAppAuthorization()`

## Usage Context

Unlinks a third-party application account from the organization settings.

## Gotchas

- Unlinking may disable integrations that depend on the account.

## Related Endpoints

- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Org settings
- [PUT_orgs_org_id_setting.md](PUT_orgs_org_id_setting.md) — Update settings

## MistHelper Notes

Not currently used by MistHelper directly.
