# listSiteDeviceUpgrades

> listSiteDeviceUpgrades

## HTTP

`GET /api/v1/sites/{site_id}/devices/upgrade`

## Description

Get all upgrades for site

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| status | string | No |  |  |  |

## Request Body

None.

## Response

### 200

Example response

```json
{
  "type": "array",
  "items": {
    "title": "response_site_device_upgrades_item",
    "required": [
      "id"
    ],
    "type": "object",
    "properties": {
      "counts": {
        "type": "object",
        "properties": {
          "download_requested": {
            "type": "integer",
            "description": "Count of devices which cloud has requested to download firmware",
            "contentEncoding": "int32"
          },
          "downloaded": {
            "type": "integer",
            "description": "Count of ap's which have the firmware downloaded",
            "contentEncoding": "int32"
          },
          "failed": {
            "type": "integer",
            "description": "Count of devices which have failed to upgrade",
            "contentEncoding": "int32"
          },
          "reboot_in_progress": {
            "type": "integer",
            "description": "Count of devices which are rebooting",
            "contentEncoding": "int32"
          },
          "rebooted": {
            "type": "integer",
            "description": "Count of devices which have rebooted successfully",
            "contentEncoding": "int32"
          },
          "scheduled": {
            "type": "integer",
            "description": "Count of devices which cloud has scheduled an upgrade for",
            "contentEncoding": "int32"
          },
          "skipped": {
            "type": "integer",
            "description": "Count of devices which skipped upgrade since requested version was same as running version. Use force to always upgrade",
            "contentEncoding": "int32"
          },
          "total": {
            "type": "integer",
            "description": "Count of devices part of this upgrade",
            "contentEncoding": "int32"
          },
          "upgraded": {
            "type": "integer",
            "description": "Count of devices which have upgraded successfully",
            "contentEncoding": "int32"
          }
        },
        "readOnly": true
      },
      "current_phase": {
        "type": "integer",
        "description": "Current canary or rrm phase in progress",
        "contentEncoding": "int32"
      },
      "enable_p2p": {
        "type": "boolean",
        "description": "Whether to allow local AP-to-AP FW upgrade"
      },
      "force": {
        "type": "boolean",
        "description": "Whether to force upgrade when requested version is same as running version"
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
      "max_failure_percentage": {
        "type": "integer",
        "description": "Percentage of failures allowed",
        "contentEncoding": "int32"
      },
      "max_failures": {
        "type": "array",
        "items": {
          "type": "integer",
          "contentEncoding": "int32"
        },
        "description": "If `strategy`==`canary`. Number of failures allowed within each phase. Only applicable for `canary`. Array length should be same as `canary_phases`. Will be used if provided, else `max_failure_percentage` will be used"
      },
      "reboot_at": {
        "type": "integer",
        "description": "reboot start time in epoch",
        "contentEncoding": "int32"
      },
      "start_time": {
        "type": "integer",
        "description": "Firmware download start time in epoch",
        "contentEncoding": "int32"
      },
      "status": {
        "type": "string",
        "description": "status upgrade is in. enum: `cancelled`, `completed`, `created`, `downloaded`, `downloading`, `failed`, `upgrading`, `queued`"
      },
      "strategy": {
        "type": "string",
        "description": "enum: `big_bang` (upgrade all at once), `canary`, `rrm` (APs only), `serial` (one at a time)"
      },
      "target_version": {
        "minLength": 1,
        "type": "string",
        "description": "Version to upgrade to"
      },
      "upgrade_plan": {
        "type": "object",
        "description": "a dictionary of rrm phase number to devices part of that phase"
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "counts": {
          "download_requested": 0,
          "downloaded": 0,
          "failed": 0,
          "reboot_in_progress": 0,
          "rebooted": 0,
          "skipped": 0,
          "total": 0
        },
        "enable_p2p": true,
        "force": true,
        "id": "472f6eca-6276-4993-bfeb-53cbbbba6f28",
        "start_time": 0,
        "status": "created",
        "strategy": "big_bang",
        "target_version": "string"
      }
    ]
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

`mistapi.api.v1.utilities.upgrade.listSiteDeviceUpgrades()`

## Usage Context

Lists all device firmware upgrade records for a specific site, including status and progress.

## Gotchas

- Shows site-scoped upgrades only; org-level upgrades affecting this site appear in the org endpoint.

## Related Endpoints

- [GET_sites_site_id_devices_upgrade_upgrade_id.md](GET_sites_site_id_devices_upgrade_upgrade_id.md) — Specific upgrade details
- [POST_sites_site_id_devices_upgrade.md](POST_sites_site_id_devices_upgrade.md) — Start a site upgrade
- [POST_sites_site_id_devices_upgrade_upgrade_id_cancel.md](POST_sites_site_id_devices_upgrade_upgrade_id_cancel.md) — Cancel an upgrade

## MistHelper Notes

Used by Menu **90** (`FirmwareManager`) to monitor site-level upgrade progress.
