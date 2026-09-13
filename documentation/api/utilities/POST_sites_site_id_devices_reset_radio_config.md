# resetSiteAllApsToUseRrm

> resetSiteAllApsToUseRrm

## HTTP

`POST /api/v1/sites/{site_id}/devices/reset_radio_config`

## Description

Reset all APs in the Site to use RRM

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
    "bands": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of bands"
    },
    "force": {
      "type": "boolean",
      "description": "Whether to reset those with radio disabled. default is false (i.e. if user intentionally disables a radio, honor it)",
      "default": false
    }
  },
  "required": [
    "bands"
  ],
  "description": "Request Body"
}
```

## Response

### 200

OK

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

`mistapi.api.v1.utilities.wi-fi.resetSiteAllApsToUseRrm()`

## Usage Context

Resets all APs at a site to use RRM (Radio Resource Management) defaults. Clears any manual radio configuration overrides and returns to automatic channel/power management.

## Gotchas

- All manual radio channel/power overrides at the site are lost.
- APs may change channels after reset, briefly disconnecting clients.

## Related Endpoints

- [POST_sites_site_id_rrm_optimize.md](POST_sites_site_id_rrm_optimize.md) — Trigger RRM optimization

## MistHelper Notes

Not currently used by MistHelper via REST API.
