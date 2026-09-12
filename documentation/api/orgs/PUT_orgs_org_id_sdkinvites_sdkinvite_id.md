# updateSdkInvite

> updateSdkInvite

## HTTP

`PUT /api/v1/orgs/{org_id}/sdkinvites/{sdkinvite_id}`

## Description

Update SDK Invite

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| sdkinvite_id | string | Yes |  |

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
    "enabled": {
      "type": "boolean",
      "default": true
    },
    "expire_time": {
      "type": "integer",
      "contentEncoding": "int32"
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
      "description": "Name, will show up in mobile"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "quota": {
      "type": "integer",
      "description": "Number of time this invite can be used",
      "contentEncoding": "int32"
    },
    "quota_limited": {
      "type": "boolean",
      "description": "Whether quota limiting is enabled",
      "default": false
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    }
  },
  "required": [
    "name"
  ],
  "description": "Request Body"
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
    "enabled": {
      "type": "boolean",
      "default": true
    },
    "expire_time": {
      "type": "integer",
      "contentEncoding": "int32"
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
      "description": "Name, will show up in mobile"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "quota": {
      "type": "integer",
      "description": "Number of time this invite can be used",
      "contentEncoding": "int32"
    },
    "quota_limited": {
      "type": "boolean",
      "description": "Whether quota limiting is enabled",
      "default": false
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    }
  },
  "required": [
    "name"
  ],
  "description": "SDK invite"
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

`mistapi.api.v1.orgs.sdk_invites.updateSdkInvite()`

## Usage Context

Updates an existing SDK invitation.

## Gotchas

- SDK invites control access to Mist SDK features.

## Related Endpoints

- [GET_orgs_org_id_sdkinvites_sdkinvite_id.md](GET_orgs_org_id_sdkinvites_sdkinvite_id.md) — Get invite
- [POST_orgs_org_id_sdkinvites.md](POST_orgs_org_id_sdkinvites.md) — Create invite

## MistHelper Notes

Not currently used by MistHelper directly.
