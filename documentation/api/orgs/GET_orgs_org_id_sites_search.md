# searchOrgSites

> searchOrgSites

## HTTP

`GET /api/v1/orgs/{org_id}/sites/search`

## Description

Search Sites

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
| analytic_enabled | boolean | No |  |  | If Advanced Analytic feature is enabled |
| app_waking | boolean | No |  |  | If App Waking feature is enabled |
| asset_enabled | boolean | No |  |  | If Asset Tracking is enabled |
| auto_upgrade_enabled | boolean | No |  |  | If Auto Upgrade feature is enabled |
| auto_upgrade_version | string | No |  |  | If Auto Upgrade feature is enabled |
| country_code | string | No |  |  | Site country code |
| honeypot_enabled | boolean | No |  |  | If Honeypot detection is enabled |
| id | string | No |  |  | Site id |
| locate_unconnected | boolean | No |  |  | If unconnected client are located |
| mesh_enabled | boolean | No |  |  | If Mesh feature is enabled |
| name | string | No |  |  | Site name. Case insensitive. Add a wildcard (`*`) at the end for partial search |
| rogue_enabled | boolean | No |  |  | If Rogue detection is enabled |
| remote_syslog_enabled | boolean | No |  |  | If Remote Syslog is enabled |
| rtsa_enabled | boolean | No |  |  | If managed mobility feature is enabled |
| vna_enabled | boolean | No |  |  | If Virtual Network Assistant is enabled |
| wifi_enabled | boolean | No |  |  | If Wi-Fi feature is enabled |
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

OK

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "next": {
      "type": "string"
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "response_site_search_item",
        "required": [
          "auto_upgrade_enabled",
          "auto_upgrade_version",
          "honeypot_enabled",
          "id",
          "name",
          "org_id",
          "site_id",
          "timestamp",
          "timezone",
          "vna_enabled",
          "wifi_enabled"
        ],
        "type": "object",
        "properties": {
          "auto_upgrade_enabled": {
            "type": "boolean"
          },
          "auto_upgrade_version": {
            "type": "string",
            "readOnly": true
          },
          "country_code": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "honeypot_enabled": {
            "type": "boolean"
          },
          "id": {
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
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "timezone": {
            "type": "string",
            "readOnly": true
          },
          "vna_enabled": {
            "type": "boolean"
          },
          "wifi_enabled": {
            "type": "boolean"
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
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

`mistapi.api.v1.orgs.sites.searchOrgSites()`

## Usage Context

Searches for sites within the organization using various filters.

## Gotchas

- Returns paginated results; use `limit` and `page` parameters.
- Supports filters: `name`, `country_code`, `timezone`, `analytic_enabled`, etc.

## Related Endpoints

- [GET_orgs_org_id_sites.md](GET_orgs_org_id_sites.md) — List all sites
- [GET_orgs_org_id_sites_count.md](GET_orgs_org_id_sites_count.md) — Count sites

## MistHelper Notes

Used by MistHelper via `searchOrgSites` in Menu 56.
