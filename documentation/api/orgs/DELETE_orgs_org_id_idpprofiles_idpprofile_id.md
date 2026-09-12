# deleteOrgIdpProfile

> deleteOrgIdpProfile

## HTTP

`DELETE /api/v1/orgs/{org_id}/idpprofiles/{idpprofile_id}`

## Description

Delete Org IDP Profile

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| idpprofile_id | string | Yes |  |

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

`mistapi.api.v1.orgs.idp_profiles.deleteOrgIdpProfile()`

## Usage Context

Deletes an Intrusion Detection and Prevention (IDP) profile from the organization.

## Gotchas

- Ensure no security policies reference this profile.

## Related Endpoints

- [GET_orgs_org_id_idpprofiles.md](GET_orgs_org_id_idpprofiles.md) — List profiles
- [POST_orgs_org_id_idpprofiles.md](POST_orgs_org_id_idpprofiles.md) — Create profile

## MistHelper Notes

Not currently used by MistHelper directly.
