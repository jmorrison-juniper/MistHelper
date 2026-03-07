# createSdkTemplate

> createSdkTemplate

## HTTP

`POST /api/v1/orgs/{org_id}/sdktemplates`

## Description

Create SDK Template

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "bg_image": {
      "type": "string"
    },
    "btn_flr_bgcolor": {
      "type": "string"
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "default": {
      "type": "boolean",
      "description": "Whether this is the default template when there are multiple templates"
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "header_txt": {
      "type": "string"
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
      "description": "Name for identification purpose"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "search_txtcolor": {
      "type": "string"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "welcome_msg": {
      "type": "string"
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
    "bg_image": {
      "type": "string"
    },
    "btn_flr_bgcolor": {
      "type": "string"
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "default": {
      "type": "boolean",
      "description": "Whether this is the default template when there are multiple templates"
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "header_txt": {
      "type": "string"
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
      "description": "Name for identification purpose"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "search_txtcolor": {
      "type": "string"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "welcome_msg": {
      "type": "string"
    }
  },
  "required": [
    "name"
  ],
  "description": "SDK Template"
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

`mistapi.api.v1.orgs.sdk_templates.createSdkTemplate()`

## Usage Context

Creates a new SDK template for mobile SDK configuration.

## Gotchas

- SDK templates define BLE and location behavior for mobile apps.

## Related Endpoints

- [GET_orgs_org_id_sdktemplates.md](GET_orgs_org_id_sdktemplates.md) — List SDK templates
- [PUT_orgs_org_id_sdktemplates_sdktemplate_id.md](PUT_orgs_org_id_sdktemplates_sdktemplate_id.md) — Update

## MistHelper Notes

Not currently used by MistHelper directly.
