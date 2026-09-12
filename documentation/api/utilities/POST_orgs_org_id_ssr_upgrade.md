# upgradeOrgSsrs

> upgradeOrgSsrs

## HTTP

`POST /api/v1/orgs/{org_id}/ssr/upgrade`

## Description

Upgrade Org SSRs

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
    "channel": {
      "type": "string",
      "description": "upgrade channel to follow. enum: `alpha`, `beta`, `stable`"
    },
    "device_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "List of 128T device IDs to upgrade"
    },
    "reboot_at": {
      "type": "integer",
      "description": "Reboot start time in epoch seconds, default is start_time, -1 disables reboot",
      "contentEncoding": "int32"
    },
    "start_time": {
      "type": "integer",
      "description": "128T firmware download start time in epoch seconds, default is now, -1 disables download",
      "contentEncoding": "int32"
    },
    "strategy": {
      "type": "string",
      "description": "enum:\n  * `big_bang`: upgrade all at once\n  * `serial`: one at a time"
    },
    "version": {
      "minLength": 1,
      "type": "string",
      "description": "128T firmware version to upgrade (e.g. 5.3.0-93)"
    }
  },
  "required": [
    "device_ids"
  ]
}
```

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "channel": {
      "minLength": 1,
      "type": "string"
    },
    "counts": {
      "title": "response_ssr_upgrade_counts",
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
    "device_type": {
      "type": "string"
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
      "type": "object",
      "additionalProperties": {
        "type": "string"
      }
    }
  },
  "required": [
    "channel",
    "counts",
    "device_type",
    "id",
    "status",
    "strategy",
    "versions"
  ]
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

`mistapi.api.v1.utilities.upgrade.upgradeOrgSsrs()`

## Usage Context

Initiates an SSR firmware upgrade across the organization. Can target specific SSR devices or upgrade all SSRs to a specified version.

## Gotchas

- SSR upgrades may cause brief WAN service interruptions during reboot. Plan maintenance windows accordingly.
- HA SSR pairs should be upgraded sequentially to maintain service continuity.
- Requires explicit confirmation due to the destructive nature of the operation.

## Related Endpoints

- [GET_orgs_org_id_ssr_versions.md](GET_orgs_org_id_ssr_versions.md) — Get available SSR versions first
- [GET_orgs_org_id_ssr_upgrade.md](GET_orgs_org_id_ssr_upgrade.md) — Monitor upgrade progress
- [POST_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md](POST_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md) — Cancel if issues arise

## MistHelper Notes

Used by Menu **99-100** (`FirmwareManager`) for SSR firmware upgrades. Requires explicit `UPGRADE` confirmation from the user.
