# deleteOrgSecIntelProfile

> deleteOrgSecIntelProfile

## HTTP

`DELETE /api/v1/orgs/{org_id}/secintelprofiles/{secintelprofile_id}`

## Description

Delete Sec Intel Profile

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| secintelprofile_id | string | Yes |  |

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

`mistapi.api.v1.orgs.secintel_profiles.deleteOrgSecIntelProfile()`

## Usage Context

Deletes a Security Intelligence profile from the organization.

## Gotchas

- Ensure no security policies reference this profile.

## Related Endpoints

- [GET_orgs_org_id_secintelprofiles.md](GET_orgs_org_id_secintelprofiles.md) — List profiles
- [POST_orgs_org_id_secintelprofiles.md](POST_orgs_org_id_secintelprofiles.md) — Create profile

## MistHelper Notes

Used by MistHelper via `listOrgSecIntelProfiles` in Menu 42.
