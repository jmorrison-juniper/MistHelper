# startSiteAutoMapAssignment

> startSiteAutoMapAssignment

## HTTP

`POST /api/v1/sites/{site_id}/auto_map_assignment`

## Description

Start the auto map assignment process for a site. The service automatically assigns APs to maps based on BLE ranging data and requires at least 3 APs with compatible firmware and model support for BLE.

Repeated POST requests while a site assignment is still running will be rejected.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "additionalProperties": false,
  "description": "Request options for validating or starting automatic AP map assignment",
  "properties": {
    "dryrun": {
      "default": false,
      "description": "If `true`, validates the site's APs without starting the map assignment process. Returns device validity and estimated runtime.",
      "type": "boolean"
    },
    "force_collection": {
      "default": false,
      "description": "If `true`, forces data collection via orchestration. If `false`, attempts to use existing BLE data first.",
      "type": "boolean"
    }
  },
  "type": "object"
}
```

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Auto map assignment start response",
  "properties": {
    "devices": {
      "additionalProperties": {
        "additionalProperties": false,
        "description": "Per-device validation result for auto map assignment",
        "properties": {
          "reason": {
            "description": "Provides the reason for the status if the AP is invalid",
            "type": "string"
          },
          "valid": {
            "description": "Indicates whether the device meets requirements for auto map assignment",
            "type": "boolean"
          }
        },
        "type": "object"
      },
      "description": "Contains the validation status of each device. The property key is the device MAC address.",
      "type": "object"
    },
    "estimated_runtime": {
      "description": "Estimated runtime for the process in seconds",
      "type": "integer"
    },
    "reason": {
      "description": "Provides the reason for the status",
      "type": "string"
    },
    "started": {
      "description": "Indicates whether the auto map assignment process has started",
      "type": "boolean"
    },
    "valid": {
      "description": "Indicates whether the auto map assignment request is valid",
      "type": "boolean"
    }
  },
  "type": "object"
}
```

## Errors

| Status | Description |
|--------|-------------|
| 400 | Auto map assignment already in progress |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.auto_map_assignment.startSiteAutoMapAssignment()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
