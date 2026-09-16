# getSiteInsightMetricsForGateway

> getSiteInsightMetricsForGateway

## HTTP

`GET /api/v1/sites/{site_id}/insights/gateway/{device_id}/stats`

## Description

Get Gateway Insight Metrics

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| metrics | string | Yes |  |  | Comma separated Metric names, e.g. `tx_bps,rx_bps`. See possible values at [List Insight Metrics](/#operations/listInsightMetrics) |
| port_id | string | No |  |  | Port ID of the gateway device, e.g. `ge-0/0/1` |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
|  | string | No |  |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Time-series insight metric response for a device",
  "properties": {
    "end": {
      "description": "Epoch timestamp for the end of the metric query window",
      "type": "integer"
    },
    "interval": {
      "description": "Aggregation interval in seconds for each metric sample",
      "type": "integer"
    },
    "limit": {
      "description": "Maximum number of metric samples returned in this page",
      "type": "integer"
    },
    "page": {
      "description": "Returned page number for paginated metric samples",
      "type": "integer"
    },
    "results": {
      "description": "Device metric result values aligned with the response timestamps",
      "items": {
        "description": "Device metric result value, returned as a string or integer",
        "oneOf": [
          {
            "type": "string"
          },
          {
            "type": "integer"
          }
        ]
      },
      "type": "array"
    },
    "rt": {
      "description": "Unique string values returned or accepted by this schema",
      "items": {
        "type": "string"
      },
      "type": "array",
      "uniqueItems": true
    },
    "start": {
      "description": "Epoch timestamp for the start of the metric query window",
      "type": "integer"
    }
  },
  "required": [
    "end",
    "interval",
    "results",
    "start"
  ],
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.insights.getSiteInsightMetricsForGateway()`

## Usage Context

Retrieves gateway-specific insight stats for a device (WAN link utilization, BGP peer status, VPN tunnel metrics, etc.).

## Gotchas

- Only applicable to SRX/SSR gateway devices. APs and switches have different insight endpoints.

## Related Endpoints

- [GET_sites_site_id_insights_device_device_mac_metric.md](GET_sites_site_id_insights_device_device_mac_metric.md) — General device insights
- [GET_sites_site_id_insights_switch_device_mac_metric.md](GET_sites_site_id_insights_switch_device_mac_metric.md) — Switch insights

## MistHelper Notes

Used by Menu **68** and **69** via `getSiteInsightMetrics`.
