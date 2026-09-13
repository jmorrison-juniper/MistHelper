# listSiteLanguages

> listSiteLanguages

## HTTP

`GET /api/v1/const/languages`

## Description

Get List of Languages

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of Languages

```json
{
  "type": "array",
  "items": {
    "title": "const_language",
    "required": [
      "display",
      "display_native",
      "key"
    ],
    "type": "object",
    "properties": {
      "display": {
        "type": "string",
        "examples": [
          "English (US)"
        ]
      },
      "display_native": {
        "type": "string",
        "examples": [
          "English (US)"
        ]
      },
      "key": {
        "type": "string",
        "examples": [
          "en-US"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "display": "English (US)",
        "display_native": "English (US)",
        "key": "en-US"
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

`mistapi.api.v1.constants.definitions.listSiteLanguages()`

## Usage Context

Returns the list of supported languages for captive portal and guest access pages. Use this when configuring multi-language guest WiFi portals or validating language settings in WLAN configurations.

## Gotchas

- Language codes follow standard locale formats (e.g., `en`, `fr`, `ja`). Ensure portal templates exist for any selected language.
- No known gotchas with the endpoint itself; the response is a small static reference list.

## Related Endpoints

- [GET_const_countries.md](GET_const_countries.md) — Country codes (often paired with language for localization)
- [../sites/GET_sites_site_id_wlans.md](../sites/GET_sites_site_id_wlans.md) — WLAN configs that may include portal language settings

## MistHelper Notes

Not currently used by MistHelper directly.
