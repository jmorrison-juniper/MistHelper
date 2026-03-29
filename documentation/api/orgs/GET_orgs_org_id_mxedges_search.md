# searchOrgMxEdges

> searchOrgMxEdges

## HTTP

`GET /api/v1/orgs/{org_id}/mxedges/search`

## Description

Search Org Mist Edges

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| mxedge_id | string | No |  |  | Mist edge id |
| site_id | string | No |  |  | Mist edge site id |
| mxcluster_id | string | No |  |  | Mist edge cluster id |
| model | string | No |  |  | Model name |
| distro | string | No |  |  | Debian code name (buster, bullseye) |
| tunterm_version | string | No |  |  | tunterm version |
| stats | boolean | No |  |  | Whether to return device stats, default is false |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1694708579
      ]
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        10
      ]
    },
    "next": {
      "type": "string"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "search_mxedge",
        "type": "object",
        "properties": {
          "distro": {
            "type": "string"
          },
          "last_seen": {
            "type": "number"
          },
          "model": {
            "type": "string",
            "examples": [
              "ME-VM"
            ]
          },
          "mxcluster_id": {
            "type": "string",
            "description": "Unique ID of the object instance in the Mist Organization",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "53f10664-3ce8-4c27-b382-0ef66432349f"
            ]
          },
          "mxedge_id": {
            "type": "string",
            "description": "Unique ID of the object instance in the Mist Organization",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "53f10664-3ce8-4c27-b382-0ef66432349f"
            ]
          },
          "name": {
            "type": "string",
            "description": "The name of the tunnel",
            "examples": [
              "me-vm-1"
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
          "tunterm_version": {
            "type": "string"
          },
          "uptime": {
            "type": "integer",
            "contentEncoding": "int32"
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1694622179
      ]
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        2
      ]
    }
  }
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.mxedges.searchOrgMxEdges()`

## Usage Context

Searches Mist Edge appliances across the organization.

## Gotchas

- No known gotchas.

## Related Endpoints

- [GET_orgs_org_id_mxedges_count.md](GET_orgs_org_id_mxedges_count.md) — Count edges
- [GET_orgs_org_id_mxedges.md](GET_orgs_org_id_mxedges.md) — List edges

## MistHelper Notes

Not currently used by MistHelper directly.
