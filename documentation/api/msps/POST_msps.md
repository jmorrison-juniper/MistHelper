# createMsp

> createMsp

## HTTP

`POST /api/v1/msps`

## Description

Create MSP account

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
    "allow_mist": {
      "type": "boolean"
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
    "logo_url": {
      "type": "string",
      "description": "For advanced tier (uMSPs) only"
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string"
    },
    "tier": {
      "type": "string",
      "description": "enum: `advanced`, `base`"
    },
    "url": {
      "type": "string",
      "description": "For advanced tier (uMSPs) only"
    }
  },
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
    "allow_mist": {
      "type": "boolean"
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
    "logo_url": {
      "type": "string",
      "description": "For advanced tier (uMSPs) only"
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string"
    },
    "tier": {
      "type": "string",
      "description": "enum: `advanced`, `base`"
    },
    "url": {
      "type": "string",
      "description": "For advanced tier (uMSPs) only"
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

`mistapi.api.v1.msps.msps.createMsp()`

## Usage Context

Creates a new Managed Service Provider (MSP) tenant. MSPs are multi-tenant management entities that oversee multiple Mist organizations, providing centralized administration, license pooling, and cross-org visibility for service providers and large enterprises.

## Gotchas

- MSP creation requires appropriate account privileges — not all admin accounts can create MSPs.
- An MSP is a top-level container; organizations are then created or adopted under it.

## Related Endpoints

- [GET_msps_msp_id.md](GET_msps_msp_id.md) — Get MSP details after creation
- [PUT_msps_msp_id.md](PUT_msps_msp_id.md) — Update MSP settings
- [POST_msps_msp_id_orgs.md](POST_msps_msp_id_orgs.md) — Create organizations under the MSP

## MistHelper Notes

Not currently used by MistHelper directly.
