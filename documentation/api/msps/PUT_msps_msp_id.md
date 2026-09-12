# updateMsp

> updateMsp

## HTTP

`PUT /api/v1/msps/{msp_id}`

## Description

Update MSP

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |

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

`mistapi.api.v1.msps.msps.updateMsp()`

## Usage Context

Updates MSP-level settings such as name and branding configuration. Use this to modify the MSP tenant properties after initial creation.

## Gotchas

- Only MSP super-admins can modify MSP-level settings.
- Changes to MSP name may affect branded portal URLs if white-labeling is enabled.

## Related Endpoints

- [GET_msps_msp_id.md](GET_msps_msp_id.md) — Get current MSP details before updating
- [POST_msps_msp_id_logo.md](POST_msps_msp_id_logo.md) — Upload MSP branding logo
- [DELETE_msps_msp_id_logo.md](DELETE_msps_msp_id_logo.md) — Remove MSP branding logo

## MistHelper Notes

Not currently used by MistHelper directly.
