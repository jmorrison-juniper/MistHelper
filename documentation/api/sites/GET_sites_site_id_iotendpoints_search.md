# searchSiteIotEndpoints

> searchSiteIotEndpoints

## HTTP

`GET /api/v1/sites/{site_id}/iotendpoints/search`

## Description

Search IoT Endpoints

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| ap_mac | string | No |  |  | Filter results by AP MAC address |
| mac | string | No |  |  | Filter results by MAC address |
| type | string | No |  |  | IoT endpoint type. enum: `zigbee` |
| mfg | string | No |  |  | Filter results by manufacturer |
|  | string | No |  |  |  |
|  | string | No |  |  |  |
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
  "description": "Time-bounded response for IoT endpoint search results",
  "properties": {
    "end": {
      "description": "Epoch timestamp, in seconds, for the end of the IoT endpoint search window",
      "type": "number"
    },
    "results": {
      "description": "IoT endpoint statistics returned by a search response",
      "items": {
        "additionalProperties": false,
        "description": "IoT endpoint statistics returned by a search response",
        "properties": {
          "ap_mac": {
            "description": "MAC address of the AP the endpoint was seen on",
            "examples": [
              "5c5b350e0001"
            ],
            "type": "string"
          },
          "id": {
            "description": "Unique identifier for the IoT endpoint",
            "examples": [
              "63f9e299182b63f9"
            ],
            "type": "string"
          },
          "lqi": {
            "description": "Link Quality Indicator (0\u2013255)",
            "maximum": 255,
            "minimum": 0,
            "type": "integer"
          },
          "mac": {
            "description": "Endpoint MAC address reported in IoT statistics",
            "examples": [
              "63f9e299182b63f9"
            ],
            "type": "string"
          },
          "mfg": {
            "description": "Manufacturer name reported for the IoT endpoint",
            "examples": [
              "Assa Abloy"
            ],
            "type": "string"
          },
          "model": {
            "description": "Device model reported for the IoT endpoint",
            "examples": [
              "Assa Abloy"
            ],
            "type": "string"
          },
          "timestamp": {
            "description": "Epoch timestamp of the last observation, in seconds",
            "type": "number"
          },
          "type": {
            "description": "IoT endpoint type. enum: `zigbee`",
            "examples": [
              "zigbee"
            ],
            "type": "string"
          }
        },
        "type": "object"
      },
      "type": "array",
      "uniqueItems": true
    },
    "start": {
      "description": "Epoch timestamp, in seconds, for the start of the IoT endpoint search window",
      "type": "number"
    },
    "total": {
      "description": "Number of IoT endpoint records matching the search filters",
      "type": "integer"
    }
  },
  "required": [
    "start",
    "end",
    "total",
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

`mistapi.api.v1.sites.stats_-_iot_endpoints.searchSiteIotEndpoints()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
