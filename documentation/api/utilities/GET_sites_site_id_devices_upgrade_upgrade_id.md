# getSiteDeviceUpgrade

> getSiteDeviceUpgrade

## HTTP

`GET /api/v1/sites/{site_id}/devices/upgrade/{upgrade_id}`

## Description

Get Site Device Upgrade

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| upgrade_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "canary_phases": {
      "type": "array",
      "items": {
        "type": "integer",
        "contentEncoding": "int32"
      },
      "description": "phases for canary deployment. Each phase represents percentage of devices that need to be upgraded in that phase.",
      "default": [
        1,
        10,
        50,
        100
      ]
    },
    "current_phase": {
      "type": "integer",
      "description": "Current canary or rrm phase in progress",
      "contentEncoding": "int32"
    },
    "enable_p2p": {
      "type": "boolean",
      "description": "Whether to allow local AP-to-AP FW upgrade",
      "default": false
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
    "p2p_cluster_size": {
      "type": "integer",
      "description": "size to split the devices for p2p",
      "contentEncoding": "int32",
      "default": 10
    },
    "p2p_parallelism": {
      "type": "integer",
      "description": "number of parallel p2p download batches to create",
      "contentEncoding": "int32",
      "default": 1
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
    "targets": {
      "type": "object",
      "properties": {
        "download_requested": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of devices MAC Addresses which cloud has requested to download firmware"
        },
        "downloaded": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of devices MAC Addresses which have the firmware downloaded"
        },
        "downloading": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of devices MAC Addresses which are currently downloading the firmware"
        },
        "failed": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of devices MAC Addresses which have failed to upgrade"
        },
        "reboot_in_progress": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of devices MAC Addresses which are rebooting"
        },
        "rebooted": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of devices MAC Addresses which have rebooted successfully"
        },
        "scheduled": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of devices MAC Addresses which cloud has scheduled an upgrade for"
        },
        "skipped": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of devices MAC Addresses which skipped upgrade since requested version was same as running version. Use force to always upgrade"
        },
        "total": {
          "type": "integer",
          "description": "Count of devices part of this upgrade",
          "contentEncoding": "int32"
        },
        "upgraded": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Count of devices which have upgraded successfully"
        }
      },
      "readOnly": true
    },
    "upgrade_plan": {
      "type": "object",
      "additionalProperties": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "If `strategy`!=`big_bang`, a dictionary of phase number to devices part of that phase"
      },
      "description": "If `strategy`!=`big_bang`, a dictionary of phase number to devices part of that phase"
    }
  },
  "required": [
    "id"
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

`mistapi.api.v1.utilities.upgrade.getSiteDeviceUpgrade()`

## Usage Context

Retrieves detailed status of a specific site-level device firmware upgrade.

## Gotchas

- No known gotchas; standard GET by ID pattern.

## Related Endpoints

- [GET_sites_site_id_devices_upgrade.md](GET_sites_site_id_devices_upgrade.md) — List all site upgrades
- [POST_sites_site_id_devices_upgrade_upgrade_id_cancel.md](POST_sites_site_id_devices_upgrade_upgrade_id_cancel.md) — Cancel this upgrade

## MistHelper Notes

Used by Menu **90** (`FirmwareManager`) to track individual site upgrade progress.
