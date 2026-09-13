# getSiteGatewayMetrics

> getSiteGatewayMetrics

## HTTP

`GET /api/v1/sites/{site_id}/stats/gateways/metrics`

## Description

Get Site Gateway Metrics

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "config_success": {
      "type": "number",
      "description": "Config success score",
      "examples": [
        99.9
      ]
    },
    "version_compliance": {
      "type": "object",
      "properties": {
        "major_version": {
          "type": "object",
          "additionalProperties": {
            "title": "gateway_compliance_major_version_properties",
            "type": "object",
            "properties": {
              "major_count": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "major_version": {
                "type": "string",
                "examples": [
                  "19.4R2-S1.2"
                ]
              }
            }
          }
        },
        "score": {
          "type": "number",
          "examples": [
            99.9
          ]
        },
        "type": {
          "type": "string",
          "examples": [
            "gateway"
          ]
        }
      },
      "description": "Version compliance score, major version for gateway, type"
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

`mistapi.api.v1.sites.stats_-_devices.getSiteGatewayMetrics()`

## Usage Context

Retrieves aggregated gateway metrics for a site, including WAN link health, throughput, and latency.

## Gotchas

- Metrics are aggregated across all gateways at the site.

## Related Endpoints

- [GET_sites_site_id_stats_devices.md](GET_sites_site_id_stats_devices.md) — All device stats
- [GET_sites_site_id_stats_bgp_peers_search.md](GET_sites_site_id_stats_bgp_peers_search.md) — BGP peers

## MistHelper Notes

Not currently used by MistHelper directly.
