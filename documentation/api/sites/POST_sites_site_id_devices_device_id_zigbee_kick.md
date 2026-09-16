# kickSiteDeviceZigbeeClients

> kickSiteDeviceZigbeeClients

## HTTP

`POST /api/v1/sites/{site_id}/devices/{device_id}/zigbee_kick`

## Description

Kick one or more Zigbee clients from a Zigbee-enabled AP. The AP must be connected.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "additionalProperties": false,
  "description": "Request body for kicking one or more Zigbee clients from an AP",
  "properties": {
    "macs": {
      "description": "One or more Zigbee EUI-64 (8-byte) MACs. Accepts colon-separated (`00:17:7a:01:06:0c:ae:9f`) or plain hex (`00177a01060cae9f`). Must be non-empty.",
      "examples": [
        [
          "00177a01060cae9f",
          "00177a01060caea1"
        ]
      ],
      "items": {
        "type": "string"
      },
      "minItems": 1,
      "type": "array"
    }
  },
  "required": [
    "macs"
  ],
  "type": "object"
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

`mistapi.api.v1.sites.devices_-_wireless.kickSiteDeviceZigbeeClients()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
