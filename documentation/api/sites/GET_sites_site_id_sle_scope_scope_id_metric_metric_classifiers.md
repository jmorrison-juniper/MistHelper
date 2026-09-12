# listSiteSleMetricClassifiers

> listSiteSleMetricClassifiers

## HTTP

`GET /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/classifiers`

## Description

List classifiers for a specific metric

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| scope | string | Yes |  |
| scope_id | string | Yes | * site_id if `scope`==`site` * device_id if `scope`==`ap`, `scope`==`switch` or `scope`==`gateway` * mac if `scope`==`client` |
| metric | string | Yes | Values from `listSiteSlesMetrics` |

## Request Body

None.

## Response

### 200

OK

```json
{
  "uniqueItems": true,
  "type": "array",
  "items": {
    "type": "string"
  },
  "description": "",
  "examples": [
    [
      "asymmetry-uplink",
      "weak-signal",
      "asymmetry-downlink"
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.sles.listSiteSleMetricClassifiers()`

## Usage Context

Retrieves SLE classifiers for a specific metric. Classifiers break down SLE failures by root cause category (e.g., DHCP, DNS, auth failures).

## Gotchas

- Classifier names are metric-specific and not consistent across different SLE metrics.

## Related Endpoints

- [GET_sites_site_id_sle_scope_scope_id_metric_metric_classifier_classifier_summary.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_classifier_classifier_summary.md) — Classifier summary
- [GET_sites_site_id_sle_scope_scope_id_metric_metric_summary.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_summary.md) — Overall SLE summary

## MistHelper Notes

Used by Menu **53** via SLE analysis workflow.
