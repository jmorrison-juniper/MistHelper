# updateOrgMxEdgeUpgrade

> updateOrgMxEdgeUpgrade

## HTTP

`PUT /api/v1/orgs/{org_id}/mxedges/upgrade/{upgrade_id}`

## Description

Update a queued Mist Edge upgrade request, such as target versions, rollout strategy, start time, or target Mist Edge IDs. Only upgrades in `queued` state can be updated.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "description": "Request to schedule upgrades for one or more Mist Edges",
  "properties": {
    "allow_downgrades": {
      "additionalProperties": false,
      "description": "Whether downgrade is allowed when running version is higher than expected version for each service",
      "properties": {
        "mxagent": {
          "default": false,
          "description": "Whether downgrades are allowed for the mxagent service",
          "type": "boolean"
        },
        "mxdas": {
          "default": false,
          "description": "Whether downgrades are allowed for the mxdas service",
          "type": "boolean"
        },
        "mxocproxy": {
          "default": false,
          "description": "Whether downgrades are allowed for the mxocproxy service",
          "type": "boolean"
        },
        "radsecproxy": {
          "default": false,
          "description": "Whether downgrades are allowed for the radsecproxy service",
          "type": "boolean"
        },
        "tunterm": {
          "default": false,
          "description": "Whether downgrades are allowed for the tunterm service",
          "type": "boolean"
        }
      },
      "type": "object"
    },
    "canary_phases": {
      "default": [
        1,
        10,
        50,
        100
      ],
      "description": "Only if `strategy`==`canary`. Phases for canary deployment. Each phase represents percentage of devices that need to be upgraded in that phase. default is [1, 10, 50, 100]",
      "items": {
        "type": "integer"
      },
      "type": "array"
    },
    "channel": {
      "default": "stable",
      "description": "upgrade channel to follow. enum: `alpha`, `beta`, `stable`",
      "enum": [
        "alpha",
        "beta",
        "stable"
      ],
      "type": "string"
    },
    "distro": {
      "description": "Linux distribution codename for an optional distro upgrade, such as bullseye or `next` to upgrade to the next distro version. Uses highest qualified versions",
      "type": "string"
    },
    "max_failure_percentage": {
      "default": 5,
      "description": "Failure threshold before we stop the upgrade and mark it as failed",
      "type": "integer"
    },
    "mxedge_ids": {
      "description": "List of Mist Edge IDs to upgrade. If not specified, it means all the org Mist Edges.",
      "items": {
        "format": "uuid",
        "type": "string"
      },
      "type": "array"
    },
    "start_time": {
      "description": "Upgrade start time in epoch seconds, default is now",
      "type": "integer"
    },
    "strategy": {
      "default": "big_bang",
      "description": "enum:\n  * `big_bang`: upgrade all at once, no orchestration\n  * `serial`: one at a time'\n  * `canary`: upgrade in phases",
      "enum": [
        "canary",
        "big_bang",
        "serial"
      ],
      "type": "string"
    },
    "versions": {
      "additionalProperties": false,
      "description": "Version to upgrade for each service, `current` / `latest` / `default` / specific version (e.g. `2.5.100`).\\nIgnored if distro upgrade, `tunterm`, `radsecproxy`, `mxagent`, `mxocproxy`, `mxdas` or `mxnacedge`",
      "properties": {
        "mxagent": {
          "default": "current",
          "description": "Target version for the mxagent service",
          "type": "string"
        },
        "mxdas": {
          "default": "current",
          "description": "Target version for the mxdas service",
          "type": "string"
        },
        "mxocproxy": {
          "default": "current",
          "description": "Target version for the mxocproxy service",
          "type": "string"
        },
        "radsecproxy": {
          "default": "current",
          "description": "Target version for the radsecproxy service",
          "type": "string"
        },
        "tunterm": {
          "default": "current",
          "description": "Target version for the tunterm service",
          "type": "string"
        }
      },
      "required": [
        "mxagent",
        "tunterm"
      ],
      "type": "object"
    }
  },
  "required": [
    "mxedge_ids"
  ],
  "type": "object"
}
```

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

`mistapi.api.v1.orgs.mxedges.updateOrgMxEdgeUpgrade()`

## Usage Context

Use this endpoint to update the resource at
`/api/v1/orgs/{org_id}/mxedges/upgrade/{upgrade_id}`.
Common use cases:

- Use it when you need to update a queued Mist Edge upgrade request, such as target versions, rollout strategy, start time, or target Mist Edge IDs.
- Use it only after you read the related resource and confirm the planned change.
- Treat this endpoint as a state-changing request.
- The installed `mistapi` 0.64.0 signature is `updateOrgMxEdgeUpgrade(mist_session: mistapi.__api_session.APISession, org_id: str, upgrade_id: str, body: dict) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `org_id`, `upgrade_id`. Use identifiers from a trusted Mist read.
- The JSON body requires `mxedge_ids`. Missing required fields return a 400 response.
- This endpoint can change Mist state. Keep a recovery record before you call it.
- Upgrade calls can interrupt service. Use an approved maintenance window.

## Related Endpoints

- [GET_orgs_org_id_mxedges_upgrade_upgrade_id.md](GET_orgs_org_id_mxedges_upgrade_upgrade_id.md) -- getOrgMxEdgeUpgrade uses `GET /api/v1/orgs/{org_id}/mxedges/upgrade/{upgrade_id}`.
- [GET_orgs_org_id_mxedges_upgrade.md](GET_orgs_org_id_mxedges_upgrade.md) -- listOrgMxEdgeUpgrades uses `GET /api/v1/orgs/{org_id}/mxedges/upgrade`.
- [POST_orgs_org_id_mxedges_upgrade.md](POST_orgs_org_id_mxedges_upgrade.md) -- upgradeOrgMxEdges uses `POST /api/v1/orgs/{org_id}/mxedges/upgrade`.

## MistHelper Notes

MistHelper does not currently call `updateOrgMxEdgeUpgrade`.
Verification source: `git grep -n "updateOrgMxEdgeUpgrade" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
