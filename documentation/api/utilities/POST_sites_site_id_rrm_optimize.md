# optimizeSiteRrm

> optimizeSiteRrm

## HTTP

`POST /api/v1/sites/{site_id}/rrm/optimize`

## Description

Optimize Site RRM

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
    "macs": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Targeting AP (neighbor APs may get changed, too), default is empty for ALL APs"
    },
    "txpower_only": {
      "type": "boolean",
      "description": "Only changing TX Power (will not disconnect clients)",
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

`mistapi.api.v1.utilities.wi-fi.optimizeSiteRrm()`

## Usage Context

Triggers an RRM (Radio Resource Management) optimization cycle at a site. Forces immediate recalculation of channel assignments and power levels for all APs.

## Gotchas

- APs may change channels and power levels, briefly disconnecting some clients.
- RRM optimization normally runs automatically — manual triggers should be rare.
- Schedule during low-usage periods to minimize client impact.

## Related Endpoints

- [POST_sites_site_id_devices_reset_radio_config.md](POST_sites_site_id_devices_reset_radio_config.md) — Reset to RRM defaults before optimizing

## MistHelper Notes

Not currently used by MistHelper via REST API.
