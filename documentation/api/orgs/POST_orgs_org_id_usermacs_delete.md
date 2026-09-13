# deleteOrgMultipleUserMacs

> deleteOrgMultipleUserMacs

## HTTP

`POST /api/v1/orgs/{org_id}/usermacs/delete`

## Description

Delete Multiple Org User MACs

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
    "usermac_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": ""
    }
  },
  "description": "Request Body"
}
```

## Response

### 200

OK

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

`mistapi.api.v1.orgs.user_macs.deleteOrgMultipleUserMacs()`

## Usage Context

Bulk-deletes user MAC entries from the organization.

## Gotchas

- Deleted MAC entries are permanently removed.

## Related Endpoints

- [GET_orgs_org_id_usermacs_search.md](GET_orgs_org_id_usermacs_search.md) — Search user MACs
- [POST_orgs_org_id_usermacs_import.md](POST_orgs_org_id_usermacs_import.md) — Import user MACs

## MistHelper Notes

Not currently used by MistHelper directly.
