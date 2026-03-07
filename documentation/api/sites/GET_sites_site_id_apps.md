# listSiteApps

> listSiteApps

## HTTP

`GET /api/v1/sites/{site_id}/apps`

## Description

Get List of Site Applications

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
  "uniqueItems": true,
  "type": "array",
  "items": {
    "title": "site_app",
    "required": [
      "group",
      "key",
      "name"
    ],
    "type": "object",
    "properties": {
      "group": {
        "minLength": 1,
        "type": "string"
      },
      "key": {
        "minLength": 1,
        "type": "string"
      },
      "name": {
        "minLength": 1,
        "type": "string"
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "group": "string",
        "key": "string",
        "name": "string"
      }
    ]
  ]
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

`mistapi.api.v1.sites.applications.listSiteApps()`

## Usage Context

Retrieves the list of discovered applications at a site, including traffic classification data for SD-WAN visibility.

## Gotchas

- Application detection requires gateway or switch traffic inspection to be enabled.

## Related Endpoints

- [GET_sites_site_id_stats_apps.md](GET_sites_site_id_stats_apps.md) — App traffic stats
- [GET_sites_site_id_services_derived.md](GET_sites_site_id_services_derived.md) — Service definitions

## MistHelper Notes

Not currently used by MistHelper directly.
