# searchSiteSkyatpEvents

> searchSiteSkyatpEvents

## HTTP

`GET /api/v1/sites/{site_id}/skyatp/events/search`

## Description

Search Skyatp Events (WIP)

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
| type | string | No |  |  | Event type, e.g. cc, fs, mw |
| mac | string | No |  |  | Client MAC |
| device_mac | string | No |  |  | Device MAC |
| threat_level | integer | No |  |  | Threat level |
| ip | string | No |  |  |  |
| limit | integer | No | 100 |  |  |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "next": {
      "type": "string"
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "events_skyatp",
        "required": [
          "device_mac",
          "ip",
          "mac",
          "org_id",
          "site_id",
          "threat_level",
          "timestamp",
          "type"
        ],
        "type": "object",
        "properties": {
          "device_mac": {
            "type": "string",
            "readOnly": true
          },
          "for_site": {
            "type": "boolean",
            "readOnly": true
          },
          "ip": {
            "type": "string",
            "readOnly": true
          },
          "mac": {
            "type": "string",
            "readOnly": true
          },
          "org_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "threat_level": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "type": {
            "type": "string",
            "readOnly": true
          }
        },
        "description": "SkyATP events"
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "end",
    "limit",
    "results",
    "start",
    "total"
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.skyatp.searchSiteSkyatpEvents()`

## Usage Context

Searches Sky ATP events at a site (malware detection, threat feeds, blocked connections).

## Gotchas

- Requires Sky ATP license. Uses cursor-based pagination.

## Related Endpoints

- [GET_sites_site_id_skyatp_events_count.md](GET_sites_site_id_skyatp_events_count.md) — Count ATP events
- [GET_sites_site_id_aamwprofiles_derived.md](GET_sites_site_id_aamwprofiles_derived.md) — AAMW profiles

## MistHelper Notes

Not currently used by MistHelper directly.
