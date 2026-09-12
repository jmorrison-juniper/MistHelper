# deleteOrgAAMWProfile

> deleteOrgAAMWProfile

## HTTP

`DELETE /api/v1/orgs/{org_id}/aamwprofiles/{aamwprofile_id}`

## Description

Delete Advanced Anti Malware Profile (SkyAtp) Profile

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| aamwprofile_id | string | Yes |  |

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

`mistapi.api.v1.orgs.advanced_anti_malware_profiles.deleteOrgAAMWProfile()`

## Usage Context

Deletes an Advanced Anti-Malware (Sky ATP) profile from an organization.

## Gotchas

- Ensure no sites reference this profile before deleting.

## Related Endpoints

- [GET_orgs_org_id_aamwprofiles.md](GET_orgs_org_id_aamwprofiles.md) — List profiles
- [POST_orgs_org_id_aamwprofiles.md](POST_orgs_org_id_aamwprofiles.md) — Create profile

## MistHelper Notes

Not currently used by MistHelper directly.
