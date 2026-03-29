# listCountryCodes

> listCountryCodes

## HTTP

`GET /api/v1/const/countries`

## Description

Get List of available Country Codes

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| extend | boolean | No | False |  | Will include more country codes if true |

## Request Body

None.

## Response

### 200

List of Countries

```json
{
  "type": "array",
  "items": {
    "title": "const_country",
    "required": [
      "alpha2",
      "certified",
      "name",
      "numeric"
    ],
    "type": "object",
    "properties": {
      "alpha2": {
        "type": "string",
        "description": "Country code, in two-character",
        "examples": [
          "FR"
        ]
      },
      "certified": {
        "type": "boolean",
        "examples": [
          true
        ]
      },
      "name": {
        "type": "string",
        "examples": [
          "France"
        ]
      },
      "numeric": {
        "type": "number",
        "description": "Country code, ISO 3166-1 numeric",
        "examples": [
          250
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "alpha2": "FR",
        "certified": true,
        "name": "France",
        "numeric": 250
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

`mistapi.api.v1.constants.definitions.listCountryCodes()`

## Usage Context

Returns the list of ISO country codes supported by the Mist platform. Country codes determine regulatory domains for RF channel selection, power limits, and DFS requirements. Use this when creating or updating site settings that require a country code.

## Gotchas

- Country codes must match exactly when used in site configuration — use the values returned here, not free-text.
- Some countries have sub-regions with different RF regulations; see the states endpoint for US states.

## Related Endpoints

- [GET_const_states.md](GET_const_states.md) — US state codes (sub-region of country)
- [GET_const_ap_channels.md](GET_const_ap_channels.md) — Available channels per country
- [GET_const_languages.md](GET_const_languages.md) — Supported languages for portals
- [../orgs/GET_orgs_org_id_sites.md](../orgs/GET_orgs_org_id_sites.md) — Sites use country_code for RF domain

## MistHelper Notes

Not currently used by MistHelper directly. Menu **11** (`OrgSiteExporter.sites`) exports site data that includes `country_code` values matching this endpoint.
