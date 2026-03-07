# listOrgSecIntelProfiles

> listOrgSecIntelProfiles

## HTTP

`GET /api/v1/orgs/{org_id}/secintelprofiles`

## Description

Get List of Sec Intel Profiles

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "array",
  "items": {
    "title": "secintel_profile",
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "examples": [
          "secintel-custom"
        ]
      },
      "profiles": {
        "type": "array",
        "items": {
          "title": "secintel_profile_profile",
          "type": "object",
          "properties": {
            "action": {
              "type": "string",
              "description": "enum: `default`, `standard`, `strict`"
            },
            "category": {
              "type": "string",
              "description": "enum: `CC`, `IH` (Infected Host), `DNS`"
            }
          }
        },
        "description": ""
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "name": "secintel-custom",
        "profiles": [
          {
            "action": "default",
            "category": "CC"
          }
        ]
      }
    ]
  ]
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

`mistapi.api.v1.orgs.secintel_profiles.listOrgSecIntelProfiles()`

## Usage Context

Lists all Security Intelligence profiles for the organization.

## Gotchas

- Requires SRX gateways to be effective.

## Related Endpoints

- [GET_orgs_org_id_secintelprofiles_secintelprofile_id.md](GET_orgs_org_id_secintelprofiles_secintelprofile_id.md) — Get specific profile
- [POST_orgs_org_id_secintelprofiles.md](POST_orgs_org_id_secintelprofiles.md) — Create profile

## MistHelper Notes

Not currently used by MistHelper directly.
