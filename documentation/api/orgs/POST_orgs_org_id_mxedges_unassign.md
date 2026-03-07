# unassignOrgMxEdgeFromSite

> unassignOrgMxEdgeFromSite

## HTTP

`POST /api/v1/orgs/{org_id}/mxedges/unassign`

## Description

Unassign Org MxEdge from Site

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
    "mxedge_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": ""
    }
  },
  "required": [
    "mxedge_ids"
  ],
  "description": "Request Body"
}
```

## Response

### 200

OK - list only devices that has deviceprofile_id changed

```json
{
  "type": "object",
  "properties": {
    "success": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    }
  },
  "required": [
    "success"
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

`mistapi.api.v1.orgs.mxedges.unassignOrgMxEdgeFromSite()`

## Usage Context

Unassigns Mist Edge appliances from their current site.

## Gotchas

- Unassigned Mist Edges remain in the org inventory.

## Related Endpoints

- [POST_orgs_org_id_mxedges_assign.md](POST_orgs_org_id_mxedges_assign.md) — Assign
- [GET_orgs_org_id_mxedges.md](GET_orgs_org_id_mxedges.md) — List Mist Edges

## MistHelper Notes

Not currently used by MistHelper directly.
