# getSiteRogueAP

> getSiteRogueAP

## HTTP

`GET /api/v1/sites/{site_id}/rogues/{rogue_bssid}`

## Description

Get Rogue AP Details

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| rogue_bssid | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "manufacture": {
      "type": "string"
    },
    "seen_as_client": {
      "type": "boolean"
    }
  },
  "required": [
    "manufacture",
    "seen_as_client"
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

`mistapi.api.v1.sites.rogues.getSiteRogueAP()`

## Usage Context

Retrieves details of a specific rogue AP by BSSID, including classification, signal strength, and detection history.

## Gotchas

- BSSID format must match exactly (colon-separated lowercase hex).

## Related Endpoints

- [GET_sites_site_id_rogues_events_search.md](GET_sites_site_id_rogues_events_search.md) — Search rogue events
- [GET_sites_site_id_insights_rogues.md](GET_sites_site_id_insights_rogues.md) — Rogue insights

## MistHelper Notes

Used by Menu **81** for rogue AP investigation.
