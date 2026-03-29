# upgradeSsr

> upgradeSsr

## HTTP

`POST /api/v1/sites/{site_id}/ssr/{device_id}/upgrade`

## Description

Upgrade Site SSR device

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| device_id | string | Yes |  |

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
    "version": {
      "minLength": 1,
      "type": "string",
      "description": "128T firmware version to upgrade (e.g. 5.3.0-93)"
    }
  },
  "required": [
    "version"
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

`mistapi.api.v1.utilities.upgrade.upgradeSsr()`

## Usage Context

Initiates a firmware upgrade for a specific SSR device at a site. Targets a single device by `device_id` for precise upgrade control.

## Gotchas

- SSR upgrades cause brief WAN outage during reboot — plan for maintenance windows.
- For HA pairs, upgrade the standby node first, verify, then upgrade the active node.

## Related Endpoints

- [GET_sites_site_id_ssr_upgrade_upgrade_id.md](GET_sites_site_id_ssr_upgrade_upgrade_id.md) — Monitor this upgrade's progress
- [POST_orgs_org_id_ssr_upgrade.md](POST_orgs_org_id_ssr_upgrade.md) — Org-level SSR upgrade (batch operation)
- [GET_orgs_org_id_ssr_versions.md](GET_orgs_org_id_ssr_versions.md) — Available SSR versions

## MistHelper Notes

Used by Menu **99-100** (`FirmwareManager`) for per-device SSR upgrades. Requires explicit `UPGRADE` confirmation from the user.
