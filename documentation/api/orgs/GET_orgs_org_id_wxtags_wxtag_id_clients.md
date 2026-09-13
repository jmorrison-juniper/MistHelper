# getOrgCurrentMatchingClientsOfAWxTag

> getOrgCurrentMatchingClientsOfAWxTag

## HTTP

`GET /api/v1/orgs/{org_id}/wxtags/{wxtag_id}/clients`

## Description

Get Current Matching Clients of a WXLAN Tag

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| wxtag_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "uniqueItems": true,
  "type": "array",
  "items": {
    "title": "wxtag_client",
    "required": [
      "mac",
      "since"
    ],
    "type": "object",
    "properties": {
      "mac": {
        "type": "string",
        "examples": [
          "5684dae9ac8b"
        ]
      },
      "since": {
        "type": "number",
        "examples": [
          1428939600
        ]
      }
    }
  },
  "description": ""
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

`mistapi.api.v1.orgs.wxtags.getOrgCurrentMatchingClientsOfAWxTag()`

## Usage Context

Retrieves clients associated with a specific WxTag.

## Gotchas

- Returns the list of client MACs currently matching the tag criteria.

## Related Endpoints

- [GET_orgs_org_id_wxtags_wxtag_id.md](GET_orgs_org_id_wxtags_wxtag_id.md) — Get WxTag
- [GET_orgs_org_id_wxtags.md](GET_orgs_org_id_wxtags.md) — List WxTags

## MistHelper Notes

Not currently used by MistHelper directly.
