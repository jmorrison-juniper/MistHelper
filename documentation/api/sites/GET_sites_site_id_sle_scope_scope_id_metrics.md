# listSiteSlesMetrics

> listSiteSlesMetrics

## HTTP

`GET /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metrics`

## Description

List the metrics for the given scope

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| scope | string | Yes |  |
| scope_id | string | Yes | * site_id if `scope`==`site` * device_id if `scope`==`ap`, `scope`==`switch` or `scope`==`gateway` * mac if `scope`==`client` |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "enabled": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "supported": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    }
  },
  "required": [
    "enabled",
    "supported"
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.sles.listSiteSlesMetrics()`

## Usage Context

Lists all available SLE (Service Level Expectation) metrics for a given scope (site, device, client). This is the starting point for SLE analysis.

## Gotchas

- The `scope` parameter defines analysis level: `site`, `ap`, `switch`, `gateway`, `client`.
- Available metrics vary by scope.

## Related Endpoints

- [GET_sites_site_id_sle_scope_scope_id_metric_metric_summary.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_summary.md) — SLE summary
- [GET_sites_site_id_sle_scope_scope_id_metric_metric_classifiers.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_classifiers.md) — SLE classifiers

## MistHelper Notes

Used by Menu **53** via `listSiteSlesMetrics` to display available SLE metrics for a site.
