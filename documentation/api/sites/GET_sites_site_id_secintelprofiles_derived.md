# listSiteSecIntelProfilesDerived

> listSiteSecIntelProfilesDerived

## HTTP

`GET /api/v1/sites/{site_id}/secintelprofiles/derived`

## Description

Get the list of derived Sky-ATP secintel profiles a Site

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| resolve | boolean | No |  |  | Whether resolve the site variables |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "array",
  "items": {
    "title": "secintel_profile",
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "examples": [
          "secintel-custom"
        ]
      },
      "profiles": {
        "type": "array",
        "items": {
          "title": "secintel_profile_profile",
          "type": "object",
          "properties": {
            "action": {
              "type": "string",
              "description": "enum: `default`, `standard`, `strict`"
            },
            "category": {
              "type": "string",
              "description": "enum: `CC`, `IH` (Infected Host), `DNS`"
            }
          }
        },
        "description": ""
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "name": "secintel-custom",
        "profiles": [
          {
            "action": "default",
            "category": "CC"
          }
        ]
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

`mistapi.api.v1.sites.secintel_profiles.listSiteSecIntelProfilesDerived()`

## Usage Context

Retrieves the effective (derived/resolved) Security Intelligence profiles for a site.

## Gotchas

- SecIntel profiles provide threat feed integration. Only applicable to SRX gateways.

## Related Endpoints

- [../orgs/GET_orgs_org_id_secintelprofiles.md](../orgs/GET_orgs_org_id_secintelprofiles.md) — Org SecIntel profiles
- [GET_sites_site_id_setting.md](GET_sites_site_id_setting.md) — Site settings

## MistHelper Notes

Not currently used by MistHelper directly.
