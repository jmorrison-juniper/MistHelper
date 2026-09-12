# listSiteMxEdgesStats

> listSiteMxEdgesStats

## HTTP

`GET /api/v1/sites/{site_id}/stats/mxedges`

## Description

Get List of Site MxEdges Stats

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
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

List of MxEdge Stats

```json
{
  "type": "array",
  "items": {
    "title": "stats_mxedge",
    "type": "object",
    "properties": {
      "cpu_stat": {
        "type": "object",
        "properties": {
          "cpus": {
            "type": "object",
            "additionalProperties": {
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
            "examples": [
              {
                "cpu0": {
                  "idle": 89,
                  "interrupt": 0,
                  "system": 8,
                  "usage": 10,
                  "user": 1
                },
                "cpu1": {
                  "idle": 81,
                  "interrupt": 0,
                  "system": 4,
                  "usage": 18,
                  "user": 13
                },
                "cpu2": {
                  "idle": 81,
                  "interrupt": 0,
                  "system": 4,
                  "usage": 18,
                  "user": 13
                },
                "cpu3": {
                  "idle": 2,
                  "interrupt": 0,
                  "system": 50,
                  "usage": 97,
                  "user": 46
                }
              }
            ]
          },
          "idle": {
            "type": "integer",
            "description": "Percentage of Idle, Idle/(Idle + Busy) since last sampling",
            "contentEncoding": "int32",
            "examples": [
              62
            ]
          },
          "interrupt": {
            "type": "integer",
            "description": "Percentage of Interrupt, (Irq + SoftIrq)/(Idle + Busy) since last sampling",
            "contentEncoding": "int32",
            "examples": [
              0
            ]
          },
          "system": {
            "type": "integer",
            "description": "Percentage of System, System/(Idle + Busy) since last sampling",
            "contentEncoding": "int32",
            "examples": [
              17
            ]
          },
          "usage": {
            "type": "integer",
            "description": "Percentage of load, Busy/(Idle + Busy) since last sampling",
            "contentEncoding": "int32",
            "examples": [
              37
            ]
          },
          "user": {
            "type": "integer",
            "description": "Percentage of User, User/(Idle + Busy) since last sampling",
            "contentEncoding": "int32",
            "examples": [
              19
            ]
          }
        },
        "description": "CPU/core stats list"
      },
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "fips_enabled": {
        "type": "boolean",
        "description": "Indicate fips configuration on the device"
      },
      "for_site": {
        "type": "boolean",
        "examples": [
          false
        ]
      },
      "fwupdate": {
        "title": "fwupdate_stat",
        "type": "object",
        "properties": {
          "progress": {
            "maximum": 100.0,
            "minimum": 0.0,
            "type": [
              "integer",
              "null"
            ],
            "contentEncoding": "int32",
            "readOnly": true,
            "examples": [
              10
            ]
          },
          "status": {
            "type": "object",
            "description": "enum: `inprogress`, `failed`, `upgraded`, `success`, `scheduled`, `error`",
            "readOnly": true
          },
          "status_id": {
            "type": [
              "integer",
              "null"
            ],
            "contentEncoding": "int32",
            "readOnly": true,
            "examples": [
              5
            ]
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          },
          "will_retry": {
            "type": [
              "boolean",
              "null"
            ],
            "readOnly": true,
            "examples": [
              false
            ]
          }
        }
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
      "idrac_version": {
        "type": "string",
        "description": "IDRAC version of the mist edge device",
        "examples": [
          "7.00.00.00"
        ]
      },
      "inactive_vlan_strs": {
        "type": "object",
        "properties": {
          "l2tp": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Inactive L2TP VLANs. Entries can be individual VLANs or ranges."
          },
          "wired": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Inactive wired VLANs. Entries can be individual VLANs or ranges.",
            "examples": [
              [
                "100",
                "102-106"
              ]
            ]
          }
        },
        "description": "Inactive wired/L2TP VLANs. Entries can be individual VLANs or ranges."
      },
      "ip_stat": {
        "type": "object",
        "properties": {
          "ip": {
            "type": "string",
            "examples": [
              "192.168.1.244"
            ]
          },
          "ip6": {
            "type": "string",
            "examples": [
              "fd4e:c615:b27d:5555::45"
            ]
          },
          "ips": {
            "type": "object",
            "additionalProperties": {
              "type": "string"
            },
            "description": "Property key is the interface name. IPs for each net interface",
            "examples": [
              {
                "ens18": "92.168.1.244/24,fd4e:c615:b27d:5555::45/128,fd4e:c615:b27d:5555:20c:29ff:fe44:af25/64,fe80::104c:ffff:fee0:caf8/64"
              }
            ]
          },
          "macs": {
            "type": "object",
            "additionalProperties": {
              "type": "string"
            },
            "description": "Property key is the interface name. MAC for each net interface",
            "examples": [
              {
                "ens18": "e4434b217044"
              }
            ]
          },
          "netmask": {
            "type": "string",
            "examples": [
              "255.255.255.0"
            ]
          },
          "netmask6": {
            "type": "string",
            "examples": [
              "/128"
            ]
          }
        },
        "description": "IP stats"
      },
      "lag_stat": {
        "type": "object",
        "additionalProperties": {
          "title": "stats_mxedge_lag_stat",
          "type": "object",
          "properties": {
            "active_ports": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": "List of ports active on the LAG defined by the LACP"
            }
          }
        },
        "description": "Stat for LAG (Link Aggregation Group). Property key is the LAG name",
        "examples": [
          {
            "lacp0": {
              "active_ports": [
                "port0",
                "port1"
              ]
            }
          }
        ]
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
      "mac": {
        "type": "string",
        "examples": [
          "020000a80cb4"
        ]
      },
      "magic": {
        "type": "string"
      },
      "memory_stat": {
        "type": "object",
        "properties": {
          "active": {
            "type": "integer",
            "description": "The amount of memory, in kilobytes, that has been used more recently and is usually not reclaimed unless absolutely necessary.",
            "contentEncoding": "int32",
            "examples": [
              394936320
            ]
          },
          "available": {
            "type": "integer",
            "description": "An estimate of how much memory is available for starting new applications, without swapping.",
            "contentEncoding": "int64",
            "examples": [
              4699291648
            ]
          },
          "buffers": {
            "type": "integer",
            "description": "The amount, in kilobytes, of temporary storage for raw disk blocks.",
            "contentEncoding": "int32",
            "examples": [
              107646976
            ]
          },
          "cached": {
            "type": "integer",
            "description": "The amount of physical RAM, in kilobytes, used as cache memory.",
            "contentEncoding": "int32",
            "examples": [
              478060544
            ]
          },
          "free": {
            "type": "integer",
            "description": "The amount of physical RAM, in kilobytes, left unused by the system",
            "contentEncoding": "int64",
            "examples": [
              4330659840
            ]
          },
          "inactive": {
            "type": "integer",
            "description": "The amount of memory, in kilobytes, that has been used less recently and is more eligible to be reclaimed for other purposes.",
            "contentEncoding": "int32",
            "examples": [
              211980288
            ]
          },
          "swap_cached": {
            "type": "integer",
            "description": "The amount of memory, in kilobytes, that has once been moved into swap, then back into the main memory, but still also remains in the swapfile.",
            "contentEncoding": "int32",
            "examples": [
              0
            ]
          },
          "swap_free": {
            "type": "integer",
            "description": "The total amount of swap free, in kilobytes.",
            "contentEncoding": "int32",
            "examples": [
              1022357504
            ]
          },
          "swap_total": {
            "type": "integer",
            "description": "The total amount of swap available, in kilobytes.",
            "contentEncoding": "int32",
            "examples": [
              1022357504
            ]
          },
          "total": {
            "type": "integer",
            "description": "Total amount of usable RAM, in kilobytes, which is physical RAM minus a number of reserved bits and the kernel binary code",
            "contentEncoding": "int64",
            "examples": [
              8365957120
            ]
          },
          "usage": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              48
            ]
          }
        },
        "description": "Memory usage"
      },
      "model": {
        "type": "string",
        "examples": [
          "ME-VM"
        ]
      },
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "mxagent_registered": {
        "type": "boolean",
        "examples": [
          true
        ]
      },
      "mxcluster_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "examples": [
          "678bc339-7635-4556-bbc0-e77ad493ef8b"
        ]
      },
      "name": {
        "type": "string",
        "description": "The name of the tunnel",
        "examples": [
          "me-vm-1"
        ]
      },
      "num_tunnels": {
        "type": "integer",
        "contentEncoding": "int32",
        "examples": [
          0
        ]
      },
      "oob_ip_config": {
        "type": "object",
        "properties": {
          "autoconf6": {
            "type": "boolean",
            "default": true
          },
          "dhcp6": {
            "type": "boolean",
            "default": true
          },
          "dns": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "IPv4 ignored if `type`!=`static`, IPv6 ignored if `type6`!=`static`",
            "default": [
              "8.8.8.8",
              "8.8.4.4",
              "2001:4860:4860::8888",
              "2001:4860:4860::8844"
            ],
            "examples": [
              [
                "8.8.8.8",
                "4.4.4.4",
                "2001:4860:4860::8888",
                "2001:4860:4860::8844"
              ]
            ]
          },
          "gateway": {
            "type": "string",
            "description": "If `type`=`static`",
            "examples": [
              "10.2.1.254"
            ]
          },
          "gateway6": {
            "type": "string",
            "examples": [
              "2601:1700:43c0:dc0::1"
            ]
          },
          "ip": {
            "type": "string",
            "description": "If `type`=`static`",
            "examples": [
              "10.2.1.2"
            ]
          },
          "ip6": {
            "type": "string",
            "examples": [
              "2601:1700:43c0:dc0:20c:29ff:fea7:93bc"
            ]
          },
          "netmask": {
            "type": "string",
            "description": "If `type`=`static`",
            "examples": [
              "255.255.255.0"
            ]
          },
          "netmask6": {
            "type": "string",
            "examples": [
              "/64"
            ]
          },
          "type": {
            "type": "string",
            "description": "enum: `dhcp`, `static`"
          },
          "type6": {
            "type": "string",
            "description": "enum: `dhcp`, `static`"
          }
        },
        "description": "IPconfiguration of the Mist Edge out-of_band management interface"
      },
      "oob_ip_stat": {
        "title": "stats_mxedge_oob_ip_stat",
        "type": "object",
        "properties": {
          "dns": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          },
          "gateway": {
            "type": "string"
          },
          "gateway6": {
            "type": "string"
          },
          "ip": {
            "type": "string"
          },
          "ip6": {
            "type": "string"
          },
          "netmask": {
            "type": "string"
          },
          "netmask6": {
            "type": "string"
          },
          "type": {
            "type": "string",
            "description": "enum: `dhcp`, `disabled`, `static`"
          },
          "type8": {
            "type": "string",
            "description": "enum: `autoconf`, `dhcp`, `disabled`, `static`"
          }
        }
      },
      "org_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
        ]
      },
      "port_stat": {
        "type": "object",
        "additionalProperties": {
          "title": "stats_mxedge_port_stat",
          "type": "object",
          "properties": {
            "full_duplex": {
              "type": "boolean"
            },
            "lacp": {
              "title": "stats_mxedge_port_stat_lacp",
              "type": "object",
              "properties": {
                "mux_state": {
                  "type": "string"
                },
                "rx_lacpdu": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "rx_state": {
                  "type": "string"
                },
                "tx_lacpdu": {
                  "type": "integer",
                  "contentEncoding": "int32"
                }
              }
            },
            "lldp_stats": {
              "title": "stats_mxedge_port_stat_lldp_stats",
              "type": "object",
              "properties": {
                "chassis_id": {
                  "type": "string"
                },
                "mgmt_addr": {
                  "type": "string"
                },
                "port_desc": {
                  "type": "string"
                },
                "port_id": {
                  "type": "string"
                },
                "system_desc": {
                  "type": "string"
                },
                "system_name": {
                  "type": "string"
                }
              }
            },
            "mac": {
              "type": "string"
            },
            "rx_bytes": {
              "type": [
                "integer",
                "null"
              ],
              "description": "Amount of traffic received since connection",
              "contentEncoding": "int64",
              "readOnly": true,
              "examples": [
                8515104416
              ]
            },
            "rx_errors": {
              "type": "integer",
              "contentEncoding": "int32"
            },
            "rx_pkts": {
              "type": [
                "integer",
                "null"
              ],
              "description": "Amount of packets received since connection",
              "contentEncoding": "int64",
              "readOnly": true,
              "examples": [
                57770567
              ]
            },
            "sfp": {
              "title": "stats_mxedge_port_stat_sfp",
              "type": "object",
              "properties": {
                "codes": {
                  "type": "string"
                },
                "mbps": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "part_no": {
                  "type": "string"
                },
                "serial_no": {
                  "type": "string"
                },
                "type": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "vendor": {
                  "type": "string"
                }
              }
            },
            "speed": {
              "type": "integer",
              "contentEncoding": "int32"
            },
            "state": {
              "type": "string"
            },
            "tx_bytes": {
              "type": [
                "integer",
                "null"
              ],
              "description": "Amount of traffic sent since connection",
              "contentEncoding": "int64",
              "readOnly": true,
              "examples": [
                211217389682
              ]
            },
            "tx_errors": {
              "type": "integer",
              "contentEncoding": "int32"
            },
            "tx_pkts": {
              "type": [
                "integer",
                "null"
              ],
              "description": "Amount of packets sent since connection",
              "contentEncoding": "int64",
              "readOnly": true,
              "examples": [
                812204062
              ]
            },
            "up": {
              "type": "boolean"
            }
          }
        },
        "examples": [
          {
            "port0": {
              "full_duplex": true,
              "mac": "9e294e49091d",
              "rx_bytes": 646898375700,
              "rx_errors": 0,
              "rx_pkts": 8784449574,
              "speed": 10000,
              "state": "forwarding",
              "tx_bytes": 647200748038,
              "tx_errors": 0,
              "tx_pkts": 8788647466,
              "up": true
            },
            "port1": {
              "full_duplex": true,
              "mac": "a270fe53437e",
              "rx_bytes": 647200437652,
              "rx_errors": 0,
              "rx_pkts": 8788644886,
              "speed": 10000,
              "state": "forwarding",
              "tx_bytes": 646898681650,
              "tx_errors": 0,
              "tx_pkts": 8784452092,
              "up": true
            }
          }
        ]
      },
      "serial": {
        "type": [
          "string",
          "null"
        ]
      },
      "service_stat": {
        "type": "object",
        "additionalProperties": {
          "title": "stats_mxedge_service_stat",
          "type": "object",
          "properties": {
            "ext_ip": {
              "type": "string",
              "description": "External IP from ep-terminator\u2019s point of view. valid only for service having its own cloud connection"
            },
            "last_seen": {
              "type": "number",
              "description": "Timestamp when the last stats is seen (cloud unix time, in second). valid only for service having its own stats or whole system (last among last_seen of all services)"
            },
            "package_state": {
              "type": "string",
              "description": "Package/service installation state."
            },
            "package_version": {
              "type": "string",
              "description": "Package/service installation state."
            },
            "running_state": {
              "type": "string",
              "description": "Service running state."
            },
            "uptime": {
              "type": "integer",
              "description": "Service uptime.",
              "contentEncoding": "int32"
            }
          }
        },
        "description": "Stat for each services",
        "examples": [
          {
            "mxagent": {
              "ext_ip": "99.0.86.164",
              "last_seen": 1633721215,
              "package_state": "Installed",
              "package_version": "3.1.1037-1",
              "running_state": "Running",
              "uptime": 21240
            },
            "tunterm": {
              "ext_ip": "99.0.86.164",
              "last_seen": 1633721203,
              "package_state": "Installed",
              "package_version": "0.1.2449+deb10",
              "running_state": "Running",
              "uptime": 76261
            }
          }
        ]
      },
      "services": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "",
        "examples": [
          [
            "tunterm"
          ]
        ]
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
        "examples": [
          "connected"
        ]
      },
      "tunterm_ip_config": {
        "title": "stats_mxedge_tunterm_ip_config",
        "type": "object",
        "properties": {
          "gateway": {
            "type": "string",
            "examples": [
              "192.168.11.1"
            ]
          },
          "ip": {
            "type": "string",
            "examples": [
              "192.168.11.91"
            ]
          },
          "netmask": {
            "type": "string",
            "examples": [
              "255.255.255.0"
            ]
          }
        }
      },
      "tunterm_port_config": {
        "title": "stats_mxedge_tunterm_port_config",
        "type": "object",
        "properties": {
          "downstream_ports": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "examples": [
              [
                "0",
                "1"
              ]
            ]
          },
          "separate_upstream_downstream": {
            "type": "boolean",
            "examples": [
              false
            ]
          },
          "upstream_ports": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "",
            "examples": [
              [
                "0",
                "1"
              ]
            ]
          }
        }
      },
      "tunterm_registered": {
        "type": "boolean",
        "examples": [
          true
        ]
      },
      "tunterm_stat": {
        "title": "stats_mxedge_tunterm_stat",
        "type": "object",
        "properties": {
          "monitoring_failed": {
            "type": "boolean",
            "examples": [
              false
            ]
          }
        }
      },
      "uptime": {
        "type": "integer",
        "contentEncoding": "int32",
        "examples": [
          76281
        ]
      },
      "virtualization_type": {
        "type": "string",
        "description": "Virtualization environment",
        "examples": [
          "KVM"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "cpu_stat": {
          "cpus": {
            "cpu0": {
              "idle": 89,
              "interrupt": 0,
              "system": 8,
              "usage": 10,
              "user": 1
            },
            "cpu1": {
              "idle": 81,
              "interrupt": 0,
              "system": 4,
              "usage": 18,
              "user": 13
            },
            "cpu2": {
              "idle": 81,
              "interrupt": 0,
              "system": 4,
              "usage": 18,
              "user": 13
            },
            "cpu3": {
              "idle": 2,
              "interrupt": 0,
              "system": 50,
              "usage": 97,
              "user": 46
            }
          },
          "idle": 62,
          "interrupt": 0,
          "system": 17,
          "usage": 37,
          "user": 19
        },
        "created_time": 1632684398,
        "for_site": false,
        "id": "00000000-0000-0000-1000-020000a80cb4",
        "ip_stat": {
          "ip": "192.168.1.244",
          "ips": {
            "ens18": "192.168.1.244/24,fe80::104c:ffff:fee0:caf8/64"
          },
          "macs": {
            "ens18": "e4434b217044"
          }
        },
        "lag_stat": {
          "lacp0": {
            "active_ports": [
              "port0",
              "port1"
            ]
          }
        },
        "last_seen": 1633721215,
        "mac": "020000a80cb4",
        "memory_stat": {
          "active": 394936320,
          "available": 4699291648,
          "buffers": 107646976,
          "cached": 478060544,
          "free": 4330659840,
          "inactive": 211980288,
          "swap_cached": 0,
          "swap_free": 1022357504,
          "swap_total": 1022357504,
          "total": 8365957120,
          "usage": 48
        },
        "model": "ME-VM",
        "modified_time": 1633643629,
        "mxagent_registered": true,
        "mxcluster_id": "678bc339-7635-4556-bbc0-e77ad493ef8b",
        "name": "me-vm-1",
        "num_tunnels": 0,
        "oob_ip_config": {
          "dns": [
            "8.8.8.8",
            "1.1.1.1"
          ],
          "gateway": "10.0.0.1",
          "ip": "10.0.0.10",
          "netmask": "255.255.255.0",
          "type": "static"
        },
        "org_id": "11b08247-b1ee-4152-9b25-312b323ce480",
        "port_stat": {
          "port0": {
            "full_duplex": true,
            "mac": "9e294e49091d",
            "rx_bytes": 646898375700,
            "rx_errors": 0,
            "rx_pkts": 8784449574,
            "speed": 10000,
            "state": "forwarding",
            "tx_bytes": 647200748038,
            "tx_errors": 0,
            "tx_pkts": 8788647466,
            "up": true
          },
          "port1": {
            "full_duplex": true,
            "mac": "a270fe53437e",
            "rx_bytes": 647200437652,
            "rx_errors": 0,
            "rx_pkts": 8788644886,
            "speed": 10000,
            "state": "forwarding",
            "tx_bytes": 646898681650,
            "tx_errors": 0,
            "tx_pkts": 8784452092,
            "up": true
          }
        },
        "serial": "string",
        "service_stat": {
          "mxagent": {
            "ext_ip": "99.0.86.164",
            "last_seen": 1633721215,
            "package_state": "Installed",
            "package_version": "3.1.1037-1",
            "running_state": "Running",
            "uptime": 21240
          },
          "tunterm": {
            "ext_ip": "99.0.86.164",
            "last_seen": 1633721203,
            "package_state": "Installed",
            "package_version": "0.1.2449+deb10",
            "running_state": "Running",
            "uptime": 76261
          }
        },
        "services": [
          "tunterm"
        ],
        "site_id": "00000000-0000-0000-0000-000000000000",
        "status": "connected",
        "tunterm_ip_config": {
          "gateway": "192.168.11.1",
          "ip": "192.168.11.91",
          "netmask": "255.255.255.0"
        },
        "tunterm_port_config": {
          "downstream_ports": [
            "0",
            "1"
          ],
          "separate_upstream_downstream": false,
          "upstream_ports": [
            "0",
            "1"
          ]
        },
        "tunterm_registered": true,
        "tunterm_stat": {
          "monitoring_failed": false
        },
        "uptime": 76281,
        "virtualization_type": "KVM"
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.stats_-_mxedges.listSiteMxEdgesStats()`

## Usage Context

Retrieves statistics for all Mist Edge appliances at a site.

## Gotchas

- Only returns data for sites with Mist Edge deployed.

## Related Endpoints

- [GET_sites_site_id_stats_mxedges_mxedge_id.md](GET_sites_site_id_stats_mxedges_mxedge_id.md) — Specific Mist Edge stats
- [GET_sites_site_id_mxedges.md](GET_sites_site_id_mxedges.md) — Mist Edge config

## MistHelper Notes

Not currently used by MistHelper directly.
