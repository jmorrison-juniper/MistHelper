# deleteOrgDeviceProfile

> deleteOrgDeviceProfile

## HTTP

`DELETE /api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}`

## Description

Delete Org Device Profile

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| deviceprofile_id | string | Yes |  |

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

`mistapi.api.v1.orgs.device_profiles.deleteOrgDeviceProfile()`

## Usage Context

Deletes a device profile from the organization.

## Gotchas

- Devices assigned to this profile lose their profile-level configuration.

## Related Endpoints

- [GET_orgs_org_id_deviceprofiles.md](GET_orgs_org_id_deviceprofiles.md) — List profiles
- [POST_orgs_org_id_deviceprofiles.md](POST_orgs_org_id_deviceprofiles.md) — Create profile

## MistHelper Notes

Used by MistHelper via `listOrgDeviceProfiles` in Menus 35, 109, 110.
