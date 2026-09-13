# getOrgIdpProfile

> getOrgIdpProfile

## HTTP

`GET /api/v1/orgs/{org_id}/idpprofiles/{idpprofile_id}`

## Description

Get Org IDP Profile

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

Example response

```json
{
  "type": "object",
  "properties": {
    "base_profile": {
      "type": "string",
      "description": "enum: `critical`, `standard`, `strict`"
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
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
        "relaxed"
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
    "overwrites": {
      "type": "array",
      "items": {
        "title": "idp_profile_overwrite",
        "type": "object",
        "properties": {
          "action": {
            "type": "string",
            "description": "enum:\n  * alert (default)\n  * drop: silently dropping packets\n  * close: notify client/server to close connection"
          },
          "matching": {
            "title": "idp_profile_matching",
            "type": "object",
            "properties": {
              "attack_name": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "dst_subnet": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "severity": {
                "type": "array",
                "items": {
                  "title": "idp_profile_matching_severity_value",
                  "enum": [
                    "critical",
                    "info",
                    "major",
                    "minor"
                  ],
                  "type": "string",
                  "description": "enum: `critical`, `info`, `major`, `minor`",
                  "examples": [
                    "major"
                  ]
                },
                "description": ""
              }
            }
          },
          "name": {
            "type": "string"
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

`mistapi.api.v1.orgs.idp_profiles.getOrgIdpProfile()`

## Usage Context

Retrieves a specific IDP (Intrusion Detection and Prevention) profile by ID.

## Gotchas

- IDP profiles define security rules for SRX gateways.

## Related Endpoints

- [GET_orgs_org_id_idpprofiles.md](GET_orgs_org_id_idpprofiles.md) — List profiles
- [PUT_orgs_org_id_idpprofiles_idpprofile_id.md](PUT_orgs_org_id_idpprofiles_idpprofile_id.md) — Update profile

## MistHelper Notes

Not currently used by MistHelper directly.
