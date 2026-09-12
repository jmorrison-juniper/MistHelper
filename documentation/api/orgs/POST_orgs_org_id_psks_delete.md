# deleteOrgPskList

> deleteOrgPskList

## HTTP

`POST /api/v1/orgs/{org_id}/psks/delete`

## Description

Delete Org PSK List

Delete list of psks on the org. This API accepts single string or list of strings

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
  "title": "psk_id_list",
  "type": "object",
  "properties": {
    "psk_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "",
      "examples": [
        [
          "0039c16c-ca87-4d3f-bb94-b97c58199f18",
          "6562cc8e-5893-418a-acaa-4d7c1af8084f"
        ]
      ]
    }
  }
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

`mistapi.api.v1.orgs.psks.deleteOrgPskList()`

## Usage Context

Bulk-deletes multiple PSKs from the organization.

## Gotchas

- Accepts a list of PSK IDs. Deleted PSKs are permanently removed.

## Related Endpoints

- [GET_orgs_org_id_psks.md](GET_orgs_org_id_psks.md) — List PSKs
- [POST_orgs_org_id_psks_import.md](POST_orgs_org_id_psks_import.md) — Import PSKs

## MistHelper Notes

Not currently used by MistHelper directly. PSK listing uses Menu 46 (`listOrgPsks`).
