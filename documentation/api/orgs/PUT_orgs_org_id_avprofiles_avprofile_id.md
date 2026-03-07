# updateOrgAntivirusProfile

> updateOrgAntivirusProfile

## HTTP

`PUT /api/v1/orgs/{org_id}/avprofiles/{avprofile_id}`

## Description

Update Org Antivirus Profile

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| avprofile_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "fallback_action": {
      "type": "string",
      "description": "enum: `block`, `log-and-permit`, `permit`"
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
    "max_filesize": {
      "maximum": 40000.0,
      "minimum": 20.0,
      "type": "integer",
      "description": "In KB",
      "contentEncoding": "int32",
      "default": 10000
    },
    "mime_whitelist": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "protocols": {
      "minItems": 1,
      "type": "array",
      "items": {
        "title": "avprofile_protocol",
        "enum": [
          "ftp",
          "http",
          "imap",
          "pop3",
          "smtp"
        ],
        "type": "string"
      },
      "description": "List of protocols to monitor. enum: `ftp`, `http`, `imap`, `pop3`, `smtp`"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "url_whitelist": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    }
  },
  "required": [
    "name"
  ]
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "fallback_action": {
      "type": "string",
      "description": "enum: `block`, `log-and-permit`, `permit`"
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
    "max_filesize": {
      "maximum": 40000.0,
      "minimum": 20.0,
      "type": "integer",
      "description": "In KB",
      "contentEncoding": "int32",
      "default": 10000
    },
    "mime_whitelist": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "protocols": {
      "minItems": 1,
      "type": "array",
      "items": {
        "title": "avprofile_protocol",
        "enum": [
          "ftp",
          "http",
          "imap",
          "pop3",
          "smtp"
        ],
        "type": "string"
      },
      "description": "List of protocols to monitor. enum: `ftp`, `http`, `imap`, `pop3`, `smtp`"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "url_whitelist": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    }
  },
  "required": [
    "name"
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

`mistapi.api.v1.orgs.antivirus_profiles.updateOrgAntivirusProfile()`

## Usage Context

Updates an existing Antivirus profile.

## Gotchas

- Changes apply to SRX gateways using this profile.

## Related Endpoints

- [GET_orgs_org_id_avprofiles_id.md](GET_orgs_org_id_avprofiles_id.md) — Get profile
- [POST_orgs_org_id_avprofiles.md](POST_orgs_org_id_avprofiles.md) — Create profile

## MistHelper Notes

Not currently used by MistHelper directly.
