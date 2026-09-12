# searchSiteClientFingerprints

> **SOURCE: mistapi SDK only** -- This endpoint is not described in the current OpenAPI specification. Documentation generated from the installed `mistapi` Python library.

> API Reference: https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/nac-fingerprints/search-site-client-fingerprints

## Module

`mistapi.api.v1.sites.insights`

## Signature

```python
searchSiteClientFingerprints(mist_session: mistapi.__api_session.APISession, site_id: str, family: str | None = None, client_type: str | None = None, model: str | None = None, mfg: str | None = None, os: str | None = None, os_type: str | None = None, mac: str | None = None, limit: int | None = None, start: str | None = None, end: str | None = None, duration: str | None = None, interval: str | None = None, sort: str | None = None, search_after: str | None = None) -> mistapi.__api_response.APIResponse
```

## Description

No description available.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| site_id | path | str | Yes |  |
| family | query | str | No |  |
| client_type | query | str{'wireless' | No |  |
| model | query | str | No |  |
| mfg | query | str | No |  |
| os | query | str | No |  |
| os_type | query | str | No |  |
| mac | query | str | No |  |
| limit | query | int | No |  |
| start | query | str | No |  |
| end | query | str | No |  |
| duration | query | str | No |  |
| interval | query | str | No |  |
| sort | query | str | No |  |
| search_after | query | str | No |  |

## Request Body

See mistapi SDK documentation.

## Response

See mistapi SDK documentation.

## Errors

None documented.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.insights.searchSiteClientFingerprints()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
