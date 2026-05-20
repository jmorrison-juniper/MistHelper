# getSiteInsightMetricsForAP

> **SOURCE: mistapi SDK only** -- This endpoint is not described in the current OpenAPI specification. Documentation generated from the installed `mistapi` Python library.

> API Reference: https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/insights/get-site-insight-metrics-for-a-p

## Module

`mistapi.api.v1.sites.insights`

## Signature

```python
getSiteInsightMetricsForAP(mist_session: mistapi.__api_session.APISession, site_id: str, device_id: str, metrics: str, start: str | None = None, end: str | None = None, duration: str | None = None, interval: str | None = None, limit: int | None = None, page: int | None = None) -> mistapi.__api_response.APIResponse
```

## Description

No description available.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| site_id | path | str | Yes |  |
| device_id | path | str | Yes |  |
| metrics | query | str | No |  |
| start | query | str | No |  |
| end | query | str | No |  |
| duration | query | str | No |  |
| interval | query | str | No |  |
| limit | query | int | No |  |
| page | query | int | No |  |

## Request Body

See mistapi SDK documentation.

## Response

See mistapi SDK documentation.

## Errors

None documented.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.insights.getSiteInsightMetricsForAP()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
