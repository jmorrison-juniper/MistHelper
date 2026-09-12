# createSiteWirelessClientsBlocklist

> createSiteWirelessClientsBlocklist

## HTTP

`POST /api/v1/sites/{site_id}/setting/blacklist`

## Description

This endpoint is to provide list of client macs for annotation blacklist.

Retrieve the current clients list `blacklist_url` under Site:Setting

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "macs": {
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "examples": [
        [
          "683b679ac024"
        ]
      ]
    }
  },
  "required": [
    "macs"
  ],
  "description": "Request Body"
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "macs": {
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "examples": [
        [
          "683b679ac024"
        ]
      ]
    }
  },
  "required": [
    "macs"
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

`mistapi.api.v1.sites.setting.createSiteWirelessClientsBlocklist()`

## Usage Context

Adds client MAC addresses to the site blacklist. Blacklisted clients are denied wireless access.

## Gotchas

- MAC addresses must be in colon-separated format. Changes take effect on next client association attempt.

## Related Endpoints

- [POST_sites_site_id_setting_whitelist.md](POST_sites_site_id_setting_whitelist.md) — Whitelist clients
- [GET_sites_site_id_setting.md](GET_sites_site_id_setting.md) — Site settings

## MistHelper Notes

Used by MistHelper via `updateSiteSetting` in Menu 118-120 (site security settings).
