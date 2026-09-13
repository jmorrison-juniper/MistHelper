# getOrgApplicationList

> getOrgApplicationList

## HTTP

`GET /api/v1/orgs/{org_id}/wxtags/apps`

## Description

Get Application List

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

None.

## Response

### 200

List of Applications

```json
{
  "type": "array",
  "items": {
    "title": "search_wxtag_apps_item",
    "required": [
      "group",
      "key",
      "name"
    ],
    "type": "object",
    "properties": {
      "group": {
        "type": "string",
        "examples": [
          "Emails"
        ]
      },
      "key": {
        "type": "string",
        "examples": [
          "gmail"
        ]
      },
      "name": {
        "type": "string",
        "examples": [
          "Gmail - web/app"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "group": "Emails",
        "key": "gmail",
        "name": "Gmail - web/app"
      }
    ]
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

`mistapi.api.v1.orgs.wxtags.getOrgApplicationList()`

## Usage Context

Retrieves available application definitions for WxTags.

## Gotchas

- Apps are pre-defined application signatures for traffic classification.

## Related Endpoints

- [GET_orgs_org_id_wxtags.md](GET_orgs_org_id_wxtags.md) — List WxTags
- [GET_orgs_org_id_wxrules.md](GET_orgs_org_id_wxrules.md) — List WxRules

## MistHelper Notes

Not currently used by MistHelper directly.
