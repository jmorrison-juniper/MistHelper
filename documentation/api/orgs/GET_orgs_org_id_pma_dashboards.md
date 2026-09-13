# listOrgPmaDashboards

> listOrgPmaDashboards

## HTTP

`GET /api/v1/orgs/{org_id}/pma/dashboards`

## Description

Get List of premium analytics dashboards for this Org

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
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "array",
  "items": {
    "title": "pma_dashboard",
    "type": "object",
    "properties": {
      "description": {
        "type": "string",
        "description": "Description of the dashboard",
        "examples": [
          "Dashboard 1 description"
        ]
      },
      "label": {
        "type": "string",
        "description": "group label name",
        "examples": [
          "Wireless"
        ]
      },
      "name": {
        "type": "string",
        "description": "Name of the dashboard",
        "examples": [
          "dashboard_1"
        ]
      },
      "url": {
        "type": "string",
        "description": "url to access dashboard. Url will redirect the user to the dashboard",
        "examples": [
          "https://api.mist.com/api/v1/forward/looker?jwt=..."
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "name": "dashboard_1",
        "url": "https://mist.looker.com/login/embed/%2Fembed%2Fdashboards%2F1?group_ids=%5B3%5D&last_name=%22%22&models=%5B%22generic%22%5D&....."
      }
    ]
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

`mistapi.api.v1.orgs.premium_analytics.listOrgPmaDashboards()`

## Usage Context

Retrieves PMA (Premium Analytics) dashboard configurations.

## Gotchas

- Requires Premium Analytics license.

## Related Endpoints

- [GET_orgs_org_id_stats.md](GET_orgs_org_id_stats.md) — Org stats
- [GET_orgs_org_id_insights_sites-sle.md](GET_orgs_org_id_insights_sites-sle.md) — SLE insights

## MistHelper Notes

Not currently used by MistHelper directly.
