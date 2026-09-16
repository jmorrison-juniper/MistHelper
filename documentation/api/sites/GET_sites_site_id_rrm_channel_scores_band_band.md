# getSiteChannelScores

> getSiteChannelScores

## HTTP

`GET /api/v1/sites/{site_id}/rrm/channel_scores/band/{band}`

## Description

Get Site Channel Scores

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
|  | string | No |  |  |  |
|  | string | No |  |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Response containing RRM channel score records",
  "properties": {
    "results": {
      "description": "RRM channel score records returned for a band",
      "items": {
        "additionalProperties": false,
        "description": "RRM utilization score for a channel",
        "properties": {
          "channel": {
            "description": "RF channel number represented by this score record",
            "type": "integer"
          },
          "util_score": {
            "description": "Utilization score for the channel, 0-1, lower means cleaner RF",
            "type": "number"
          },
          "util_score_noise_floor": {
            "description": "Score contribution from noise, 0-1, lower means cleaner RF",
            "type": "number"
          },
          "util_score_non_wifi": {
            "description": "Score contribution from non-wifi utilization, 0-1, lower means cleaner RF",
            "type": "number"
          },
          "util_score_other": {
            "description": "Score contribution from RxOtherBss utilization (wifi packets destined for other radios), 0-1, lower means cleaner RF",
            "type": "number"
          },
          "util_score_radar": {
            "description": "Score contribution from radar detections, 0-1, lower means cleaner RF",
            "type": "number"
          },
          "util_score_undecodable_wifi": {
            "description": "Score contribution from undecodable wifi utilization (wifi packets which can't be decoded), 0-1, lower means cleaner RF",
            "type": "number"
          },
          "util_score_unknown_wifi": {
            "description": "Score contribution from unknown wifi utilization (wifi packets of unknown type), 0-1, lower means cleaner RF",
            "type": "number"
          }
        },
        "required": [
          "channel",
          "util_score",
          "util_score_noise_floor",
          "util_score_non_wifi",
          "util_score_other",
          "util_score_radar",
          "util_score_undecodable_wifi",
          "util_score_unknown_wifi"
        ],
        "type": "object"
      },
      "type": "array",
      "uniqueItems": true
    }
  },
  "required": [
    "results"
  ],
  "type": "object"
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

`mistapi.api.v1.sites.rrm.getSiteChannelScores()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
