# upgradeOrgDevices

> upgradeOrgDevices

## HTTP

`POST /api/v1/orgs/{org_id}/devices/upgrade`

## Description

Upgrade Multiple Sites (Only supported for Access Points upgrades)

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
  "title": "upgrade_org_devices",
  "type": "object",
  "properties": {
    "all_sites": {
      "type": "boolean",
      "description": "If `true`, will upgrade all sites in this org",
      "default": false
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
    "device_type": {
      "type": "string",
      "description": "enum: `ap`, `gateway`, `switch`"
    },
    "download_strategy": {
      "type": "string",
      "description": "enum:\n  * `big_bang`: download all at once, no orchestration\n  * `serial`: one at a time'\n  * `canary`: upgrade in phases"
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
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "description": "Only devices of these model types will be selected for upgrade"
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
    "reboot_at": {
      "type": "integer",
      "description": "For Switches and Gateways only and if `reboot`==`true`. Reboot start time in epoch seconds, default is `start_time`",
      "contentEncoding": "int32",
      "examples": [
        1624399840
      ],
      "deprecated": true
    },
    "reboot_datetime": {
      "type": "string",
      "description": "Process start date and time, ISO8601 format. Exclude timezone component if site local timezone needs to be used",
      "examples": [
        "2024-06-13 15:00:00-07:00"
      ]
    },
    "reboot_strategy": {
      "type": "string",
      "description": "enum: `big_bang` (upgrade all at once), `canary`, `rrm` (APs only), `serial` (one at a time)"
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
    "site_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "Only devices belonging to these sites will be selected for upgrade. Will be ignored if `all_sites`==`true`"
    },
    "snapshot": {
      "type": "boolean",
      "description": "For Junos devices only. Perform recovery snapshot after device is rebooted",
      "default": false
    },
    "start_datetime": {
      "type": "string",
      "description": "Process start date and time, ISO8601 format",
      "examples": [
        "2024-06-13 15:00:00-07:00"
      ]
    },
    "start_time": {
      "type": "integer",
      "description": "Upgrade start time in epoch seconds, default is now",
      "contentEncoding": "int32",
      "examples": [
        1624399840
      ],
      "deprecated": true
    },
    "strategy": {
      "type": "string",
      "description": "enum: `big_bang` (upgrade all at once), `canary`, `rrm` (APs only), `serial` (one at a time)"
    },
    "versions": {
      "type": "array",
      "items": {
        "title": "upgrade_org_devices_version",
        "type": "object",
        "properties": {
          "firmware_type": {
            "type": "string",
            "description": "enum: `ap`, `junos`"
          },
          "force": {
            "type": "boolean",
            "description": "If `firmware_type`==`ap`, set to `true` if upgrade is needed when target version <= running version",
            "default": false
          },
          "model_version": {
            "type": "object",
            "additionalProperties": {
              "type": "string"
            },
            "description": "If `firmware_type`==`junos`, used to select different versions for different models (Overrides `version` for the specified models). Property key is the hadware model (e.g. `EX4400-24MP`), Property value is the firmware version (e.g. `23.4R1.9`)"
          },
          "version": {
            "type": "string",
            "description": "version of the firmware to deploy"
          }
        }
      },
      "description": ""
    }
  }
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
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
    "strategy": {
      "type": "string",
      "description": "enum: `big_bang` (upgrade all at once), `canary`, `rrm` (APs only), `serial` (one at a time)"
    },
    "target_version": {
      "type": "string",
      "description": "Version to upgrade to",
      "examples": [
        "0.14.29411"
      ]
    },
    "upgrades": {
      "type": "array",
      "items": {
        "title": "upgrade_org_devices_upgrade",
        "type": "object",
        "properties": {
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "upgrade": {
            "title": "upgrade_org_devices_upgrade_info",
            "type": "object",
            "properties": {
              "id": {
                "type": "string",
                "description": "Unique ID of the object instance in the Mist Organization",
                "contentEncoding": "uuid",
                "readOnly": true,
                "examples": [
                  "53f10664-3ce8-4c27-b382-0ef66432349f"
                ]
              },
              "start_time": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  1717658765
                ]
              },
              "status": {
                "type": "string",
                "description": "status upgrade is in. enum: `cancelled`, `completed`, `created`, `downloaded`, `downloading`, `failed`, `upgrading`, `queued`"
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
              }
            }
          }
        }
      },
      "description": ""
    }
  }
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

`mistapi.api.v1.utilities.upgrade.upgradeOrgDevices()`

## Usage Context

Initiates a firmware upgrade for devices across the organization. Can target specific devices by MAC address, model, site, or upgrade all devices of a type. Supports scheduling and canary (staged) upgrades.

## Gotchas

- This is a destructive operation — devices reboot during upgrade and are briefly offline.
- Large-scale upgrades should use canary deployments to catch issues before full rollout.
- Specify `version` from the available versions endpoint; invalid versions are rejected.
- Upgrade windows and maintenance schedules should be coordinated with site operations.

## Related Endpoints

- [GET_orgs_org_id_devices_versions.md](GET_orgs_org_id_devices_versions.md) — Get available firmware versions first
- [GET_orgs_org_id_devices_upgrade_upgrade_id.md](GET_orgs_org_id_devices_upgrade_upgrade_id.md) — Monitor upgrade progress
- [POST_orgs_org_id_devices_upgrade_upgrade_id_cancel.md](POST_orgs_org_id_devices_upgrade_upgrade_id_cancel.md) — Cancel if issues arise
- [POST_sites_site_id_devices_upgrade.md](POST_sites_site_id_devices_upgrade.md) — Site-level upgrade (narrower scope)

## MistHelper Notes

Used by Menu **90** (`FirmwareManager`) for AP firmware upgrades (site-based or template-based targeting). Requires explicit `UPGRADE` confirmation from the user.
