# searchOrgMarvisClientEvents

> **SOURCE: mistapi SDK only** -- This endpoint is not described in the current OpenAPI specification. Documentation generated from the installed `mistapi` Python library.

> API Reference: https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/clients/marvis/search-org-marvis-client-events

## Module

`mistapi.api.v1.orgs.marvisclients`

## Signature

```python
searchOrgMarvisClientEvents(mist_session: mistapi.__api_session.APISession, org_id: str, type: str | None = None, device_id: str | None = None, wifi_mac: str | None = None, wifi_ip: str | None = None, hostname: str | None = None, ssid: str | None = None, bssid: str | None = None, channel: str | None = None, pre_bssid: str | None = None, pre_channel: str | None = None, limit: int | None = None, start: str | None = None, end: str | None = None, duration: str | None = None) -> mistapi.__api_response.APIResponse
```

## Description

No description available.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| org_id | path | str | Yes |  |
| type | query | str | No |  |
| device_id | query | str | No |  |
| wifi_mac | query | str | No |  |
| wifi_ip | query | str | No |  |
| hostname | query | str | No |  |
| ssid | query | str | No |  |
| bssid | query | str | No |  |
| channel | query | str | No |  |
| pre_bssid | query | str | No |  |
| pre_channel | query | str | No |  |
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

`mistapi.api.v1.orgs.marvisclients.searchOrgMarvisClientEvents()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
