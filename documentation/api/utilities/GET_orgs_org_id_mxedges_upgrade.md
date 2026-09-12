# listOrgMxEdgeUpgrades

> listOrgMxEdgeUpgrades

## HTTP

`GET /api/v1/orgs/{org_id}/mxedges/upgrade`

## Description

Get List of Org Mist Edge Upgrades

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "array",
  "items": {
    "title": "response_mxedge_upgrade",
    "required": [
      "channel",
      "counts",
      "id",
      "status",
      "strategy",
      "versions"
    ],
    "type": "object",
    "properties": {
      "channel": {
        "minLength": 1,
        "type": "string"
      },
      "counts": {
        "title": "mxedge_upgrade_response_counts",
        "required": [
          "failed",
          "queued",
          "success",
          "upgrading"
        ],
        "type": "object",
        "properties": {
          "failed": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "queued": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "success": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "upgrading": {
            "type": "integer",
            "contentEncoding": "int32"
          }
        }
      },
      "id": {
        "type": "string",
        "description": "Unique ID of the object instance in the Mist Organization",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "53f10664-3ce8-4c27-b382-0ef66432349f"
        ]
      },
      "status": {
        "minLength": 1,
        "type": "string"
      },
      "strategy": {
        "minLength": 1,
        "type": "string"
      },
      "versions": {
        "type": "object"
      }
    }
  },
  "description": ""
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

`mistapi.api.v1.utilities.upgrade.listOrgMxEdgeUpgrades()`

## Usage Context

Lists all Mist Edge firmware upgrade records for the organization. Use this to track upgrade history and monitor active Mist Edge upgrades.

## Gotchas

- Mist Edge upgrades are separate from standard device upgrades — use the mxedges-specific endpoints.

## Related Endpoints

- [GET_orgs_org_id_mxedges_upgrade_upgrade_id.md](GET_orgs_org_id_mxedges_upgrade_upgrade_id.md) — Specific upgrade details
- [POST_orgs_org_id_mxedges_upgrade.md](POST_orgs_org_id_mxedges_upgrade.md) — Start a Mist Edge upgrade

## MistHelper Notes

Not currently used by MistHelper directly.
