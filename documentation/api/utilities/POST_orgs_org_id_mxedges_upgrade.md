# upgradeOrgMxEdges

> upgradeOrgMxEdges

## HTTP

`POST /api/v1/orgs/{org_id}/mxedges/upgrade`

## Description

Upgrade Mist Edges

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "allow_downgrades": {
      "type": "object",
      "properties": {
        "mxagent": {
          "type": "boolean",
          "default": false
        },
        "mxdas": {
          "type": "boolean",
          "default": false
        },
        "mxocproxy": {
          "type": "boolean",
          "default": false
        },
        "radsecproxy": {
          "type": "boolean",
          "default": false
        },
        "tunterm": {
          "type": "boolean",
          "default": false
        }
      },
      "description": "Whether downgrade is allowed when running version is higher than expected version for each service"
    },
    "canary_phases": {
      "type": "array",
      "items": {
        "type": "integer",
        "contentEncoding": "int32"
      },
      "description": "Only if `strategy`==`canary`. Phases for canary deployment. Each phase represents percentage of devices that need to be upgraded in that phase. default is [1, 10, 50, 100]",
      "default": [
        1,
        10,
        50,
        100
      ]
    },
    "channel": {
      "type": "string",
      "description": "upgrade channel to follow. enum: `alpha`, `beta`, `stable`"
    },
    "distro": {
      "type": "string",
      "description": "Distro upgrade, optional, to specific codename (e.g. bullseye) with highest qualified versions"
    },
    "max_failure_percentage": {
      "type": "integer",
      "description": "Failure threshold before we stop the upgrade and mark it as failed",
      "contentEncoding": "int32",
      "default": 5
    },
    "mxedge_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "List of mxedge IDs to upgrade. If not specified, it means all the org mxedges."
    },
    "start_time": {
      "type": "integer",
      "description": "Upgrade start time in epoch seconds, default is now",
      "contentEncoding": "int32"
    },
    "strategy": {
      "type": "string",
      "description": "enum:\n  * `big_bang`: upgrade all at once, no orchestration\n  * `serial`: one at a time'\n  * `canary`: upgrade in phases"
    },
    "versions": {
      "type": "object",
      "properties": {
        "mxagent": {
          "type": "string"
        },
        "mxdas": {
          "type": "string",
          "default": "current"
        },
        "mxocproxy": {
          "type": "string",
          "default": "current"
        },
        "radsecproxy": {
          "type": "string",
          "default": "current"
        },
        "tunterm": {
          "type": "string"
        }
      },
      "required": [
        "mxagent",
        "tunterm"
      ],
      "description": "Version to upgrade for each service, `current` / `latest` / `default` / specific version (e.g. `2.5.100`).\\nIgnored if distro upgrade, `tunterm`, `radsecproxy`, `mxagent`, `mxocproxy`, `mxdas` or `mxnacedge`"
    }
  },
  "required": [
    "mxedge_ids"
  ],
  "description": "Request Body"
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

`mistapi.api.v1.utilities.upgrade.upgradeOrgMxEdges()`

## Usage Context

Initiates a firmware upgrade for Mist Edge appliances across the organization. Mist Edge appliances provide local tunnel termination and edge services.

## Gotchas

- Mist Edge upgrades may briefly disrupt tunnel services during the reboot phase.
- Coordinate with HA pair failover if using clustered Mist Edge deployments.

## Related Endpoints

- [GET_orgs_org_id_mxedges_upgrade.md](GET_orgs_org_id_mxedges_upgrade.md) — Monitor upgrade progress
- [GET_orgs_org_id_mxedges_upgrade_upgrade_id.md](GET_orgs_org_id_mxedges_upgrade_upgrade_id.md) — Specific upgrade status

## MistHelper Notes

Not currently used by MistHelper directly.
