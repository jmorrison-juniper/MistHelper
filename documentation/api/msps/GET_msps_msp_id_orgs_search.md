# searchMspOrgs

> searchMspOrgs

## HTTP

`GET /api/v1/msps/{msp_id}/orgs/search`

## Description

Search Org in MSP

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| name | string | No |  |  |  |
| org_id | string | No |  |  | Org id |
| sub_insufficient | boolean | No |  |  | If this org has sufficient subscription |
| trial_enabled | boolean | No |  |  | If this org is under trial period |
| usage_types | array | No |  |  | List of types that enabled by usage |
| limit | integer | No | 100 |  |  |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

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
      "type": "number",
      "readOnly": true
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32",
      "readOnly": true
    },
    "next": {
      "type": "string"
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "response_org_search_item",
        "type": "object",
        "properties": {
          "msp_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "b9d42c2e-88ee-41f8-b798-f009ce7fe909"
            ]
          },
          "name": {
            "type": "string",
            "description": "org name",
            "readOnly": true
          },
          "num_aps": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "num_gateways": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "num_sites": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "num_switches": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "num_unassigned_aps": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "org_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "sub_ana_entitled": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "sub_ana_required": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "sub_ast_entitled": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "sub_ast_required": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "sub_eng_entitled": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "sub_eng_required": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "sub_ex12_required": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "sub_insufficient": {
            "type": "boolean",
            "description": "If this org has sufficient subscription",
            "readOnly": true
          },
          "sub_man_entitled": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "sub_man_required": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "sub_me_entitled": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "sub_vna_entitled": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "sub_vna_required": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "trial_enabled": {
            "type": "boolean",
            "description": "If this org is under trial period",
            "readOnly": true
          },
          "usage_types": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "a list of types that enabled by usage",
            "readOnly": true
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "number",
      "readOnly": true
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32",
      "readOnly": true
    }
  },
  "required": [
    "end",
    "limit",
    "results",
    "start",
    "total"
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.msps.orgs.searchMspOrgs()`

## Usage Context

Searches organizations under an MSP with filtering capabilities such as name, status, or other attributes. More efficient than listing all orgs when you need to find specific organizations within a large MSP.

## Gotchas

- Search parameters are passed as query strings; check the API reference for available filter fields.
- Results are paginated — handle pagination for complete results.

## Related Endpoints

- [GET_msps_msp_id_orgs.md](GET_msps_msp_id_orgs.md) — List all orgs (no filtering)
- [GET_msps_msp_id_orgs_org_id.md](GET_msps_msp_id_orgs_org_id.md) — Get a specific org by ID

## MistHelper Notes

Not currently used by MistHelper directly.
