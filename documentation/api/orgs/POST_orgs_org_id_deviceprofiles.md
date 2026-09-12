# createOrgDeviceProfile

> createOrgDeviceProfile

## HTTP

`POST /api/v1/orgs/{org_id}/deviceprofiles`

## Description

Create Device Profile

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

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

`mistapi.api.v1.orgs.device_profiles.createOrgDeviceProfile()`

## Usage Context

Creates a new device profile for the organization.

## Gotchas

- Device profiles apply to APs, switches, or gateways depending on the `type` field.

## Related Endpoints

- [GET_orgs_org_id_deviceprofiles.md](GET_orgs_org_id_deviceprofiles.md) — List profiles
- [PUT_orgs_org_id_deviceprofiles_deviceprofile_id.md](PUT_orgs_org_id_deviceprofiles_deviceprofile_id.md) — Update profile

## MistHelper Notes

Not currently used by MistHelper directly.
