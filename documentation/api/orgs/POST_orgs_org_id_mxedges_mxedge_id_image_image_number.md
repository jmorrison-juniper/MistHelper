# addOrgMxEdgeImage

> addOrgMxEdgeImage

## HTTP

`POST /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/image/{image_number}`

## Description

Attach up to 3 images to a mxedge

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| mxedge_id | string | Yes |  |
| image_number | integer | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "required": [
    "file"
  ],
  "type": "object",
  "properties": {
    "file": {
      "type": "string",
      "description": "Binary file",
      "contentEncoding": "base64"
    },
    "json": {
      "type": "string"
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

`mistapi.api.v1.orgs.mxedges.addOrgMxEdgeImage()`

## Usage Context

Uploads a VM image to a specific Mist Edge appliance.

## Gotchas

- Image number identifies the image slot on the Mist Edge.

## Related Endpoints

- [GET_orgs_org_id_mxedges_mxedge_id.md](GET_orgs_org_id_mxedges_mxedge_id.md) — Get Mist Edge
- [GET_orgs_org_id_mxedges.md](GET_orgs_org_id_mxedges.md) — List Mist Edges

## MistHelper Notes

Not currently used by MistHelper directly.
