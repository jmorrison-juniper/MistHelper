# updateOrgSecurityZone

> updateOrgSecurityZone

## HTTP

`PUT /api/v1/orgs/{org_id}/securityzones/{securityzone_id}`

## Description

Update an organization security zone. Renaming a zone changes the security zone name used on the device for every Network referencing it.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "additionalProperties": false,
  "description": "Org-level security zone used by SRX gateways. The zone `name` is used as the security zone name on the device, and Networks reference a zone through their `zone_id`.",
  "properties": {
    "created_time": {
      "description": "When the object has been created, in epoch",
      "format": "double",
      "readOnly": true,
      "type": "number"
    },
    "id": {
      "description": "Unique ID of the object instance in the Mist Organization",
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ],
      "format": "uuid",
      "readOnly": true,
      "type": "string"
    },
    "modified_time": {
      "description": "When the object has been modified for the last time, in epoch",
      "format": "double",
      "readOnly": true,
      "type": "number"
    },
    "name": {
      "description": "Security zone name used on the device. Must start with a letter or a digit, followed by letters, digits, hyphens or underscores",
      "examples": [
        "corp-zone"
      ],
      "maxLength": 64,
      "minLength": 1,
      "pattern": "^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$",
      "type": "string"
    },
    "org_id": {
      "description": "Unique identifier of a Mist organization",
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ],
      "format": "uuid",
      "readOnly": true,
      "type": "string"
    }
  },
  "required": [
    "name"
  ],
  "type": "object"
}
```

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Org-level security zone used by SRX gateways. The zone `name` is used as the security zone name on the device, and Networks reference a zone through their `zone_id`.",
  "properties": {
    "created_time": {
      "description": "When the object has been created, in epoch",
      "format": "double",
      "readOnly": true,
      "type": "number"
    },
    "id": {
      "description": "Unique ID of the object instance in the Mist Organization",
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ],
      "format": "uuid",
      "readOnly": true,
      "type": "string"
    },
    "modified_time": {
      "description": "When the object has been modified for the last time, in epoch",
      "format": "double",
      "readOnly": true,
      "type": "number"
    },
    "name": {
      "description": "Security zone name used on the device. Must start with a letter or a digit, followed by letters, digits, hyphens or underscores",
      "examples": [
        "corp-zone"
      ],
      "maxLength": 64,
      "minLength": 1,
      "pattern": "^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$",
      "type": "string"
    },
    "org_id": {
      "description": "Unique identifier of a Mist organization",
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ],
      "format": "uuid",
      "readOnly": true,
      "type": "string"
    }
  },
  "required": [
    "name"
  ],
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

`mistapi.api.v1.orgs.security_zones.updateOrgSecurityZone()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
