# upgradeSiteDevices

> upgradeSiteDevices

## HTTP

`POST /api/v1/sites/{site_id}/devices/upgrade`

## Description

Upgrade Site Device

**Note**: this call doesn’t guarantee the devices to be upgraded right away (they may be offline)

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

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
      "description": "Only if `strategy`==`canary`. Phases for canary deployment. Each phase represents percentage of devices that need to be upgraded in that phase. default is [1, 10, 50, 100]",
      "default": [
        1,
        10,
        50,
        100
      ]
    },
    "device_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "id's of devices which will be selected for upgrade"
    },
    "enable_p2p": {
      "type": "boolean",
      "description": "For APs only. Whether to allow local AP-to-AP FW upgrade"
    },
    "force": {
      "type": "boolean",
      "description": "`force`==`true` will force upgrade when requested version is same as running version",
      "default": false
    },
    "max_failure_percentage": {
      "maximum": 100.0,
      "minimum": 0.0,
      "type": "integer",
      "description": "If `strategy`!=`big_bang`. percentage of failures allowed across the entire upgrade",
      "contentEncoding": "int32",
      "default": 5
    },
    "max_failures": {
      "type": "array",
      "items": {
        "type": "integer",
        "contentEncoding": "int32"
      },
      "description": "If `strategy`==`canary`. Number of failures allowed within each phase. Only applicable for `canary`. Array length should be same as `canary_phases`. Will be used if provided, else `max_failure_percentage` will be used"
    },
    "models": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Models which will be selected for upgrade"
    },
    "p2p_cluster_size": {
      "minimum": 0.0,
      "type": "integer",
      "description": "For APs only and if `enable_p2p`==`true`.",
      "contentEncoding": "int32",
      "default": 10,
      "examples": [
        0
      ]
    },
    "p2p_parallelism": {
      "type": "integer",
      "description": "For APs only and if `enable_p2p`==`true`. Number of parallel p2p download batches to create",
      "contentEncoding": "int32"
    },
    "reboot": {
      "type": "boolean",
      "description": "For Switches and Gateways only (APs are automatically rebooted). Reboot device immediately after upgrade is completed",
      "default": false
    },
    "reboot_at": {
      "type": "integer",
      "description": "For Switches and Gateways only and if `reboot`==`true`. Reboot start time in epoch seconds, default is `start_time`",
      "contentEncoding": "int32",
      "examples": [
        1624399840
      ]
    },
    "rrm_first_batch_percentage": {
      "type": "integer",
      "description": "For APs only and if `strategy`==`rrm`. Percentage of APs that need to be present in the first RRM batch",
      "contentEncoding": "int32",
      "examples": [
        2
      ]
    },
    "rrm_max_batch_percentage": {
      "type": "integer",
      "description": "For APs only and if `strategy`==`rrm`. Max percentage of APs that need to be present in each RRM batch",
      "contentEncoding": "int32",
      "examples": [
        10
      ]
    },
    "rrm_mesh_upgrade": {
      "type": "string",
      "description": "For APs only and if `strategy`==`rrm`. Whether to upgrade mesh AP\u2019s parallelly or sequentially at the end of the upgrade. enum: `parallel`, `sequential`"
    },
    "rrm_node_order": {
      "type": "string",
      "description": "For APs only and if `strategy`==`rrm`. Used in rrm to determine whether to start upgrade from fringe or center AP\u2019s. enum: `center_to_fringe`, `fringe_to_center`"
    },
    "rrm_slow_ramp": {
      "type": "boolean",
      "description": "For APs only and if `strategy`==`rrm`. True will make rrm batch sizes slowly ramp up"
    },
    "rules": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": {
          "type": "string"
        },
        "description": "Rules used to identify devices which will be selected for upgrade. Device will be selected as long as it satisfies any one rule  \nProperty key defines the type of matching, value is the string to match. e.g:\n  * `match_name`: Device name must match the property value\n  * `match_name[0:3]`: Device name must match the first 3 letters of the property value\n  * `match_name[2:6]`: Device name must match the property value from the 2nd to the 6th letter\n  * `match_model`: Device model must match the property value\n  * `match_model[1:3]`: Device model must match the property value from the 1st to the 3rd letter\n * `match_role`: Device role must match the property value\n  * `match_role[0:3]`: Device role must match the property value from the 1st to the 3rd letter\n * `match_evpn_role`: Device EVPN topology role must match the property value\n  * `match_evpn_role[0:3]`: Device EVPN topology role must match the property value from the 1st to the 3rd letter",
        "examples": [
          [
            {
              "match_model": "AP43",
              "match_name[2:8]": "access"
            },
            {
              "match_model": "AP45"
            }
          ]
        ]
      },
      "description": "Rules used to identify devices which will be selected for upgrade. Device will be selected as long as it satisfies any one rule  \nProperty key defines the type of matching, value is the string to match. e.g:\n  * `match_name`: Device name must match the property value\n  * `match_name[0:3]`: Device name must match the first 3 letters of the property value\n  * `match_name[2:6]`: Device name must match the property value from the 2nd to the 6th letter\n  * `match_model`: Device model must match the property value\n  * `match_model[1:3]`: Device model must match the property value from the 1st to the 3rd letter\n * `match_role`: Device role must match the property value\n  * `match_role[0:3]`: Device role must match the property value from the 1st to the 3rd letter\n * `match_evpn_role`: Device EVPN topology role must match the property value\n  * `match_evpn_role[0:3]`: Device EVPN topology role must match the property value from the 1st to the 3rd letter",
      "examples": [
        [
          {
            "match_model": "AP43",
            "match_name[2:8]": "access"
          },
          {
            "match_model": "AP45"
          }
        ]
      ]
    },
    "snapshot": {
      "type": "boolean",
      "description": "For Junos devices only. Perform recovery snapshot after device is rebooted",
      "default": false
    },
    "start_time": {
      "type": "integer",
      "description": "Upgrade start time in epoch seconds, default is now",
      "contentEncoding": "int32",
      "examples": [
        1624399840
      ]
    },
    "strategy": {
      "type": "string",
      "description": "enum: `big_bang` (upgrade all at once), `canary`, `rrm` (APs only), `serial` (one at a time)"
    },
    "version": {
      "type": "string",
      "description": "Specific version / stable, default is to use the latest available version",
      "examples": [
        "3.1.5"
      ]
    }
  },
  "description": "Request Body"
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "upgrade_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "examples": [
        "4316c116-0acb-4c43-8f06-6723154e741e"
      ]
    }
  },
  "required": [
    "upgrade_id"
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

`mistapi.api.v1.utilities.upgrade.upgradeSiteDevices()`

## Usage Context

Initiates a firmware upgrade for devices at a specific site. Allows targeting by device model, MAC address, or all devices of a type at the site.

## Gotchas

- Devices reboot during upgrade and are briefly offline.
- Site-level upgrades are recommended over org-level for better control and rollback capability.
- Confirm the target version is correct before proceeding.

## Related Endpoints

- [GET_sites_site_id_devices_versions.md](GET_sites_site_id_devices_versions.md) — Available versions for this site
- [GET_sites_site_id_devices_upgrade_upgrade_id.md](GET_sites_site_id_devices_upgrade_upgrade_id.md) — Monitor upgrade progress
- [POST_sites_site_id_devices_upgrade_upgrade_id_cancel.md](POST_sites_site_id_devices_upgrade_upgrade_id_cancel.md) — Cancel if needed
- [POST_orgs_org_id_devices_upgrade.md](POST_orgs_org_id_devices_upgrade.md) — Org-level upgrade (broader scope)

## MistHelper Notes

Used by Menu **90** (`FirmwareManager`) for site-specific AP firmware upgrades. Requires explicit `UPGRADE` confirmation from the user.
