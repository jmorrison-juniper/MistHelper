# startSiteFlowCapture

> startSiteFlowCapture

## HTTP

`POST /api/v1/sites/{site_id}/flow_capture`

## Description

Start a flow capture session on one or more online switches running JMA firmware. The same filter is applied to every switch. Only one packet or flow capture session can be active per site at a time.

The captured flow records are streamed over websocket rather than returned in the HTTP response.

#### Subscribe to Flow Capture outputs
`WS /api-ws/v1/stream`

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "additionalProperties": false,
  "description": "Flow capture request for one or more switches",
  "properties": {
    "dst_ip": {
      "type": "string"
    },
    "dst_port": {
      "maximum": 65535,
      "minimum": 1,
      "type": "integer"
    },
    "duration": {
      "default": 600,
      "maximum": 900,
      "minimum": 60,
      "type": "integer"
    },
    "protocol": {
      "description": "Flow capture protocol filter. enum: `tcp`, `udp`, `icmp`, `icmp6`",
      "enum": [
        "tcp",
        "udp",
        "icmp",
        "icmp6"
      ],
      "type": "string"
    },
    "src_ip": {
      "type": "string"
    },
    "src_port": {
      "maximum": 65535,
      "minimum": 1,
      "type": "integer"
    },
    "switches": {
      "items": {
        "type": "string"
      },
      "minItems": 1,
      "type": "array"
    }
  },
  "required": [
    "switches"
  ],
  "type": "object"
}
```

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Current flow capture session status for a site",
  "properties": {
    "capture_filter": {
      "additionalProperties": false,
      "description": "Normalized filter applied to a flow capture session",
      "properties": {
        "dst_ip": {
          "type": "string"
        },
        "dst_port": {
          "type": "integer"
        },
        "protocol": {
          "description": "Flow capture protocol filter. enum: `tcp`, `udp`, `icmp`, `icmp6`",
          "enum": [
            "tcp",
            "udp",
            "icmp",
            "icmp6"
          ],
          "type": "string"
        },
        "src_ip": {
          "type": "string"
        },
        "src_port": {
          "type": "integer"
        }
      },
      "type": "object"
    },
    "duration": {
      "type": "integer"
    },
    "enabled": {
      "type": "boolean"
    },
    "expiry": {
      "type": "integer"
    },
    "id": {
      "format": "uuid",
      "type": "string"
    },
    "invalid_switches": {
      "additionalProperties": true,
      "description": "Switches that failed flow capture validation",
      "type": "object"
    },
    "org_id": {
      "description": "Unique identifier of a Mist organization",
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ],
      "format": "uuid",
      "readOnly": true,
      "type": "string"
    },
    "site_id": {
      "description": "Unique identifier of a Mist site",
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ],
      "format": "uuid",
      "readOnly": true,
      "type": "string"
    },
    "switch_count": {
      "type": "integer"
    },
    "timestamp": {
      "type": "integer"
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

`mistapi.api.v1.utilities.pcaps.startSiteFlowCapture()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
