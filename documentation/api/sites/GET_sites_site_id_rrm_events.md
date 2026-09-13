# listSiteRrmEvents

> listSiteRrmEvents

## HTTP

`GET /api/v1/sites/{site_id}/rrm/events`

## Description

List Site RRM Events

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
| band | string | No |  |  | 802.11 Band |
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

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
      "type": "string",
      "description": "Link to query next set of results. value is null if no next page exists."
    },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "rrm_event",
        "required": [
          "ap_id",
          "band",
          "bandwidth",
          "channel",
          "event",
          "power",
          "pre_bandwidth",
          "pre_channel",
          "pre_power",
          "pre_usage",
          "timestamp",
          "usage"
        ],
        "type": "object",
        "properties": {
          "ap_id": {
            "type": "string",
            "contentEncoding": "uuid"
          },
          "band": {
            "type": "string",
            "description": "enum: `24`, `5`, `6`"
          },
          "bandwidth": {
            "type": "integer",
            "description": "channel width for the band.enum: `0`(disabled, response only), `20`, `40`, `80` (only applicable for band_5 and band_6), `160` (only for band_6)"
          },
          "channel": {
            "type": "integer",
            "description": "Channel for the band from rrm",
            "contentEncoding": "int32"
          },
          "event": {
            "type": "string",
            "description": "enum: `interference-ap-co-channel`, `interference-ap-non-wifi`, `neighbor-ap-down`, `neighbor-ap-recovered`, `radar-detected`, `rrm-radar`, `scheduled-site_rrm`, `triggered-site_rrm`"
          },
          "power": {
            "type": "integer",
            "description": "Tx power of the radio",
            "contentEncoding": "int32"
          },
          "pre_bandwidth": {
            "type": "integer",
            "description": "(previously) channel width for the band , 0 means no previously available. enum: `0`, `20`, `40`, `80`, `160`"
          },
          "pre_channel": {
            "type": "integer",
            "description": "(previously) channel for the band, 0 means no previously available",
            "contentEncoding": "int32"
          },
          "pre_power": {
            "type": "number",
            "description": "(previously) tx power of the radio, 0 means no previously available"
          },
          "pre_usage": {
            "type": "string"
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "usage": {
            "type": "string"
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32"
    }
  },
  "required": [
    "end",
    "limit",
    "results",
    "start"
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

`mistapi.api.v1.sites.rrm.listSiteRrmEvents()`

## Usage Context

Retrieves RRM (Radio Resource Management) events at a site, showing channel and power changes made by the auto-optimization engine.

## Gotchas

- Each RRM cycle can generate many events across multiple APs simultaneously.

## Related Endpoints

- [GET_sites_site_id_rrm_current.md](GET_sites_site_id_rrm_current.md) — Current RRM state
- [GET_sites_site_id_rrm_neighbors_band_band.md](GET_sites_site_id_rrm_neighbors_band_band.md) — RF neighbors

## MistHelper Notes

Not currently used by MistHelper directly.
