# searchOrgClientFingerprints

> searchOrgClientFingerprints

## HTTP

`GET /api/v1/sites/{site_id}/insights/fingerprints/search`

## Description

Search Client Fingerprints

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| family | string | No |  |  | Device Category  of the client device |
| client_type | string | No |  |  | Whether client is wired or wireless |
| model | string | No |  |  | Model name of the client device |
| mfg | string | No |  |  | Manufacturer name of the client device |
| os | string | No |  |  | Operating System name and version of the client device |
| os_type | string | No |  |  | Operating system name of the client device |
| mac | string | No |  |  | MAC address of the client device |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| interval | string | No |  |  | Aggregation works by giving a time range plus interval (e.g. 1d, 1h, 10m) where aggregation function would be applied to. |
| sort | string | No | wxid |  | On which field the list should be sorted, -prefix represents DESC order. |
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
      "contentEncoding": "int32",
      "examples": [
        1711035686
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
        "title": "fingerprint",
        "type": "object",
        "properties": {
          "family": {
            "type": "string",
            "readOnly": true
          },
          "mac": {
            "type": "string",
            "readOnly": true
          },
          "mfg": {
            "type": "string",
            "readOnly": true
          },
          "model": {
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
          "os": {
            "type": "string",
            "readOnly": true
          },
          "os_type": {
            "type": "string",
            "readOnly": true
          },
          "random_mac": {
            "type": "boolean",
            "readOnly": true
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
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1710949286
      ]
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        232
      ]
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

`mistapi.api.v1.orgs.nac_fingerprints.searchOrgClientFingerprints()`

## Usage Context

Searches for client fingerprints at a specific site.

## Gotchas

- This is a site-level endpoint but documented under orgs.
- Can filter by family (e.g., Windows, macOS, iOS).

## Related Endpoints

- [GET_sites_site_id_insights_fingerprints_count.md](GET_sites_site_id_insights_fingerprints_count.md) — Count fingerprints
- [GET_orgs_org_id_clients_search.md](GET_orgs_org_id_clients_search.md) — Search clients

## MistHelper Notes

Not currently used by MistHelper directly.
