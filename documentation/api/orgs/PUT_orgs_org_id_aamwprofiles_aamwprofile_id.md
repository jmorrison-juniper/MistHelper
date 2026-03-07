# updateOrgAAMWProfile

> updateOrgAAMWProfile

## HTTP

`PUT /api/v1/orgs/{org_id}/aamwprofiles/{aamwprofile_id}`

## Description

Update Advanced Anti Malware Profile (SkyAtp) Profile

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| aamwprofile_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "categories": {
      "type": "array",
      "items": {
        "title": "aamw_profile_category",
        "type": "object",
        "properties": {
          "category": {
            "type": "string",
            "description": "enum: `archive`, `document`, `pdf`, `executable`, `rich_application`, `library`, `os_package`, `mobile`, `java`, `configuration`, `script`"
          },
          "hash_lookup_only": {
            "type": "boolean",
            "default": false
          }
        }
      },
      "description": ""
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "fallback_action": {
      "type": "string",
      "description": "enum: `block`, `permit`"
    },
    "file_action": {
      "type": "string",
      "description": "enum: `block`, `permit`"
    },
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "examples": [
        "aamw-custom"
      ]
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "verdict_threshold": {
      "maximum": 10.0,
      "minimum": 1.0,
      "type": "integer",
      "contentEncoding": "int32",
      "default": 8
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
    "categories": {
      "type": "array",
      "items": {
        "title": "aamw_profile_category",
        "type": "object",
        "properties": {
          "category": {
            "type": "string",
            "description": "enum: `archive`, `document`, `pdf`, `executable`, `rich_application`, `library`, `os_package`, `mobile`, `java`, `configuration`, `script`"
          },
          "hash_lookup_only": {
            "type": "boolean",
            "default": false
          }
        }
      },
      "description": ""
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "fallback_action": {
      "type": "string",
      "description": "enum: `block`, `permit`"
    },
    "file_action": {
      "type": "string",
      "description": "enum: `block`, `permit`"
    },
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "examples": [
        "aamw-custom"
      ]
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "verdict_threshold": {
      "maximum": 10.0,
      "minimum": 1.0,
      "type": "integer",
      "contentEncoding": "int32",
      "default": 8
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

`mistapi.api.v1.orgs.advanced_anti_malware_profiles.updateOrgAAMWProfile()`

## Usage Context

Updates an existing Advanced Anti-Malware (AAMW) profile.

## Gotchas

- Changes take effect on devices using this profile after the next config push.

## Related Endpoints

- [GET_orgs_org_id_aamwprofiles_id.md](GET_orgs_org_id_aamwprofiles_id.md) — Get profile
- [POST_orgs_org_id_aamwprofiles.md](POST_orgs_org_id_aamwprofiles.md) — Create profile

## MistHelper Notes

Not currently used by MistHelper directly.
