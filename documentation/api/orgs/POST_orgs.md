# createOrg

> createOrg

## HTTP

`POST /api/v1/orgs`

## Description

Org admin can invite people to manage the org. Furthermore, he can dictate the level of security those accounts are. The check is enforced when the invited admin tries to "accept" the invitation and every time the admin tries to login

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "alarmtemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "contentEncoding": "uuid"
    },
    "allow_mist": {
      "type": "boolean",
      "default": true
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
    "msp_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "b9d42c2e-88ee-41f8-b798-f009ce7fe909"
      ]
    },
    "msp_logo_url": {
      "type": "string",
      "description": "logo uploaded by the MSP with advanced tier, only present if provided",
      "readOnly": true,
      "examples": [
        "https://example.com/logo/b9d42c2e-88ee-41f8-b798-f009ce7fe909.jpeg"
      ]
    },
    "msp_name": {
      "type": "string",
      "description": "Name of the msp the org belongs to",
      "readOnly": true,
      "examples": [
        "MSP"
      ]
    },
    "name": {
      "type": "string",
      "examples": [
        "Org"
      ]
    },
    "orggroup_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": ""
    },
    "session_expiry": {
      "maximum": 20160.0,
      "minimum": 10.0,
      "type": "integer",
      "contentEncoding": "int32",
      "default": 1440
    }
  },
  "required": [
    "name"
  ]
}
```

## Response

### 200

Org Infos

```json
{
  "type": "object",
  "properties": {
    "alarmtemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "contentEncoding": "uuid"
    },
    "allow_mist": {
      "type": "boolean",
      "default": true
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
    "msp_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "b9d42c2e-88ee-41f8-b798-f009ce7fe909"
      ]
    },
    "msp_logo_url": {
      "type": "string",
      "description": "logo uploaded by the MSP with advanced tier, only present if provided",
      "readOnly": true,
      "examples": [
        "https://example.com/logo/b9d42c2e-88ee-41f8-b798-f009ce7fe909.jpeg"
      ]
    },
    "msp_name": {
      "type": "string",
      "description": "Name of the msp the org belongs to",
      "readOnly": true,
      "examples": [
        "MSP"
      ]
    },
    "name": {
      "type": "string",
      "examples": [
        "Org"
      ]
    },
    "orggroup_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": ""
    },
    "session_expiry": {
      "maximum": 20160.0,
      "minimum": 10.0,
      "type": "integer",
      "contentEncoding": "int32",
      "default": 1440
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

`mistapi.api.v1.orgs.orgs.createOrg()`

## Usage Context

Creates a new organization in the Mist cloud.

## Gotchas

- Org creation requires appropriate account-level privileges.
- The org_id returned is used for all subsequent API calls.

## Related Endpoints

- [GET_orgs_org_id.md](GET_orgs_org_id.md) — Get org
- [PUT_orgs_org_id.md](PUT_orgs_org_id.md) — Update org

## MistHelper Notes

Not currently used by MistHelper directly. MistHelper operates within an existing org.
