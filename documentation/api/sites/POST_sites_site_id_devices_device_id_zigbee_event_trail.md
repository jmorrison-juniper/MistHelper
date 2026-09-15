# startSiteDeviceZigbeeEventTrail

> startSiteDeviceZigbeeEventTrail

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/zigbee_event_trail`

## Description

Start a Zigbee event trail session on an AP. Returns a `session` that the UI can use to stream results.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Response containing the session identifier for a Zigbee event or packet trail operation",
  "properties": {
    "session": {
      "description": "Session ID the UI can use to stream trail results",
      "examples": [
        "7a5f7796-83ee-11e5-95c6-1258369c38a9"
      ],
      "format": "uuid",
      "type": "string"
    }
  },
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

`mistapi.api.v1.sites.devices_-_wireless.startSiteDeviceZigbeeEventTrail()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
