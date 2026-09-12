# updateSiteSleThreshold

> updateSiteSleThreshold

## HTTP

`PUT /api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/threshold`

## Description

Update the SLE threshold

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

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "default": {
      "type": "number",
      "readOnly": true
    },
    "direction": {
      "minLength": 1,
      "type": "string",
      "readOnly": true
    },
    "maximum": {
      "type": "number"
    },
    "metric": {
      "minLength": 1,
      "type": "string",
      "readOnly": true
    },
    "minimum": {
      "type": "number"
    },
    "threshold": {
      "minLength": 1,
      "type": "string",
      "readOnly": true
    },
    "units": {
      "minLength": 1,
      "type": "string",
      "readOnly": true
    }
  }
}
```

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "default": {
      "type": "number",
      "readOnly": true
    },
    "direction": {
      "minLength": 1,
      "type": "string",
      "readOnly": true
    },
    "maximum": {
      "type": "number"
    },
    "metric": {
      "minLength": 1,
      "type": "string",
      "readOnly": true
    },
    "minimum": {
      "type": "number"
    },
    "threshold": {
      "minLength": 1,
      "type": "string",
      "readOnly": true
    },
    "units": {
      "minLength": 1,
      "type": "string",
      "readOnly": true
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.sles.updateSiteSleThreshold()`

## Usage Context

Updates custom SLE threshold values for a specific scope and metric.

## Gotchas

- Threshold values must be within valid ranges for the metric type.

## Related Endpoints

- [GET_sites_site_id_sle_scope_scope_id_metric_metric_threshold.md](GET_sites_site_id_sle_scope_scope_id_metric_metric_threshold.md) — Get thresholds
- [POST_sites_site_id_sle_scope_scope_id_metric_metric_threshold.md](POST_sites_site_id_sle_scope_scope_id_metric_metric_threshold.md) — Create thresholds

## MistHelper Notes

Not currently used by MistHelper directly.
