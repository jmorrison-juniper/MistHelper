# getOrgMxEdgeVmParams

> getOrgMxEdgeVmParams

## HTTP

`GET /api/v1/orgs/{org_id}/mxedges/{mxedge_id}/vm_params`

## Description

Get Mist Edge VM parameters

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| mxedge_id | string | Yes |  |

## Request Body

None.

## Response

### 200

Mist Edge VM Parameters

```json
{
  "type": "object",
  "properties": {
    "model": {
      "type": "string",
      "description": "SKU",
      "examples": [
        "ME-VM"
      ]
    },
    "name": {
      "type": "string",
      "description": "User given name (optional)"
    },
    "user_data": {
      "type": "string",
      "description": "Base64 encoded user data"
    }
  },
  "description": "Mist Edge VM parameters"
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

`mistapi.api.v1.orgs.mxedges.getOrgMxEdgeVmParams()`

## Usage Context

Retrieves VM parameters for a specific Mist Edge appliance.

## Gotchas

- Used for virtualized Mist Edge deployments.

## Related Endpoints

- [GET_orgs_org_id_mxedges_mxedge_id.md](GET_orgs_org_id_mxedges_mxedge_id.md) — Get edge details
- [GET_orgs_org_id_mxedges.md](GET_orgs_org_id_mxedges.md) — List edges

## MistHelper Notes

Not currently used by MistHelper directly.
