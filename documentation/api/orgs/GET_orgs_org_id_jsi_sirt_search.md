# searchOrgJsiSirt

> searchOrgJsiSirt

## HTTP

`GET /api/v1/orgs/{org_id}/jsi/sirt/search`

## Description

Text search for SIRT (Security Incident Response Team) advisories. Search can be done on versions, models, severity, and id fields.

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
| severity | string | No |  |  | Severity level to filter by |
| id | string | No |  |  | SIRT ID to search for |
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
        "title": "jsi_sirt_item",
        "type": "object",
        "properties": {
          "cvss_score": {
            "type": "number",
            "description": "CVSS score"
          },
          "id": {
            "type": "string",
            "description": "ID of the SIRT",
            "examples": [
              "JSA100053"
            ]
          },
          "models": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "OS models affected"
          },
          "problem": {
            "type": "string",
            "description": "Problem description"
          },
          "published_date": {
            "type": "integer",
            "description": "Release date of the SIRT issue",
            "contentEncoding": "int32"
          },
          "release_notes": {
            "type": "string",
            "description": "Release notes if any"
          },
          "severity": {
            "type": "string",
            "description": "Severity of the issue"
          },
          "solution": {
            "type": "string",
            "description": "Solution for the security issue"
          },
          "title": {
            "type": "string",
            "description": "Title of the SIRT"
          },
          "updated_date": {
            "type": "integer",
            "description": "JSA updated timestamp",
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
            "description": "Workaround provided"
          }
        },
        "description": "SIRT advisory item"
      },
      "description": "List of SIRT advisories"
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
  "description": "SIRT search response"
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

`mistapi.api.v1.orgs.jsi.searchOrgJsiSirt()`

## Usage Context

Searches JSI SIRT (Security Incident Response Team) entries.

## Gotchas

- No known gotchas.

## Related Endpoints

- [GET_orgs_org_id_jsi_sirt_count.md](GET_orgs_org_id_jsi_sirt_count.md) — Count SIRT
- [GET_orgs_org_id_jsi_inventory.md](GET_orgs_org_id_jsi_inventory.md) — JSI inventory

## MistHelper Notes

Not currently used by MistHelper directly.
