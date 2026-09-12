# getOrgSitesSle

> getOrgSitesSle

## HTTP

`GET /api/v1/orgs/{org_id}/insights/sites-sle`

## Description

Get Org Sites SLE

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
| sle | string | No |  |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| interval | string | No |  |  | Aggregation works by giving a time range plus interval (e.g. 1d, 1h, 10m) where aggregation function would be applied to. |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "object"
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

`mistapi.api.v1.orgs.sles.getOrgSitesSle()`

## Usage Context

Retrieves SLE (Service Level Expectation) scores across all sites in the organization.

## Gotchas

- Provides a high-level view of wireless quality per site.
- Results are aggregated over the specified time range.

## Related Endpoints

- [GET_orgs_org_id_insights_metric.md](GET_orgs_org_id_insights_metric.md) — Available metrics
- [GET_orgs_org_id_stats_sites.md](GET_orgs_org_id_stats_sites.md) — Site stats

## MistHelper Notes

Used by MistHelper via `getOrgSitesSle` in Menus 53, 66, 67.
