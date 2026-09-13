# updateInstallerVirtualChassisMember

> updateInstallerVirtualChassisMember

## HTTP

`PUT /api/v1/installer/orgs/{org_id}/devices/{fpc0_mac}/vc`

## Description

The VC creation and adding member switch API will update the device’ s virtual chassis config which is applied after VC is formed to create JUNOS pre-provisioned virtual chassis configuration.

## Change to use preprovisioned VC
To switch the VC to use preprovisioned VC, enable preprovisioned in virtual_chassis config. Both vc_role master and backup will be matched to routing-engine role in Junos preprovisioned VC config.

In this config, fpc0 has to be the same as the mac of device_id. Use renumber if you want to replace fpc0 which involves device_id change.

Notice: to configure preprovisioned VC, every member of the VC must be in the inventory.

## Add new members
For models (e.g. EX4300 and up) having dedicated VC ports, it is easier to add new member switches into a VC by just connecting cables with the dedicated VC ports. Cloud will detect the new members and update the inventory.

For EX2300 VC, adding new members requires to follow the procedures below:
1. Powering on the new member switches and ensuring cables are not connected to any VC ports.
2. Claim or adopt all new member switches under the VC’s organization Inventory
3. Assign all new member switches to the same Site as the VC
4. Invoke vc command to add switches to the VC.
5. Connect the cables to the VC ports for these switches
6. After a while, the Org’s Inventory shows this new switches has been added into the VC.

## Removing member switch
To remove a member switch from the VC, following the procedures below:

1. Ensuring the VC is connected to the cloud first
2. Unplug the cable from the VC port of the switch
3. Waiting for the VC state (vc_state) of this switch is changed to not-present
4. Invoke update_vc with remove to remove this switch from the VC
5. The Org’s Inventory shows the switch is removed.

Please notice that member ID 0 (fpc0) cannot be removed. When a VC has two switches left, unplugging the cable may result in the situation that fpc0 becomes a line card (LC). When this situation is happening, please re-plug in the cable, wait for both switches becoming present (show virtual-chassis) and then removing the cable again.

## Renumber a member switch
When a member switch doesn't' work properly and needed to be replaced, the renumber API could be used. The following two types of renumber are supported:

1. Replace a non-fpc0 member switch
2. Replace fpc0. When fpc0 is replaced, PAPI device config and JUNOS config will be both updated.

For renumber to work, the following procedures are needed: 
1. Ensuring the VC is connected to the cloud and the state of the member switch to be replaced must be non present. 
2. Adding the new member switch to the VC 
3. Waiting for the VC state (vc_state) of this VC to be updated to API server 
4. Invoke vc with renumber to replace the new member switch from fpc X to

## Perprovision VC members
By specifying "preprovision" op, you can convert the current VC to pre-provisioned mode, update VC members as well as specify vc_ports when adding new members for device models without dedicated vc ports. Use renumber for fpc0 replacement which involves device_id change.

Note: 
1. vc_ports is used for adding new members and not needed if * the device model has dedicated vc ports, or * no new member is added 
2. New VC members to be added should exist in the same Site as the VC

Update Device’s VC config can achieve similar purpose by directly modifying current virtual_chassis config. However, it cannot fulfill requests to enabling vc_ports on new members that are yet to belong to current VC.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| fpc0_mac | string | Yes | FPC0 MAC Address |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "member": {
      "type": "integer",
      "description": "Only if `op`==`renumber`",
      "contentEncoding": "int32"
    },
    "members": {
      "type": "array",
      "items": {
        "title": "virtual_chassis_member_update",
        "type": "object",
        "properties": {
          "mac": {
            "type": "string",
            "description": "Required if `op`==`add` or `op`==`preprovision`."
          },
          "member": {
            "type": "integer",
            "description": "Required if `op`==`remove`",
            "contentEncoding": "int32"
          },
          "member_id": {
            "type": "integer",
            "description": "Required if `op`==`preprovision`. Optional if `op`==`add`",
            "contentEncoding": "int32"
          },
          "vc_ports": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Required if `op`==`add` or `op`==`preprovision`"
          },
          "vc_role": {
            "type": "string",
            "description": "Required if `op`==`add` or `op`==`preprovision`. enum: `backup`, `linecard`, `master`"
          }
        }
      },
      "description": ""
    },
    "new-member": {
      "type": "integer",
      "description": "Only if `op`==`renumber`",
      "contentEncoding": "int32"
    },
    "op": {
      "type": "string",
      "description": "enum: `add`, `preprovision`, `remove`, `renumber`"
    }
  },
  "description": "Request Body"
}
```

## Response

### 200

Example response

```json
{
  "type": "object",
  "properties": {
    "config_type": {
      "type": "string",
      "readOnly": true
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
    "locating": {
      "type": "boolean",
      "readOnly": true
    },
    "mac": {
      "type": "string"
    },
    "members": {
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "stats_switch_module_stat_item",
        "type": "object",
        "properties": {
          "backup_version": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "bios_version": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "boot_partition": {
            "type": "string"
          },
          "cpld_version": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "cpu_stat": {
            "title": "cpu_stat",
            "type": "object",
            "properties": {
              "idle": {
                "type": [
                  "number",
                  "null"
                ],
                "description": "Percentage of CPU time that is idle",
                "readOnly": true
              },
              "interrupt": {
                "type": [
                  "number",
                  "null"
                ],
                "description": "Percentage of CPU time being used by interrupts",
                "readOnly": true
              },
              "load_avg": {
                "type": "array",
                "items": {
                  "type": "number"
                },
                "description": "Load averages for the last 1, 5, and 15 minutes"
              },
              "system": {
                "type": [
                  "number",
                  "null"
                ],
                "description": "Percentage of CPU time being used by system processes",
                "readOnly": true
              },
              "usage": {
                "type": [
                  "number",
                  "null"
                ],
                "description": "CPU usage",
                "readOnly": true
              },
              "user": {
                "type": [
                  "number",
                  "null"
                ],
                "description": "Percentage of CPU time being used by user processes",
                "readOnly": true
              }
            }
          },
          "errors": {
            "type": "array",
            "items": {
              "title": "module_stat_item_errors_items",
              "required": [
                "since",
                "type"
              ],
              "type": "object",
              "properties": {
                "feature": {
                  "type": "string",
                  "examples": [
                    "Mist-Management"
                  ]
                },
                "minimum_version": {
                  "type": "string",
                  "examples": [
                    "128T-6.0.0-1"
                  ]
                },
                "reason": {
                  "type": "string"
                },
                "since": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    1657497600
                  ]
                },
                "type": {
                  "type": "string",
                  "examples": [
                    "FW_UPGRADE_REQUIRED_BY_FEATURE"
                  ]
                }
              }
            },
            "description": "Used to report all error states the device node is running into. An error should always have `type` and `since` fields, and could have some other fields specific to that type."
          },
          "fans": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "title": "module_stat_item_fans_items",
              "type": "object",
              "properties": {
                "airflow": {
                  "type": "string",
                  "examples": [
                    "out"
                  ]
                },
                "name": {
                  "type": "string",
                  "examples": [
                    "Fan 0"
                  ]
                },
                "rpm": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "status": {
                  "type": "string",
                  "examples": [
                    "ok"
                  ]
                }
              }
            },
            "description": ""
          },
          "fpc_idx": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "fpga_version": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "last_seen": {
            "type": [
              "number",
              "null"
            ],
            "description": "Last seen timestamp",
            "readOnly": true,
            "examples": [
              1470417522
            ]
          },
          "locating": {
            "type": "boolean"
          },
          "mac": {
            "type": "string",
            "examples": [
              "fc3342123456"
            ]
          },
          "memory_stat": {
            "type": "object",
            "properties": {
              "usage": {
                "type": "number"
              }
            },
            "required": [
              "usage"
            ],
            "description": "Memory usage stat (for virtual chassis, memory usage of master RE)"
          },
          "model": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true,
            "examples": [
              "EX4300-48P"
            ]
          },
          "optics_cpld_version": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "pending_version": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "pics": {
            "type": "array",
            "items": {
              "title": "module_stat_item_pics_item",
              "type": "object",
              "properties": {
                "index": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "model_number": {
                  "type": "string"
                },
                "port_groups": {
                  "type": "array",
                  "items": {
                    "title": "module_stat_item_pics_item_port_groups_item",
                    "type": "object",
                    "properties": {
                      "count": {
                        "type": "integer",
                        "contentEncoding": "int32"
                      },
                      "type": {
                        "type": "string"
                      }
                    }
                  },
                  "description": ""
                }
              }
            },
            "description": ""
          },
          "poe": {
            "title": "module_stat_item_poe",
            "type": "object",
            "properties": {
              "max_power": {
                "type": "number",
                "examples": [
                  250
                ]
              },
              "power_draw": {
                "type": "number",
                "examples": [
                  120.3
                ]
              },
              "status": {
                "type": "string"
              }
            }
          },
          "poe_version": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "power_cpld_version": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "psus": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "title": "module_stat_item_psus_item",
              "type": "object",
              "properties": {
                "name": {
                  "type": "string",
                  "examples": [
                    "Power Supply 0"
                  ]
                },
                "status": {
                  "type": "string",
                  "examples": [
                    "ok"
                  ]
                }
              }
            },
            "description": ""
          },
          "re_fpga_version": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "recovery_version": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "serial": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true,
            "examples": [
              "PX8716230021"
            ]
          },
          "status": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "temperatures": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "title": "module_stat_item_temperatures_item",
              "type": "object",
              "properties": {
                "celsius": {
                  "type": "number",
                  "examples": [
                    45
                  ]
                },
                "name": {
                  "type": "string",
                  "examples": [
                    "CPU"
                  ]
                },
                "status": {
                  "type": "string",
                  "examples": [
                    "ok"
                  ]
                }
              }
            },
            "description": ""
          },
          "tmc_fpga_version": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "type": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "uboot_version": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "uptime": {
            "type": [
              "integer",
              "null"
            ],
            "contentEncoding": "int32",
            "readOnly": true
          },
          "vc_links": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "title": "module_stat_item_vc_links_item",
              "type": "object",
              "properties": {
                "neighbor_module_idx": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    1
                  ]
                },
                "neighbor_port_id": {
                  "type": "string",
                  "examples": [
                    "vcp-255/1/0"
                  ]
                },
                "port_id": {
                  "type": "string",
                  "examples": [
                    "vcp-255/1/0"
                  ]
                }
              }
            },
            "description": ""
          },
          "vc_mode": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "vc_role": {
            "type": [
              "string",
              "null"
            ],
            "description": "enum: `master`, `backup`, `linecard`",
            "readOnly": true,
            "examples": [
              "master"
            ]
          },
          "vc_state": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "version": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          }
        }
      },
      "description": ""
    },
    "model": {
      "type": "string",
      "readOnly": true
    },
    "num_routing_engines": {
      "type": "integer",
      "description": "routing-engine count",
      "contentEncoding": "int32",
      "examples": [
        1
      ]
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "serial": {
      "type": "string",
      "readOnly": true
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "status": {
      "type": "string",
      "readOnly": true
    },
    "type": {
      "type": "string"
    },
    "vc_mac": {
      "type": "string",
      "readOnly": true
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

`mistapi.api.v1.installer.installer.updateInstallerVirtualChassisMember()`

## Usage Context

Use this endpoint to update the virtual chassis configuration, such as adding or removing member switches. Common use cases:

- Adding a new member switch to an existing VC stack
- Modifying VC member roles or priority settings
- Removing a failed member from the VC configuration

## Gotchas

- The `{fpc0_mac}` must be the MAC of the current master switch
- Changes to VC configuration may cause a brief disruption as members re-negotiate roles
- Member switches must be physically connected and powered on

## Related Endpoints

- [GET_installer_orgs_org_id_devices_fpc0_mac_vc.md](GET_installer_orgs_org_id_devices_fpc0_mac_vc.md) -- Check VC status before/after updating
- [POST_installer_orgs_org_id_devices_fpc0_mac_vc.md](POST_installer_orgs_org_id_devices_fpc0_mac_vc.md) -- Create a new VC
- [../sites/PUT_sites_site_id_devices_device_id_vc.md](../sites/PUT_sites_site_id_devices_device_id_vc.md) -- Full admin VC update

## MistHelper Notes

Not currently used by MistHelper. MistHelper manages VC through the full admin APIs (Menu **92-94**).
