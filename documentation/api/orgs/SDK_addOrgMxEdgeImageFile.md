# addOrgMxEdgeImageFile

> **SOURCE: mistapi SDK only** -- This endpoint is not described in the current OpenAPI specification. Documentation generated from the installed `mistapi` Python library.

> API Reference: https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/mxedges/add-org-mx-edge-image

## Module

`mistapi.api.v1.orgs.mxedges`

## Signature

```python
addOrgMxEdgeImageFile(mist_session: mistapi.__api_session.APISession, org_id: str, mxedge_id: str, image_number: int, file: str | None = None, json: str | None = None) -> mistapi.__api_response.APIResponse
```

## Description

No description available.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| org_id | path | str | Yes |  |
| mxedge_id | path | str | Yes |  |
| image_number | path | int | Yes |  |
| file | body | str | No |  |
| json | body | str | No |  |

## Request Body

See mistapi SDK documentation.

## Response

See mistapi SDK documentation.

## Errors

None documented.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.mxedges.addOrgMxEdgeImageFile()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
