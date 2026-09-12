# updateOrgSecIntelProfile

> updateOrgSecIntelProfile

## HTTP

`PUT /api/v1/orgs/{org_id}/secintelprofiles/{secintelprofile_id}`

## Description

Update Sec Intel Profile

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| secintelprofile_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
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
  },
  "description": "Request Body"
}
```

## Response

### 200

Example response

```json
{
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

`mistapi.api.v1.orgs.secintel_profiles.updateOrgSecIntelProfile()`

## Usage Context

Updates an existing Security Intelligence profile.

## Gotchas

- Changes affect threat feed behavior on SRX gateways.

## Related Endpoints

- [GET_orgs_org_id_secintelprofiles_secintelprofile_id.md](GET_orgs_org_id_secintelprofiles_secintelprofile_id.md) — Get profile
- [POST_orgs_org_id_secintelprofiles.md](POST_orgs_org_id_secintelprofiles.md) — Create profile

## MistHelper Notes

Not currently used by MistHelper directly.
