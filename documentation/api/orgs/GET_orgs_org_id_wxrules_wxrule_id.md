# getOrgWxRule

> getOrgWxRule

## HTTP

`GET /api/v1/orgs/{org_id}/wxrules/{wxrule_id}`

## Description

Get Org WxRule Details

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| wxrule_id | string | Yes |  |

## Request Body

None.

## Response

### 200

Wrule

```json
{
  "type": "object",
  "properties": {
    "action": {
      "type": "string",
      "description": "type of action, allow / block. enum: `allow`, `block`"
    },
    "apply_tags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "blocked_apps": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Blocked apps (always blocking, ignoring action), the key of Get Application List",
      "examples": [
        [
          "mist",
          "all-videos"
        ]
      ]
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "dst_allow_wxtags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of WxTag UUID to indicate these tags are allowed access",
      "examples": [
        [
          "fff34466-eec0-3756-6765-381c728a6037",
          "eee2c7b0-d1d0-5a30-f349-e35fa43dc3b3"
        ]
      ]
    },
    "dst_deny_wxtags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of WxTag UUID to indicate these tags are blocked access",
      "examples": [
        [
          "aaa34466-eec0-3756-6765-381c728a6037",
          "bbb2c7b0-d1d0-5a30-f349-e35fa43dc3b3"
        ]
      ]
    },
    "dst_wxtags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of WxTag UUID",
      "examples": [
        [
          "aaa34466-eec0-3756-6765-381c728a6037",
          "bbb2c7b0-d1d0-5a30-f349-e35fa43dc3b3"
        ]
      ]
    },
    "enabled": {
      "type": "boolean",
      "default": true
    },
    "for_site": {
      "type": "boolean",
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
    "order": {
      "minimum": -1.0,
      "type": "integer",
      "description": "Order how rules would be looked up, > 0 and bigger order got matched first, -1 means LAST, uniqueness not checked",
      "contentEncoding": "int32",
      "examples": [
        1
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
    "src_wxtags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of WxTag UUID to determine if this rule would match",
      "examples": [
        [
          "8bfc2490-d726-3587-038d-cb2e71bd2330",
          "3aa8e73f-9f46-d827-8d6a-567bb7e67fc9"
        ]
      ]
    },
    "template_id": {
      "type": "string",
      "description": "Only for Org Level WxRule",
      "contentEncoding": "uuid",
      "examples": [
        "6aa54cbd-e039-4878-846a-04f270de8a5c"
      ]
    }
  },
  "required": [
    "order",
    "src_wxtags"
  ],
  "description": "WXlan"
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

`mistapi.api.v1.orgs.wxrules.getOrgWxRule()`

## Usage Context

Retrieves a specific WxLAN rule by ID.

## Gotchas

- WxLAN rules define network access restrictions within WLAN templates.

## Related Endpoints

- [GET_orgs_org_id_wxrules.md](GET_orgs_org_id_wxrules.md) — List WxRules
- [PUT_orgs_org_id_wxrules_wxrule_id.md](PUT_orgs_org_id_wxrules_wxrule_id.md) — Update WxRule

## MistHelper Notes

Not currently used by MistHelper directly.
