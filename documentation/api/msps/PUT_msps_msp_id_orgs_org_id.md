# updateMspOrg

> updateMspOrg

## HTTP

`PUT /api/v1/msps/{msp_id}/orgs/{org_id}`

## Description

Update MSP Org

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |
| org_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "title": "org",
  "required": [
    "name"
  ],
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
  }
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

`mistapi.api.v1.msps.orgs.updateMspOrg()`

## Usage Context

Updates an organization's settings within an MSP, such as name, subscription tier, or management preferences. Use this for org-level configuration changes managed centrally through the MSP.

## Gotchas

- Changes are applied immediately to the target org.
- Some settings may require the org's own admin consent if it was an adopted (not MSP-created) org.

## Related Endpoints

- [GET_msps_msp_id_orgs_org_id.md](GET_msps_msp_id_orgs_org_id.md) — Get current org details before updating
- [PUT_msps_msp_id_orgs.md](PUT_msps_msp_id_orgs.md) — Bulk manage multiple orgs
- [DELETE_msps_msp_id_orgs_org_id.md](DELETE_msps_msp_id_orgs_org_id.md) — Remove the org

## MistHelper Notes

Not currently used by MistHelper directly.
