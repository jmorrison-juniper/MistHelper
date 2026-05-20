# importOrgMapToSiteFile

> **SOURCE: mistapi SDK only** -- This endpoint is not described in the current OpenAPI specification. Documentation generated from the installed `mistapi` Python library.

> API Reference: https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/maps/import-org-map-to-site

## Module

`mistapi.api.v1.orgs.sites`

## Signature

```python
importOrgMapToSiteFile(mist_session: mistapi.__api_session.APISession, org_id: str, site_name: str, auto_deviceprofile_assignment: bool | None = None, csv: str | None = None, file: str | None = None, json: dict | None = None) -> mistapi.__api_response.APIResponse
```

## Description

No description available.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| org_id | path | str | Yes |  |
| site_name | path | str | Yes |  |
| auto_deviceprofile_assignment | body | bool | No |  |
| csv | body | str | No |  |
| file | body | str | No |  |
| json | body | dict | No |  |

## Request Body

See mistapi SDK documentation.

## Response

See mistapi SDK documentation.

## Errors

None documented.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.sites.importOrgMapToSiteFile()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
