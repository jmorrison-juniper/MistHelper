# acceptSiteApLocalizationData

> acceptSiteApLocalizationData

## HTTP

`POST /api/v1/sites/{site_id}/maps/{map_id}/apply_autoplacement`

## Description

Accept the cached autoplacement and auto-orientation values of a map or subset of APs on a map. Any APs that have autoplacement values are stored in cache for up to 7 days while awaiting acceptance.


Accepting the autoplacement values overwrites the existing X, Y, and orientation of the accepted APs with their cached autoplacement values.

Once a decision to accept is made, or the 7-day time-to-live (TTL) expires, the cached values are deleted.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "description": "Request body to apply or clear cached autoplacement or auto-orientation values for a map or subset of APs",
  "properties": {
    "for": {
      "default": "placement",
      "description": "The selector to choose auto placement or auto orientation. enum: `orientation`, `placement`",
      "enum": [
        "orientation",
        "placement"
      ],
      "type": "string"
    },
    "macs": {
      "description": "List of AP MAC addresses to apply the action to. If omitted, the action applies to all APs on the map",
      "items": {
        "type": "string"
      },
      "type": "array"
    }
  },
  "type": "object"
}
```

## Response

### 200

Success

## Errors

| Status | Description |
|--------|-------------|
| 400 | Map does not exist or belong to specified site / Invalid localization service. Expected [placement, orientation] |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.maps_-_auto-placement.acceptSiteApLocalizationData()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
