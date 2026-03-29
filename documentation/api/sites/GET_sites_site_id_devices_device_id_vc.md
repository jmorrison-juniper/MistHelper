# getSiteDeviceVirtualChassis

> getSiteDeviceVirtualChassis

## HTTP

`GET /api/v1/sites/{site_id}/devices/{device_id}/vc`

## Description

Get VC Status

The API returns a combined view of the VC status which includes topology and stats_

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| device_id | string | Yes |  |

## Request Body

None.

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

`mistapi.api.v1.sites.devices_-_wired_-_virtual_chassis.getSiteDeviceVirtualChassis()`

## Usage Context

Retrieves the Virtual Chassis (VC) configuration and member details for a switch device. Shows member roles, priorities, and status.

## Gotchas

- Only applicable to EX series switches configured as VC.
- Returns empty or error for non-VC devices.

## Related Endpoints

- [POST_sites_site_id_devices_device_id_vc.md](POST_sites_site_id_devices_device_id_vc.md) — Create/update VC config
- [DELETE_sites_site_id_devices_device_id_vc.md](DELETE_sites_site_id_devices_device_id_vc.md) — Delete VC config
- [PUT_sites_site_id_devices_device_id_vc.md](PUT_sites_site_id_devices_device_id_vc.md) — Update VC members

## MistHelper Notes

Used by Menu **24** and Menu **33** via `getSiteDeviceVirtualChassis` for VC inventory and management.
