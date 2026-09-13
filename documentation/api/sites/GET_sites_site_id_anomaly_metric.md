# listSiteAnomalyEvents

> listSiteAnomalyEvents

## HTTP

`GET /api/v1/sites/{site_id}/anomaly/{metric}`

## Description

List Site Anomaly Events

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| metric | string | Yes | See [List Insight Metrics]($e/Constants%20Definitions/listInsightMetrics) for available metrics |

## Request Body

None.

## Response

### 200

OK

```json
{
  "title": "response_anomaly_search",
  "required": [
    "end",
    "limit",
    "page",
    "results",
    "start"
  ],
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
    "page": {
      "type": "integer",
      "contentEncoding": "int32",
      "examples": [
        1
      ]
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "anomaly",
        "required": [
          "events",
          "sle_baseline",
          "sle_deviation",
          "timestamp"
        ],
        "type": "object",
        "properties": {
          "events": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "readOnly": true
          },
          "since": {
            "type": "number",
            "readOnly": true
          },
          "sle_baseline": {
            "type": "number",
            "readOnly": true
          },
          "sle_deviation": {
            "type": "number",
            "readOnly": true
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          }
        },
        "description": "Anomaly"
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

`mistapi.api.v1.sites.anomaly.listSiteAnomalyEvents()`

## Usage Context

Retrieves metric-level anomalies at a site (e.g., unusual latency spikes, throughput deviation from baseline).

## Gotchas

- Metric anomalies depend on baseline data. New sites may not have enough history for meaningful detection.

## Related Endpoints

- [GET_sites_site_id_anomaly_client.md](GET_sites_site_id_anomaly_client_client_mac_metric.md) — Client anomalies
- [GET_sites_site_id_anomaly_device.md](GET_sites_site_id_anomaly_device_device_mac_metric.md) — Device anomalies

## MistHelper Notes

Used by Menus **84**, **85**, **86** for anomaly data export.
