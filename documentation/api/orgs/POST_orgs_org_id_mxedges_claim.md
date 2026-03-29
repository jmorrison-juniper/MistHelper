# claimOrgMxEdge

> claimOrgMxEdge

## HTTP

`POST /api/v1/orgs/{org_id}/mxedges/claim`

## Description

For a Mist Edge in default state, it will show a random claim code like `135-546-673` which you can "claim" it into your Org

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
  "uniqueItems": true,
  "type": "array",
  "items": {
    "type": "string"
  },
  "description": "Request Body",
  "examples": [
    [
      "6JG8E-PTFV2-A9Z2N",
      "DVH4V-SNMSZ-PDXBR"
    ]
  ]
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    },
    "magic": {
      "type": "string"
    }
  },
  "required": [
    "id",
    "magic"
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

`mistapi.api.v1.orgs.mxedges.claimOrgMxEdge()`

## Usage Context

Claims Mist Edge appliances into the organization.

## Gotchas

- Requires a valid claim code from the Mist Edge device.

## Related Endpoints

- [POST_orgs_org_id_mxedges.md](POST_orgs_org_id_mxedges.md) — Create Mist Edge
- [GET_orgs_org_id_mxedges.md](GET_orgs_org_id_mxedges.md) — List Mist Edges

## MistHelper Notes

Not currently used by MistHelper directly.
