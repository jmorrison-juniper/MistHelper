# listSiteMxEdgeUpgrades

> listSiteMxEdgeUpgrades

## HTTP

`GET /api/v1/sites/{site_id}/mxedges/upgrade`

## Description

List Mist Edge upgrade operations for a site. Use [List Org Mist Edge Upgrades](/#operations/listOrgMxEdgeUpgrades) to retrieve Mist Edge upgrade operations across the organization.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

Example response

```json
{
  "description": "Mist Edge upgrade records returned by list upgrade operations",
  "items": {
    "additionalProperties": false,
    "description": "Mist Edge upgrade details response",
    "properties": {
      "channel": {
        "description": "Upgrade channel used to select Mist Edge package versions",
        "minLength": 1,
        "type": "string"
      },
      "counts": {
        "additionalProperties": false,
        "description": "Counts of Mist Edge upgrades by current status",
        "properties": {
          "failed": {
            "description": "Number of Mist Edge upgrades that failed",
            "type": "integer"
          },
          "queued": {
            "description": "Number of Mist Edge upgrades waiting to run",
            "type": "integer"
          },
          "success": {
            "description": "Number of Mist Edge upgrades completed successfully",
            "type": "integer"
          },
          "upgrading": {
            "description": "Number of Mist Edge upgrades currently in progress",
            "type": "integer"
          }
        },
        "required": [
          "queued",
          "upgrading",
          "success",
          "failed"
        ],
        "type": "object"
      },
      "id": {
        "description": "Unique ID of the object instance in the Mist Organization",
        "examples": [
          "53f10664-3ce8-4c27-b382-0ef66432349f"
        ],
        "format": "uuid",
        "readOnly": true,
        "type": "string"
      },
      "status": {
        "description": "Current status of the Mist Edge upgrade",
        "minLength": 1,
        "type": "string"
      },
      "strategy": {
        "description": "Rollout strategy used for the Mist Edge upgrade",
        "minLength": 1,
        "type": "string"
      },
      "versions": {
        "additionalProperties": true,
        "description": "Per-service target versions for this Mist Edge upgrade",
        "type": "object"
      }
    },
    "required": [
      "status",
      "strategy",
      "versions",
      "channel",
      "id",
      "counts"
    ],
    "type": "object"
  },
  "type": "array"
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

`mistapi.api.v1.utilities.upgrade.listSiteMxEdgeUpgrades()`

## Usage Context

*To be enriched by AI agent.*

## Gotchas

*To be enriched by AI agent.*

## Related Endpoints

*To be enriched by AI agent.*

## MistHelper Notes

*To be enriched by AI agent.*
