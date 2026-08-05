# getOrgMarvisClientInsights

> **SOURCE: mistapi SDK only** -- This endpoint is not described in the current OpenAPI specification. Documentation generated from the installed `mistapi` Python library.

> API Reference: https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/clients/marvis/get-org-marvis-client-insights

## Module

`mistapi.api.v1.orgs.insights`

## Signature

```python
getOrgMarvisClientInsights(mist_session: mistapi.__api_session.APISession, org_id: str, marvisclient_id: str, duration: str | None = None, interval: str | None = None, start: str | None = None, end: str | None = None, limit: int | None = None, page: int | None = None) -> mistapi.__api_response.APIResponse
```

## Description

No description available.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| org_id | path | str | Yes |  |
| marvisclient_id | path | str | Yes |  |
| duration | query | str | No |  |
| interval | query | str | No |  |
| start | query | str | No |  |
| end | query | str | No |  |
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

`mistapi.api.v1.orgs.insights.getOrgMarvisClientInsights()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
