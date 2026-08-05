# searchSiteMarvisConfigActions

> **SOURCE: mistapi SDK only** -- This endpoint is not described in the current OpenAPI specification. Documentation generated from the installed `mistapi` Python library.

> API Reference: https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/marvis-configs/search-site-marvis-config-actions

## Module

`mistapi.api.v1.sites.marvis_configs`

## Signature

```python
searchSiteMarvisConfigActions(mist_session: mistapi.__api_session.APISession, site_id: str, mac: str | None = None, type: str | None = None, src: str | None = None, admin_id: str | None = None, op: str | None = None, port_id: str | None = None, vlan_ids: int | None = None, reason: str | None = None, limit: int | None = None, start: str | None = None, end: str | None = None, duration: str | None = None) -> mistapi.__api_response.APIResponse
```

## Description

No description available.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| site_id | path | str | Yes |  |
| mac | query | str | No |  |
| type | query | str | No |  |
| src | query | str | No |  |
| admin_id | query | str | No |  |
| op | query | str | No |  |
| port_id | query | str | No |  |
| vlan_ids | query | int | No |  |
| reason | query | str | No |  |
| limit | query | int | No |  |
| start | query | str | No |  |
| end | query | str | No |  |
| duration | query | str | No |  |

## Request Body

See mistapi SDK documentation.

## Response

See mistapi SDK documentation.

## Errors

None documented.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.marvis_configs.searchSiteMarvisConfigActions()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
