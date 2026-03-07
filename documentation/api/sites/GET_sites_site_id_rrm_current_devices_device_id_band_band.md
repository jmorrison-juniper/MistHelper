# getSiteCurrentRrmConsiderations

> getSiteCurrentRrmConsiderations

## HTTP

`GET /api/v1/sites/{site_id}/rrm/current/devices/{device_id}/band/{band}`

## Description

Get Current RRM Considerations for an AP on a Specific Band

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| device_id | string | Yes |  |
| band | string | Yes | 802.11 Band |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "rrm_consideration",
        "required": [
          "channel",
          "noise",
          "util_score",
          "util_score_non_wifi",
          "util_score_other"
        ],
        "type": "object",
        "properties": {
          "channel": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "noise": {
            "type": "number"
          },
          "other_rssi": {
            "type": "number",
            "description": "Avg RSSI heard from other APs (that does NOT belongs to the same site)"
          },
          "other_ssid": {
            "type": "string",
            "description": "SSID from other AP that we heard from with the max RSSI"
          },
          "rssi": {
            "type": "number",
            "description": "Avg RSSI heard from APs (that belongs to the same site)"
          },
          "util_score": {
            "type": "number",
            "description": "utilization score, 0-1, lower means less utilization (cleaner RF)"
          },
          "util_score_non_wifi": {
            "type": "number",
            "description": "non-Wi-Fi utilization score, 0-1, lower means less utilization (cleaner RF)"
          },
          "util_score_other": {
            "type": "number",
            "description": "other utilization score, 0-1, lower means less utilization (cleaner RF)"
          }
        }
      },
      "description": ""
    }
  },
  "required": [
    "results"
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

`mistapi.api.v1.sites.rrm.getSiteCurrentRrmConsiderations()`

## Usage Context

Retrieves current RRM (Radio Resource Management) data for a specific device and radio band.

## Gotchas

- Band must be specified (e.g., `24`, `5`, `6`). Data may be empty if RRM hasn't converged.

## Related Endpoints

- [GET_sites_site_id_rrm_current.md](GET_sites_site_id_rrm_current.md) — Site RRM overview
- [GET_sites_site_id_rrm_events.md](GET_sites_site_id_rrm_events.md) — RRM events

## MistHelper Notes

Not currently used by MistHelper directly.
