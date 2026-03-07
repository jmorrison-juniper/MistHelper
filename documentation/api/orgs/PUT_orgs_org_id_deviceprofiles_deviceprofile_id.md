# updateOrgDeviceProfile

> updateOrgDeviceProfile

## HTTP

`PUT /api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}`

## Description

Update Org Device Profile

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| deviceprofile_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "description": "Request Body"
}
```

## Response

### 200

OK

```json
{
  "type": "object"
}
```

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

`mistapi.api.v1.orgs.device_profiles.updateOrgDeviceProfile()`

## Usage Context

Updates an existing device profile.

## Gotchas

- Changes propagate to all devices assigned to this profile.

## Related Endpoints

- [GET_orgs_org_id_deviceprofiles_id.md](GET_orgs_org_id_deviceprofiles_id.md) — Get profile
- [POST_orgs_org_id_deviceprofiles.md](POST_orgs_org_id_deviceprofiles.md) — Create profile

## MistHelper Notes

Device profile listing uses Menu 33 (`listOrgDeviceProfiles`). Update is not used directly.
