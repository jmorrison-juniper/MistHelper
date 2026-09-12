# searchOrgJsiPbn

> searchOrgJsiPbn

## HTTP

`GET /api/v1/orgs/{org_id}/jsi/pbn/search`

## Description

Text search for PBN (Problem Bug Notification) advisories. Search can be done on versions, models, customer_risk, id, and bug_type fields.

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
| versions | string | No |  |  | OS versions to search for |
| models | string | No |  |  | Device models to search for |
| customer_risk | string | No |  |  | Customer risk level to filter by |
| id | string | No |  |  | PBN ID to search for |
| bug_type | string | No |  |  | Bug type to filter by |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "description": "End timestamp",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "description": "Number of results to return",
      "contentEncoding": "int32"
    },
    "next": {
      "type": "string",
      "description": "Next page URL"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "jsi_pbn_item",
        "type": "object",
        "properties": {
          "bug_type": {
            "type": "string",
            "description": "Type of the bug (Day-1, Regression)"
          },
          "customer_risk": {
            "type": "string",
            "description": "Risk level"
          },
          "fixed_in": {
            "type": "string",
            "description": "Release in which the issue was fixed"
          },
          "id": {
            "type": "string",
            "description": "ID of the PBN",
            "examples": [
              "1403338"
            ]
          },
          "introduced_in": {
            "type": "string",
            "description": "Release introduced in"
          },
          "models": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "OS models affected"
          },
          "product_family": {
            "type": "string",
            "description": "Product family affected"
          },
          "release_notes": {
            "type": "string",
            "description": "Release notes for this PBN"
          },
          "restoration": {
            "type": "string",
            "description": "Restoration steps"
          },
          "title": {
            "type": "string",
            "description": "Title of the issue"
          },
          "updated_date": {
            "type": "integer",
            "description": "PBN updated timestamp",
            "contentEncoding": "int32"
          },
          "versions": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "OS versions affected"
          },
          "workaround": {
            "type": "string",
            "description": "Workaround for this issue"
          },
          "workaround_provided": {
            "type": "string",
            "description": "Any workaround available"
          }
        },
        "description": "PBN (Problem Bug Notification) advisory item"
      },
      "description": "List of PBN advisories"
    },
    "start": {
      "type": "integer",
      "description": "Start timestamp",
      "contentEncoding": "int32"
    },
    "total": {
      "type": "integer",
      "description": "Total number of results",
      "contentEncoding": "int32"
    }
  },
  "description": "PBN search response"
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

`mistapi.api.v1.orgs.jsi.searchOrgJsiPbn()`

## Usage Context

Searches JSI PBN (Policy-Based Networking) entries.

## Gotchas

- No known gotchas.

## Related Endpoints

- [GET_orgs_org_id_jsi_pbn_count.md](GET_orgs_org_id_jsi_pbn_count.md) — Count PBN
- [GET_orgs_org_id_jsi_inventory.md](GET_orgs_org_id_jsi_inventory.md) — JSI inventory

## MistHelper Notes

Not currently used by MistHelper directly.
