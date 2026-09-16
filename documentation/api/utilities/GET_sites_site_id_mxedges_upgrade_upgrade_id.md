# getSiteMxEdgeUpgrade

> getSiteMxEdgeUpgrade

## HTTP

`GET /api/v1/sites/{site_id}/mxedges/upgrade/{upgrade_id}`

## Description

Get Mist Edge Upgrade

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

`mistapi.api.v1.sites.mxedges.getSiteMxEdgeUpgrade()`

## Usage Context

Use this endpoint to read the resource at
`/api/v1/sites/{site_id}/mxedges/upgrade/{upgrade_id}`.
Common use cases:

- Use it when you need to get Mist Edge Upgrade.
- Use it in an audit or status workflow before you make a related change.
- Treat this endpoint as a read-only request.
- The installed `mistapi` 0.64.0 signature is `getSiteMxEdgeUpgrade(mist_session: mistapi.__api_session.APISession, site_id: str, upgrade_id: str) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `site_id`, `upgrade_id`. Use identifiers from a trusted Mist read.
- Upgrade calls can interrupt service. Use an approved maintenance window.

## Related Endpoints

- [PUT_sites_site_id_mxedges_upgrade_upgrade_id.md](PUT_sites_site_id_mxedges_upgrade_upgrade_id.md) -- updateSiteMxEdgeUpgrade uses `PUT /api/v1/sites/{site_id}/mxedges/upgrade/{upgrade_id}`.
- [GET_sites_site_id_mxedges_upgrade.md](GET_sites_site_id_mxedges_upgrade.md) -- listSiteMxEdgeUpgrades uses `GET /api/v1/sites/{site_id}/mxedges/upgrade`.
- [POST_sites_site_id_mxedges_upgrade.md](POST_sites_site_id_mxedges_upgrade.md) -- upgradeSiteMxEdges uses `POST /api/v1/sites/{site_id}/mxedges/upgrade`.

## MistHelper Notes

MistHelper does not currently call `getSiteMxEdgeUpgrade`.
Verification source: `git grep -n "getSiteMxEdgeUpgrade" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
