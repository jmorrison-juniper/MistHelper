# upgradeSiteMxEdges

> upgradeSiteMxEdges

## HTTP

`POST /api/v1/sites/{site_id}/mxedges/upgrade`

## Description

Upgrade Mist Edges in a Site.

See [Org Mist Edges](/#tag/Utilities-Upgrade/operation/upgradeOrgMxEdges) for package upgrades

See [Org Mist Edges Distro](/#tag/Utilities-Upgrade/operation/upgradeOrgMxEdges) for distro upgrades

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

`mistapi.api.v1.sites.mxedges.upgradeSiteMxEdges()`

## Usage Context

Use this endpoint to start or create the resource at
`/api/v1/sites/{site_id}/mxedges/upgrade`.
Common use cases:

- Use it when you need to upgrade Mist Edges in a Site.
- Use it only after you read the related resource and confirm the planned change.
- Treat this endpoint as a state-changing request.
- The installed `mistapi` 0.64.0 signature is `upgradeSiteMxEdges(mist_session: mistapi.__api_session.APISession, site_id: str, body: dict | list) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `site_id`. Use identifiers from a trusted Mist read.
- The JSON body requires `mxedge_ids`. Missing required fields return a 400 response.
- This endpoint can change Mist state. Keep a recovery record before you call it.
- Upgrade calls can interrupt service. Use an approved maintenance window.

## Related Endpoints

- [GET_sites_site_id_mxedges_upgrade.md](GET_sites_site_id_mxedges_upgrade.md) -- listSiteMxEdgeUpgrades uses `GET /api/v1/sites/{site_id}/mxedges/upgrade`.
- [DELETE_sites_site_id_mxedges_mxedge_id.md](../sites/DELETE_sites_site_id_mxedges_mxedge_id.md) -- deleteSiteMxEdge uses `DELETE /api/v1/sites/{site_id}/mxedges/{mxedge_id}`.
- [GET_sites_site_id_mxedges.md](../sites/GET_sites_site_id_mxedges.md) -- listSiteMxEdges uses `GET /api/v1/sites/{site_id}/mxedges`.

## MistHelper Notes

MistHelper does not currently call `upgradeSiteMxEdges`.
Verification source: `git grep -n "upgradeSiteMxEdges" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
