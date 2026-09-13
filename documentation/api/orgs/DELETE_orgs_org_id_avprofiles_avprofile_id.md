# deleteOrgAntivirusProfile

> deleteOrgAntivirusProfile

## HTTP

`DELETE /api/v1/orgs/{org_id}/avprofiles/{avprofile_id}`

## Description

DeleteOrgAntivirusProfile

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| avprofile_id | string | Yes |  |

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

`mistapi.api.v1.orgs.antivirus_profiles.deleteOrgAntivirusProfile()`

## Usage Context

Deletes an antivirus profile from the organization.

## Gotchas

- Ensure no security policies reference this profile before deleting.

## Related Endpoints

- [GET_orgs_org_id_avprofiles.md](GET_orgs_org_id_avprofiles.md) — List profiles
- [POST_orgs_org_id_avprofiles.md](POST_orgs_org_id_avprofiles.md) — Create profile

## MistHelper Notes

Not currently used by MistHelper directly.
