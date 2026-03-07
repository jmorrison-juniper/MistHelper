# listSiteDevicesStats

> listSiteDevicesStats

## HTTP

`GET /api/v1/sites/{site_id}/stats/devices`

## Description

Get List of Site Devices Stats

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
| type | string | No | ap |  |  |
| status | string | No |  |  |  |
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "array",
  "items": {
    "oneOf": [
      {
        "title": "stats_ap",
        "required": [
          "type"
        ],
        "type": "object",
        "properties": {
          "antenna_select": {
            "type": "string",
            "description": "Antenna Mode for AP which supports selectable antennas. enum: `\"\"` (default), `external`, `internal`"
          },
          "auto_placement": {
            "title": "stats_ap_auto_placement",
            "type": "object",
            "properties": {
              "info": {
                "type": "object",
                "properties": {
                  "cluster_number": {
                    "type": "integer",
                    "description": "All APs sharing a given cluster number can be placed relative to each other",
                    "contentEncoding": "int32",
                    "examples": [
                      0
                    ]
                  },
                  "orientation_stats": {
                    "type": "integer",
                    "description": "The orientation of an AP",
                    "contentEncoding": "int32",
                    "examples": [
                      0
                    ]
                  },
                  "probability_surface": {
                    "type": "object",
                    "properties": {
                      "radius": {
                        "type": "number",
                        "description": "The radius representing placement uncertainty, measured in pixels",
                        "examples": [
                          2.1
                        ]
                      },
                      "radius_m": {
                        "type": "number",
                        "description": "The radius representing placement uncertainty, measured in meters"
                      },
                      "x": {
                        "type": "number",
                        "description": "Y-coordinate of the potential placement\u2019s center, measured in pixels",
                        "examples": [
                          17
                        ]
                      }
                    },
                    "description": "Coordinates representing a circle where the AP is most likely exists in the event of an inaccurate placement result"
                  }
                },
                "description": "Additional information about auto placements AP data"
              },
              "recommended_anchor": {
                "type": "boolean",
                "description": "Flag to represent if AP is recommended as an anchor by auto placement service"
              },
              "status": {
                "type": "string",
                "description": "Basic Placement Status",
                "examples": [
                  "localized"
                ]
              },
              "status_detail": {
                "type": "string",
                "description": "Additional info about placement status",
                "examples": [
                  "localized"
                ]
              },
              "x": {
                "type": "number",
                "description": "X Autoplaced Position in pixels",
                "examples": [
                  53.5
                ]
              },
              "x_m": {
                "type": "number",
                "description": "X Autoplaced Position in meters",
                "examples": [
                  5.35
                ]
              },
              "y": {
                "type": "number",
                "description": "Y Autoplaced Position in pixels",
                "examples": [
                  173.1
                ]
              },
              "y_m": {
                "type": "number",
                "description": "X Autoplaced Position in meters",
                "examples": [
                  17.31
                ]
              }
            }
          },
          "auto_upgrade_stat": {
            "title": "stats_ap_auto_upgrade",
            "type": "object",
            "properties": {
              "lastcheck": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int64",
                "readOnly": true,
                "examples": [
                  1720594762
                ]
              }
            }
          },
          "ble_stat": {
            "title": "stats_ap_ble",
            "type": "object",
            "properties": {
              "beacon_enabled": {
                "type": [
                  "boolean",
                  "null"
                ],
                "readOnly": true
              },
              "beacon_rate": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int32",
                "readOnly": true,
                "examples": [
                  3
                ]
              },
              "eddystone_uid_enabled": {
                "type": [
                  "boolean",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  false
                ]
              },
              "eddystone_uid_freq_msec": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int32",
                "readOnly": true,
                "examples": [
                  2000
                ]
              },
              "eddystone_uid_instance": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "5c5b35000001"
                ]
              },
              "eddystone_uid_namespace": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "2818e3868dec25629ede"
                ]
              },
              "eddystone_url_enabled": {
                "type": [
                  "boolean",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  true
                ]
              },
              "eddystone_url_freq_msec": {
                "type": [
                  "integer",
                  "null"
                ],
                "description": "Frequency (msec) of data emit by Eddystone-UID beacon",
                "contentEncoding": "int32",
                "readOnly": true,
                "examples": [
                  100
                ]
              },
              "eddystone_url_url": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "https://www.abc.com"
                ]
              },
              "ibeacon_enabled": {
                "type": [
                  "boolean",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  true
                ]
              },
              "ibeacon_freq_msec": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int32",
                "readOnly": true,
                "examples": [
                  2000
                ]
              },
              "ibeacon_major": {
                "maximum": 65535.0,
                "minimum": 1.0,
                "type": [
                  "integer",
                  "null"
                ],
                "description": "Major number for iBeacon",
                "contentEncoding": "int32",
                "examples": [
                  1234
                ]
              },
              "ibeacon_minor": {
                "maximum": 65535.0,
                "minimum": 1.0,
                "type": [
                  "integer",
                  "null"
                ],
                "description": "Minor number for iBeacon",
                "contentEncoding": "int32",
                "examples": [
                  1234
                ]
              },
              "ibeacon_uuid": {
                "type": [
                  "string",
                  "null"
                ],
                "contentEncoding": "uuid",
                "examples": [
                  "f3f17139-704a-f03a-2786-0400279e37c3"
                ]
              },
              "major": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int32",
                "readOnly": true,
                "examples": [
                  12345
                ]
              },
              "minors": {
                "type": "array",
                "items": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "description": ""
              },
              "power": {
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
              "tx_resets": {
                "type": [
                  "integer",
                  "null"
                ],
                "description": "Resets due to tx hung",
                "contentEncoding": "int32",
                "readOnly": true,
                "examples": [
                  0
                ]
              },
              "uuid": {
                "type": [
                  "string",
                  "null"
                ],
                "contentEncoding": "uuid",
                "readOnly": true,
                "examples": [
                  "ada72f8f-1643-e5c6-94db-f2a5636f1a64"
                ]
              }
            }
          },
          "cert_expiry": {
            "type": [
              "number",
              "null"
            ],
            "readOnly": true,
            "examples": [
              1534534392
            ]
          },
          "config_reverted": {
            "type": [
              "boolean",
              "null"
            ],
            "readOnly": true
          },
          "cpu_system": {
            "type": [
              "integer",
              "null"
            ],
            "contentEncoding": "int64",
            "readOnly": true
          },
          "cpu_user": {
            "type": [
              "integer",
              "null"
            ],
            "contentEncoding": "int32",
            "readOnly": true
          },
          "cpu_util": {
            "type": [
              "integer",
              "null"
            ],
            "contentEncoding": "int32",
            "readOnly": true
          },
          "created_time": {
            "type": "number",
            "description": "When the object has been created, in epoch",
            "readOnly": true
          },
          "deviceprofile_id": {
            "type": [
              "string",
              "null"
            ],
            "contentEncoding": "uuid",
            "readOnly": true
          },
          "env_stat": {
            "type": "object",
            "properties": {
              "accel_x": {
                "type": [
                  "number",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  0
                ]
              },
              "accel_y": {
                "type": [
                  "number",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  0.032
                ]
              },
              "accel_z": {
                "type": [
                  "number",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  -1.088
                ]
              },
              "ambient_temp": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int32",
                "readOnly": true,
                "examples": [
                  43
                ]
              },
              "attitude": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int32",
                "readOnly": true,
                "examples": [
                  0
                ]
              },
              "cpu_temp": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int32",
                "readOnly": true,
                "examples": [
                  61
                ]
              },
              "humidity": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int32",
                "readOnly": true,
                "examples": [
                  9
                ]
              },
              "magne_x": {
                "type": [
                  "number",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  0
                ]
              },
              "magne_y": {
                "type": [
                  "number",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  0
                ]
              },
              "magne_z": {
                "type": [
                  "number",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  0
                ]
              },
              "pressure": {
                "type": [
                  "number",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  968
                ]
              },
              "vcore_voltage": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int32",
                "readOnly": true,
                "examples": [
                  0
                ]
              }
            },
            "description": "Device environment, including CPU temperature, Ambient temperature, Humidity, Attitude, Pressure, Accelerometers, Magnetometers and vCore Voltage"
          },
          "esl_stat": {
            "type": "object",
            "readOnly": true
          },
          "evpntopo_id": {
            "type": [
              "string",
              "null"
            ],
            "contentEncoding": "uuid",
            "readOnly": true
          },
          "expiring_certs": {
            "type": "object",
            "additionalProperties": {
              "type": "integer",
              "format": "int32"
            },
            "description": "Map of certificate serial numbers to their expiry timestamps (in epoch) for certificates expiring within 30 days. Property key is the certificate serial number"
          },
          "ext_ip": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true,
            "examples": [
              "73.92.124.103"
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
          "gps_stat": {
            "title": "stats_ap_gps_stat",
            "type": "object",
            "properties": {
              "accuracy": {
                "type": "number",
                "description": "The estimated accuracy or accuracy of the GPS coordinates, measured in meters.",
                "examples": [
                  12.5
                ]
              },
              "altitude": {
                "type": "number",
                "description": "The elevation of the AP above sea level, measured in meters.",
                "examples": [
                  99.939
                ]
              },
              "latitude": {
                "type": "number",
                "description": "The geographic latitude of the AP, measured in degrees.",
                "examples": [
                  37.29548
                ]
              },
              "longitude": {
                "type": "number",
                "description": "The geographic longitude of the AP, measured in degrees.",
                "examples": [
                  -122.03304
                ]
              },
              "src": {
                "type": "string",
                "description": "The origin of the GPS data. enum: `gps`: from this device GPS estimates, `other_ap` from neighboring device GPS estimates. Note: API responses may return `other_aps` which should be treated as `other_ap`"
              },
              "timestamp": {
                "type": "number",
                "description": "Epoch (seconds)",
                "readOnly": true
              }
            }
          },
          "hw_rev": {
            "type": [
              "string",
              "null"
            ],
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
          "inactive_wired_vlans": {
            "type": "array",
            "items": {
              "type": "integer",
              "contentEncoding": "int32"
            },
            "description": ""
          },
          "iot_stat": {
            "type": "object",
            "additionalProperties": {
              "title": "stats_ap_iot_stat_additional_properties",
              "type": "object",
              "properties": {
                "value": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32",
                  "readOnly": true
                }
              }
            },
            "examples": [
              {
                "DI2": {
                  "value": 0
                }
              }
            ]
          },
          "ip": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true,
            "examples": [
              "10.2.9.159"
            ]
          },
          "ip_config": {
            "type": "object",
            "properties": {
              "dns": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "If `type`==`static`",
                "examples": [
                  [
                    "8.8.8.8",
                    "4.4.4.4"
                  ]
                ]
              },
              "dns_suffix": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "Required if `type`==`static`",
                "examples": [
                  [
                    ".mist.local",
                    ".mist.com"
                  ]
                ]
              },
              "gateway": {
                "type": "string",
                "description": "Required if `type`==`static`",
                "examples": [
                  "10.2.1.254"
                ]
              },
              "gateway6": {
                "type": "string",
                "examples": [
                  "2607:f8b0:4005:808::1"
                ]
              },
              "ip": {
                "type": "string",
                "description": "Required if `type`==`static`",
                "examples": [
                  "10.2.1.1"
                ]
              },
              "ip6": {
                "type": "string",
                "examples": [
                  "2607:f8b0:4005:808::2004"
                ]
              },
              "mtu": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  0
                ]
              },
              "netmask": {
                "type": "string",
                "description": "Required if `type`==`static`",
                "examples": [
                  "255.255.255.0"
                ]
              },
              "netmask6": {
                "type": "string",
                "examples": [
                  "/32"
                ]
              },
              "type": {
                "type": "string",
                "description": "enum: `dhcp`, `static`"
              },
              "type6": {
                "type": "string",
                "description": "enum: `autoconf`, `dhcp`, `disabled`, `static`"
              },
              "vlan_id": {
                "type": "integer",
                "description": "Management VLAN id, default is 1 (untagged)",
                "contentEncoding": "int32",
                "default": 1,
                "examples": [
                  1
                ]
              }
            },
            "description": "IP AP settings"
          },
          "ip_stat": {
            "title": "ip_stat",
            "type": "object",
            "properties": {
              "dhcp_server": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "192.168.95.1"
                ]
              },
              "dns": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "dns_suffix": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "gateway": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true
              },
              "gateway6": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "fdad:b0bc:f29e::1"
                ]
              },
              "ip": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "10.3.3.1"
                ]
              },
              "ip6": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "fdad:b0bc:f29e::3d16"
                ]
              },
              "ips": {
                "type": "object",
                "additionalProperties": {
                  "type": "string",
                  "nullable": true
                }
              },
              "netmask": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "255.255.255.0"
                ]
              },
              "netmask6": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "/64"
                ]
              }
            }
          },
          "l2tp_stat": {
            "type": "object",
            "additionalProperties": {
              "title": "stats_ap_l2tp_stat",
              "type": "object",
              "properties": {
                "sessions": {
                  "type": "array",
                  "items": {
                    "title": "stats_ap_l2tp_stat_session",
                    "type": "object",
                    "properties": {
                      "local_sid": {
                        "type": [
                          "integer",
                          "null"
                        ],
                        "description": "Remote sessions id (dynamically unless Tunnel is said to be static)",
                        "contentEncoding": "int32",
                        "readOnly": true,
                        "examples": [
                          31
                        ]
                      },
                      "remote_id": {
                        "type": [
                          "string",
                          "null"
                        ],
                        "description": "WxlanTunnel Remote ID (user-configured)",
                        "readOnly": true,
                        "examples": [
                          "vpn1"
                        ]
                      },
                      "remote_sid": {
                        "type": [
                          "integer",
                          "null"
                        ],
                        "description": "Remote sessions id (dynamically unless Tunnel is said to be static)",
                        "contentEncoding": "int32",
                        "readOnly": true,
                        "examples": [
                          13
                        ]
                      },
                      "state": {
                        "type": "string",
                        "description": "enum: `established`, `established_with_session`, `idle`, `wait-ctrl-conn`, `wait-ctrl-reply`"
                      }
                    }
                  },
                  "description": "List of sessions"
                },
                "state": {
                  "type": "string",
                  "description": "enum: `established`, `established_with_session`, `idle`, `wait-ctrl-conn`, `wait-ctrl-reply`"
                },
                "uptime": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "description": "Uptime",
                  "contentEncoding": "int32",
                  "readOnly": true,
                  "examples": [
                    135
                  ]
                },
                "wxtunnel_id": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "description": "WxlanTunnel ID",
                  "contentEncoding": "uuid",
                  "readOnly": true,
                  "examples": [
                    "7dae216d-7c98-a51b-e068-dd7d477b7216"
                  ]
                }
              }
            },
            "description": "L2TP tunnel status (key is the wxtunnel_id)"
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
          "last_trouble": {
            "type": "object",
            "properties": {
              "code": {
                "type": "string",
                "description": "Code definitions list at [List Ap Led Definition]($e/Constants%20Definitions/listApLedDefinition)",
                "examples": [
                  "03"
                ]
              },
              "timestamp": {
                "type": "number",
                "description": "Epoch (seconds)",
                "readOnly": true
              }
            },
            "description": "Last trouble code of switch"
          },
          "led": {
            "type": "object",
            "properties": {
              "brightness": {
                "maximum": 255.0,
                "minimum": 0.0,
                "type": "integer",
                "contentEncoding": "int32",
                "default": 255,
                "examples": [
                  255
                ]
              },
              "enabled": {
                "type": "boolean",
                "default": true
              }
            },
            "description": "LED AP settings"
          },
          "lldp_stat": {
            "type": "object",
            "properties": {
              "chassis_id": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true
              },
              "lldp_med_supported": {
                "type": [
                  "boolean",
                  "null"
                ],
                "description": "Whether it support LLDP-MED",
                "readOnly": true
              },
              "mgmt_addr": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "Management IP address of the switch",
                "readOnly": true
              },
              "mgmt_addrs": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "List of management IP addresses (IPv4 and IPv6)"
              },
              "port_desc": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "Port description, e.g. \u201c2/20\u201d, \u201cPort 2 on Switch0\u201d",
                "readOnly": true,
                "examples": [
                  "2/20"
                ]
              },
              "port_id": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "Port identifier",
                "readOnly": true,
                "examples": [
                  "ge-0/0/4"
                ]
              },
              "power_allocated": {
                "type": [
                  "number",
                  "null"
                ],
                "description": "In mW, power allocated by PSE",
                "readOnly": true
              },
              "power_avail": {
                "type": "integer",
                "description": "In mW, total Power Avail at AP from pwr source",
                "contentEncoding": "int32"
              },
              "power_budget": {
                "type": "integer",
                "description": "In mW, surplus if positive or deficit if negative",
                "contentEncoding": "int32"
              },
              "power_constrained": {
                "type": "boolean",
                "description": "Whether power is insufficient"
              },
              "power_draw": {
                "type": [
                  "number",
                  "null"
                ],
                "description": "In mW, total power needed by PD",
                "readOnly": true
              },
              "power_needed": {
                "type": "integer",
                "description": "In mW, total Power needed incl Peripherals",
                "contentEncoding": "int32"
              },
              "power_opmode": {
                "type": "string",
                "description": "Constrained mode"
              },
              "power_request_count": {
                "type": [
                  "integer",
                  "null"
                ],
                "description": "Number of negotiations, if it keeps increasing, we don\u2019 t have a stable power",
                "contentEncoding": "int32",
                "readOnly": true
              },
              "power_requested": {
                "type": [
                  "number",
                  "null"
                ],
                "description": "In mW, power requested by PD",
                "readOnly": true
              },
              "power_src": {
                "type": "string",
                "description": "Single power source (DC Input / PoE 802.3at / PoE 802.3af / PoE 802.3bt / MULTI-PD / LLDP / ? (unknown))."
              },
              "power_srcs": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "List of management IP addresses (IPv4 and IPv6)"
              },
              "system_desc": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "Description provided by switch",
                "readOnly": true,
                "examples": [
                  "uniper Networks, Inc. ex4300-48t internet router, kernel JUNOS 20.4R3-S7.2, Build date: 2023-04-21 19:47:18 UTC Copyright (c) 1996-2023 Juniper Networks, Inc."
                ]
              },
              "system_name": {
                "type": [
                  "string",
                  "null"
                ],
                "description": "Name of the switch",
                "readOnly": true,
                "examples": [
                  "Core-AE23"
                ]
              }
            },
            "description": "LLDP neighbor information and power negotiations. For backward compatibility, when multiple neighbors exist, only information from the first neighbor is displayed."
          },
          "lldp_stats": {
            "type": "object",
            "additionalProperties": {
              "title": "stats_ap_lldp_stat",
              "type": "object",
              "properties": {
                "chassis_id": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "readOnly": true
                },
                "lldp_med_supported": {
                  "type": [
                    "boolean",
                    "null"
                  ],
                  "description": "Whether it support LLDP-MED",
                  "readOnly": true
                },
                "mgmt_addr": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "description": "Management IP address of the switch",
                  "readOnly": true
                },
                "mgmt_addrs": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": "List of management IP addresses (IPv4 and IPv6)"
                },
                "port_desc": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "description": "Port description, e.g. \u201c2/20\u201d, \u201cPort 2 on Switch0\u201d",
                  "readOnly": true,
                  "examples": [
                    "2/20"
                  ]
                },
                "port_id": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "description": "Port identifier",
                  "readOnly": true,
                  "examples": [
                    "ge-0/0/4"
                  ]
                },
                "power_allocated": {
                  "type": [
                    "number",
                    "null"
                  ],
                  "description": "In mW, power allocated by PSE",
                  "readOnly": true
                },
                "power_avail": {
                  "type": "integer",
                  "description": "In mW, total Power Avail at AP from pwr source",
                  "contentEncoding": "int32"
                },
                "power_budget": {
                  "type": "integer",
                  "description": "In mW, surplus if positive or deficit if negative",
                  "contentEncoding": "int32"
                },
                "power_constrained": {
                  "type": "boolean",
                  "description": "Whether power is insufficient"
                },
                "power_draw": {
                  "type": [
                    "number",
                    "null"
                  ],
                  "description": "In mW, total power needed by PD",
                  "readOnly": true
                },
                "power_needed": {
                  "type": "integer",
                  "description": "In mW, total Power needed incl Peripherals",
                  "contentEncoding": "int32"
                },
                "power_opmode": {
                  "type": "string",
                  "description": "Constrained mode"
                },
                "power_request_count": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "description": "Number of negotiations, if it keeps increasing, we don\u2019 t have a stable power",
                  "contentEncoding": "int32",
                  "readOnly": true
                },
                "power_requested": {
                  "type": [
                    "number",
                    "null"
                  ],
                  "description": "In mW, power requested by PD",
                  "readOnly": true
                },
                "power_src": {
                  "type": "string",
                  "description": "Single power source (DC Input / PoE 802.3at / PoE 802.3af / PoE 802.3bt / MULTI-PD / LLDP / ? (unknown))."
                },
                "power_srcs": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": "List of management IP addresses (IPv4 and IPv6)"
                },
                "system_desc": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "description": "Description provided by switch",
                  "readOnly": true,
                  "examples": [
                    "uniper Networks, Inc. ex4300-48t internet router, kernel JUNOS 20.4R3-S7.2, Build date: 2023-04-21 19:47:18 UTC Copyright (c) 1996-2023 Juniper Networks, Inc."
                  ]
                },
                "system_name": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "description": "Name of the switch",
                  "readOnly": true,
                  "examples": [
                    "Core-AE23"
                  ]
                }
              },
              "description": "LLDP neighbor information and power negotiations. For backward compatibility, when multiple neighbors exist, only information from the first neighbor is displayed."
            },
            "description": "Property key is the port name (e.g. \"eth0\", \"eth1\", ...). Map of ethernet ports to their respective LLDP neighbor information and power negotiations. Only present when multiple neighbors exist."
          },
          "locating": {
            "type": [
              "boolean",
              "null"
            ],
            "readOnly": true,
            "examples": [
              false
            ]
          },
          "locked": {
            "type": [
              "boolean",
              "null"
            ],
            "description": "Whether this AP is considered locked (placement / orientation has been vetted)",
            "readOnly": true,
            "examples": [
              true
            ]
          },
          "mac": {
            "type": [
              "string",
              "null"
            ],
            "description": "Device mac",
            "readOnly": true,
            "examples": [
              "5c5b35000010"
            ]
          },
          "map_id": {
            "type": [
              "string",
              "null"
            ],
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "63eda950-c6da-11e4-a628-60f81dd250cc"
            ]
          },
          "mem_total_kb": {
            "type": [
              "integer",
              "null"
            ],
            "contentEncoding": "int64",
            "readOnly": true
          },
          "mem_used_kb": {
            "type": [
              "integer",
              "null"
            ],
            "contentEncoding": "int64",
            "readOnly": true
          },
          "mesh_downlinks": {
            "type": "object",
            "additionalProperties": {
              "title": "ap_stat_mesh_downlink",
              "type": "object",
              "properties": {
                "band": {
                  "type": "string",
                  "examples": [
                    "5"
                  ]
                },
                "channel": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    36
                  ]
                },
                "idle_time": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    3
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
                "proto": {
                  "type": "string",
                  "examples": [
                    "n"
                  ]
                },
                "rssi": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    -65
                  ]
                },
                "rx_bps": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "description": "Rate of receiving traffic, bits/seconds, last known",
                  "contentEncoding": "int64",
                  "readOnly": true,
                  "examples": [
                    60003
                  ]
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
                "rx_packets": {
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
                "rx_rate": {
                  "type": [
                    "number",
                    "null"
                  ],
                  "description": "RX Rate, Mbps",
                  "readOnly": true
                },
                "rx_retries": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "description": "Amount of rx retries",
                  "contentEncoding": "int32",
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
                "snr": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    31
                  ]
                },
                "tx_bps": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "description": "Rate of transmitting traffic, bits/seconds, last known",
                  "contentEncoding": "int64",
                  "readOnly": true,
                  "examples": [
                    634301
                  ]
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
                "tx_packets": {
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
                "tx_rate": {
                  "type": [
                    "number",
                    "null"
                  ],
                  "description": "TX Rate, Mbps",
                  "readOnly": true
                },
                "tx_retries": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "description": "Amount of tx retries",
                  "contentEncoding": "int32",
                  "readOnly": true
                }
              }
            },
            "description": "Property key is the mesh downlink id (e.g. `00000000-0000-0000-1000-5c5b35000010`)"
          },
          "mesh_uplink": {
            "title": "ap_stat_mesh_uplink",
            "type": "object",
            "properties": {
              "band": {
                "type": "string",
                "examples": [
                  "5"
                ]
              },
              "channel": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  36
                ]
              },
              "idle_time": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  3
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
              "proto": {
                "type": "string",
                "examples": [
                  "n"
                ]
              },
              "rssi": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  -65
                ]
              },
              "rx_bps": {
                "type": [
                  "integer",
                  "null"
                ],
                "description": "Rate of receiving traffic, bits/seconds, last known",
                "contentEncoding": "int64",
                "readOnly": true,
                "examples": [
                  60003
                ]
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
              "rx_packets": {
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
              "rx_rate": {
                "type": [
                  "number",
                  "null"
                ],
                "description": "RX Rate, Mbps",
                "readOnly": true
              },
              "rx_retries": {
                "type": [
                  "integer",
                  "null"
                ],
                "description": "Amount of rx retries",
                "contentEncoding": "int32",
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
              "snr": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  31
                ]
              },
              "tx_bps": {
                "type": [
                  "integer",
                  "null"
                ],
                "description": "Rate of transmitting traffic, bits/seconds, last known",
                "contentEncoding": "int64",
                "readOnly": true,
                "examples": [
                  634301
                ]
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
              "tx_packets": {
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
              "tx_rate": {
                "type": [
                  "number",
                  "null"
                ],
                "description": "TX Rate, Mbps",
                "readOnly": true
              },
              "tx_retries": {
                "type": [
                  "integer",
                  "null"
                ],
                "description": "Amount of tx retries",
                "contentEncoding": "int32",
                "readOnly": true
              },
              "uplink_ap_id": {
                "type": "string",
                "contentEncoding": "uuid",
                "examples": [
                  "00000000-0000-0000-1000-5c5b35000010"
                ]
              }
            }
          },
          "model": {
            "type": [
              "string",
              "null"
            ],
            "description": "Device model",
            "readOnly": true,
            "examples": [
              "AP200"
            ]
          },
          "modified_time": {
            "type": "number",
            "description": "When the object has been modified for the last time, in epoch",
            "readOnly": true
          },
          "mount": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true,
            "examples": [
              "faceup"
            ]
          },
          "name": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true,
            "examples": [
              "conference room"
            ]
          },
          "notes": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "num_clients": {
            "type": [
              "integer",
              "null"
            ],
            "description": "How many wireless clients are currently connected",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "num_wlans": {
            "type": "integer",
            "description": "How many WLANs are applied to the device",
            "contentEncoding": "int32"
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
            "type": [
              "object",
              "null"
            ],
            "additionalProperties": {
              "title": "stats_ap_port_stat",
              "type": "object",
              "properties": {
                "full_duplex": {
                  "type": [
                    "boolean",
                    "null"
                  ],
                  "readOnly": true,
                  "examples": [
                    true
                  ]
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
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32",
                  "readOnly": true,
                  "examples": [
                    0
                  ]
                },
                "rx_peak_bps": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32",
                  "readOnly": true,
                  "examples": [
                    22185
                  ]
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
                "speed": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32",
                  "readOnly": true,
                  "examples": [
                    1000
                  ]
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
                "tx_peak_bps": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "contentEncoding": "int32",
                  "readOnly": true,
                  "examples": [
                    43922
                  ]
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
                  "type": [
                    "boolean",
                    "null"
                  ],
                  "readOnly": true,
                  "examples": [
                    true
                  ]
                }
              }
            },
            "description": "Property key is the port name (e.g. `eth0`)",
            "readOnly": true
          },
          "power_budget": {
            "type": [
              "integer",
              "null"
            ],
            "description": "In mW, surplus if positive or deficit if negative",
            "contentEncoding": "int32",
            "readOnly": true,
            "examples": [
              1000
            ]
          },
          "power_constrained": {
            "type": [
              "boolean",
              "null"
            ],
            "description": "Whether insufficient power",
            "readOnly": true,
            "examples": [
              false
            ]
          },
          "power_opmode": {
            "type": [
              "string",
              "null"
            ],
            "description": "Constrained mode",
            "readOnly": true,
            "examples": [
              "[20] 6GHz(2x2) 5GHz(4x4) 2.4GHz(2x2)."
            ]
          },
          "power_src": {
            "type": [
              "string",
              "null"
            ],
            "description": "DC Input / PoE 802.3at / PoE 802.3af / LLDP / ? (unknown)",
            "readOnly": true,
            "examples": [
              "PoE 802.3af"
            ]
          },
          "radio_config": {
            "title": "stats_ap_radio_config",
            "type": "object",
            "properties": {
              "band_24": {
                "title": "stats_ap_radio_config_band",
                "type": "object",
                "properties": {
                  "allow_rrm_disable": {
                    "type": [
                      "boolean",
                      "null"
                    ],
                    "readOnly": true
                  },
                  "bandwidth": {
                    "type": [
                      "number",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      20
                    ]
                  },
                  "channel": {
                    "type": "integer",
                    "contentEncoding": "int32",
                    "examples": [
                      1
                    ]
                  },
                  "disabled": {
                    "type": [
                      "boolean",
                      "null"
                    ],
                    "readOnly": true
                  },
                  "dynamic_chaining_enabled": {
                    "type": [
                      "boolean",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      false
                    ]
                  },
                  "power": {
                    "type": [
                      "number",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      10
                    ]
                  },
                  "power_max": {
                    "type": [
                      "number",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      10
                    ]
                  },
                  "power_min": {
                    "type": [
                      "number",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      10
                    ]
                  },
                  "rx_chain": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "readOnly": true,
                    "examples": [
                      4
                    ]
                  },
                  "tx_chain": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "readOnly": true,
                    "examples": [
                      4
                    ]
                  }
                }
              },
              "band_24_usage": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "5"
                ]
              },
              "band_5": {
                "title": "stats_ap_radio_config_band",
                "type": "object",
                "properties": {
                  "allow_rrm_disable": {
                    "type": [
                      "boolean",
                      "null"
                    ],
                    "readOnly": true
                  },
                  "bandwidth": {
                    "type": [
                      "number",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      20
                    ]
                  },
                  "channel": {
                    "type": "integer",
                    "contentEncoding": "int32",
                    "examples": [
                      1
                    ]
                  },
                  "disabled": {
                    "type": [
                      "boolean",
                      "null"
                    ],
                    "readOnly": true
                  },
                  "dynamic_chaining_enabled": {
                    "type": [
                      "boolean",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      false
                    ]
                  },
                  "power": {
                    "type": [
                      "number",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      10
                    ]
                  },
                  "power_max": {
                    "type": [
                      "number",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      10
                    ]
                  },
                  "power_min": {
                    "type": [
                      "number",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      10
                    ]
                  },
                  "rx_chain": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "readOnly": true,
                    "examples": [
                      4
                    ]
                  },
                  "tx_chain": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "readOnly": true,
                    "examples": [
                      4
                    ]
                  }
                }
              },
              "band_6": {
                "title": "stats_ap_radio_config_band",
                "type": "object",
                "properties": {
                  "allow_rrm_disable": {
                    "type": [
                      "boolean",
                      "null"
                    ],
                    "readOnly": true
                  },
                  "bandwidth": {
                    "type": [
                      "number",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      20
                    ]
                  },
                  "channel": {
                    "type": "integer",
                    "contentEncoding": "int32",
                    "examples": [
                      1
                    ]
                  },
                  "disabled": {
                    "type": [
                      "boolean",
                      "null"
                    ],
                    "readOnly": true
                  },
                  "dynamic_chaining_enabled": {
                    "type": [
                      "boolean",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      false
                    ]
                  },
                  "power": {
                    "type": [
                      "number",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      10
                    ]
                  },
                  "power_max": {
                    "type": [
                      "number",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      10
                    ]
                  },
                  "power_min": {
                    "type": [
                      "number",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      10
                    ]
                  },
                  "rx_chain": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "readOnly": true,
                    "examples": [
                      4
                    ]
                  },
                  "tx_chain": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "readOnly": true,
                    "examples": [
                      4
                    ]
                  }
                }
              },
              "scanning_enabled": {
                "type": "boolean"
              }
            }
          },
          "radio_stat": {
            "title": "stats_ap_radio_stat",
            "type": "object",
            "properties": {
              "band_24": {
                "type": "object",
                "properties": {
                  "bandwidth": {
                    "type": "integer",
                    "description": "channel width for the band.enum: `0`(disabled, response only), `20`, `40`, `80` (only applicable for band_5 and band_6), `160` (only for band_6)"
                  },
                  "channel": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Current channel the radio is running on",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "dynamic_chaining_enabled": {
                    "type": [
                      "boolean",
                      "null"
                    ],
                    "description": "Use dynamic chaining for downlink",
                    "readOnly": true
                  },
                  "mac": {
                    "type": [
                      "string",
                      "null"
                    ],
                    "description": "Radio (base) mac, it can have 16 bssids (e.g. 5c5b350001a0-5c5b350001af)",
                    "readOnly": true
                  },
                  "noise_floor": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "readOnly": true,
                    "examples": [
                      -90
                    ]
                  },
                  "num_clients": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "num_wlans": {
                    "type": "integer",
                    "description": "How many WLANs are applied to the radio",
                    "contentEncoding": "int32"
                  },
                  "power": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Transmit power (in dBm)",
                    "contentEncoding": "int32",
                    "readOnly": true
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
                  "usage": {
                    "type": [
                      "string",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      "24"
                    ]
                  },
                  "util_all": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "All utilization in percentage",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_non_wifi": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Reception of \"No Packets\" utilization in percentage, received frames with invalid PLCPs and CRS glitches as noise",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_rx_in_bss": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Reception of \"In BSS\" utilization in percentage, only frames that are received from AP/STAs within the BSS",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_rx_other_bss": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Reception of \"Other BSS\" utilization in percentage, all frames received from AP/STAs that are outside the BSS",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_tx": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Transmission utilization in percentage",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_undecodable_wifi": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Reception of \"UnDecodable Wifi\" utilization in percentage, only Preamble, PLCP header is decoded, Rest is undecodable in this radio",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_unknown_wifi": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Reception of \"No Category\" utilization in percentage, all 802.11 frames that are corrupted at the receiver",
                    "contentEncoding": "int32",
                    "readOnly": true
                  }
                },
                "description": "Radio stat"
              },
              "band_5": {
                "type": "object",
                "properties": {
                  "bandwidth": {
                    "type": "integer",
                    "description": "channel width for the band.enum: `0`(disabled, response only), `20`, `40`, `80` (only applicable for band_5 and band_6), `160` (only for band_6)"
                  },
                  "channel": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Current channel the radio is running on",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "dynamic_chaining_enabled": {
                    "type": [
                      "boolean",
                      "null"
                    ],
                    "description": "Use dynamic chaining for downlink",
                    "readOnly": true
                  },
                  "mac": {
                    "type": [
                      "string",
                      "null"
                    ],
                    "description": "Radio (base) mac, it can have 16 bssids (e.g. 5c5b350001a0-5c5b350001af)",
                    "readOnly": true
                  },
                  "noise_floor": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "readOnly": true,
                    "examples": [
                      -90
                    ]
                  },
                  "num_clients": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "num_wlans": {
                    "type": "integer",
                    "description": "How many WLANs are applied to the radio",
                    "contentEncoding": "int32"
                  },
                  "power": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Transmit power (in dBm)",
                    "contentEncoding": "int32",
                    "readOnly": true
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
                  "usage": {
                    "type": [
                      "string",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      "24"
                    ]
                  },
                  "util_all": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "All utilization in percentage",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_non_wifi": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Reception of \"No Packets\" utilization in percentage, received frames with invalid PLCPs and CRS glitches as noise",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_rx_in_bss": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Reception of \"In BSS\" utilization in percentage, only frames that are received from AP/STAs within the BSS",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_rx_other_bss": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Reception of \"Other BSS\" utilization in percentage, all frames received from AP/STAs that are outside the BSS",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_tx": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Transmission utilization in percentage",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_undecodable_wifi": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Reception of \"UnDecodable Wifi\" utilization in percentage, only Preamble, PLCP header is decoded, Rest is undecodable in this radio",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_unknown_wifi": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Reception of \"No Category\" utilization in percentage, all 802.11 frames that are corrupted at the receiver",
                    "contentEncoding": "int32",
                    "readOnly": true
                  }
                },
                "description": "Radio stat"
              },
              "band_6": {
                "type": "object",
                "properties": {
                  "bandwidth": {
                    "type": "integer",
                    "description": "channel width for the band.enum: `0`(disabled, response only), `20`, `40`, `80` (only applicable for band_5 and band_6), `160` (only for band_6)"
                  },
                  "channel": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Current channel the radio is running on",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "dynamic_chaining_enabled": {
                    "type": [
                      "boolean",
                      "null"
                    ],
                    "description": "Use dynamic chaining for downlink",
                    "readOnly": true
                  },
                  "mac": {
                    "type": [
                      "string",
                      "null"
                    ],
                    "description": "Radio (base) mac, it can have 16 bssids (e.g. 5c5b350001a0-5c5b350001af)",
                    "readOnly": true
                  },
                  "noise_floor": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "readOnly": true,
                    "examples": [
                      -90
                    ]
                  },
                  "num_clients": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "num_wlans": {
                    "type": "integer",
                    "description": "How many WLANs are applied to the radio",
                    "contentEncoding": "int32"
                  },
                  "power": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Transmit power (in dBm)",
                    "contentEncoding": "int32",
                    "readOnly": true
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
                  "usage": {
                    "type": [
                      "string",
                      "null"
                    ],
                    "readOnly": true,
                    "examples": [
                      "24"
                    ]
                  },
                  "util_all": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "All utilization in percentage",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_non_wifi": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Reception of \"No Packets\" utilization in percentage, received frames with invalid PLCPs and CRS glitches as noise",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_rx_in_bss": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Reception of \"In BSS\" utilization in percentage, only frames that are received from AP/STAs within the BSS",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_rx_other_bss": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Reception of \"Other BSS\" utilization in percentage, all frames received from AP/STAs that are outside the BSS",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_tx": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Transmission utilization in percentage",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_undecodable_wifi": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Reception of \"UnDecodable Wifi\" utilization in percentage, only Preamble, PLCP header is decoded, Rest is undecodable in this radio",
                    "contentEncoding": "int32",
                    "readOnly": true
                  },
                  "util_unknown_wifi": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Reception of \"No Category\" utilization in percentage, all 802.11 frames that are corrupted at the receiver",
                    "contentEncoding": "int32",
                    "readOnly": true
                  }
                },
                "description": "Radio stat"
              }
            }
          },
          "rx_bps": {
            "type": [
              "integer",
              "null"
            ],
            "description": "Rate of receiving traffic, bits/seconds, last known",
            "contentEncoding": "int64",
            "readOnly": true,
            "examples": [
              60003
            ]
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
          "serial": {
            "type": [
              "string",
              "null"
            ],
            "description": "Serial Number",
            "readOnly": true,
            "examples": [
              "FXLH2015170017"
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
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "switch_redundancy": {
            "title": "stats_ap_switch_redundancy",
            "type": "object",
            "properties": {
              "num_redundant_aps": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int32",
                "readOnly": true,
                "examples": [
                  1
                ]
              }
            }
          },
          "tx_bps": {
            "type": [
              "integer",
              "null"
            ],
            "description": "Rate of transmitting traffic, bits/seconds, last known",
            "contentEncoding": "int64",
            "readOnly": true,
            "examples": [
              634301
            ]
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
          "type": {
            "const": "ap",
            "type": "string",
            "description": "Device Type. enum: `ap`",
            "readOnly": true
          },
          "uptime": {
            "type": [
              "number",
              "null"
            ],
            "description": "How long, in seconds, has the device been up (or rebooted)",
            "readOnly": true,
            "examples": [
              13500
            ]
          },
          "usb_stat": {
            "title": "stats_ap_usb_stat",
            "type": "object",
            "properties": {
              "channel": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int32",
                "readOnly": true,
                "examples": [
                  3
                ]
              },
              "connected": {
                "type": [
                  "boolean",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  true
                ]
              },
              "last_activity": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int32",
                "readOnly": true,
                "examples": [
                  1586873254
                ]
              },
              "type": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "imagotag"
                ]
              },
              "up": {
                "type": [
                  "boolean",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  true
                ]
              }
            }
          },
          "version": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true,
            "examples": [
              "0.14.12345"
            ]
          },
          "x": {
            "type": [
              "number",
              "null"
            ],
            "readOnly": true,
            "examples": [
              53.5
            ]
          },
          "y": {
            "type": [
              "number",
              "null"
            ],
            "readOnly": true,
            "examples": [
              173.1
            ]
          }
        },
        "description": "AP statistics"
      },
      {
        "title": "stats_switch",
        "required": [
          "type"
        ],
        "type": "object",
        "properties": {
          "ap_redundancy": {
            "title": "stats_switch_ap_redundancy",
            "type": "object",
            "properties": {
              "modules": {
                "type": "object",
                "additionalProperties": {
                  "title": "stats_switch_ap_redundancy_module",
                  "type": "object",
                  "properties": {
                    "num_aps": {
                      "type": "integer",
                      "contentEncoding": "int32",
                      "examples": [
                        15
                      ]
                    },
                    "num_aps_with_switch_redundancy": {
                      "type": "integer",
                      "contentEncoding": "int32",
                      "examples": [
                        8
                      ]
                    }
                  }
                },
                "description": "For a VC / stacked switches."
              },
              "num_aps": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  15
                ]
              },
              "num_aps_with_switch_redundancy": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  8
                ]
              }
            }
          },
          "arp_table_stats": {
            "title": "arp_table_stats",
            "type": "object",
            "properties": {
              "arp_table_count": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "max_entries_supported": {
                "type": "integer",
                "contentEncoding": "int32"
              }
            }
          },
          "auto_upgrade_stat": {
            "title": "stats_ap_auto_upgrade",
            "type": "object",
            "properties": {
              "lastcheck": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int64",
                "readOnly": true,
                "examples": [
                  1720594762
                ]
              }
            }
          },
          "cert_expiry": {
            "type": "integer",
            "contentEncoding": "int64"
          },
          "clients": {
            "type": "array",
            "items": {
              "title": "stats_switch_client_item",
              "type": "object",
              "properties": {
                "device_mac": {
                  "type": "string"
                },
                "hostname": {
                  "type": "string"
                },
                "mac": {
                  "type": "string"
                },
                "port_id": {
                  "type": "string"
                }
              }
            },
            "description": ""
          },
          "clients_stats": {
            "title": "stats_switch_clients_stats",
            "type": "object",
            "properties": {
              "total": {
                "title": "stats_switch_clients_stats_total",
                "type": "object",
                "properties": {
                  "num_aps": {
                    "type": "array",
                    "items": {
                      "type": "integer",
                      "contentEncoding": "int32"
                    },
                    "description": ""
                  },
                  "num_wired_clients": {
                    "type": "integer",
                    "contentEncoding": "int32"
                  }
                }
              }
            }
          },
          "config_status": {
            "type": "string",
            "readOnly": true
          },
          "config_timestamp": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "config_version": {
            "type": "integer",
            "contentEncoding": "int32"
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
          "created_time": {
            "type": "number",
            "description": "When the object has been created, in epoch",
            "readOnly": true
          },
          "deviceprofile_id": {
            "type": [
              "string",
              "null"
            ],
            "contentEncoding": "uuid",
            "readOnly": true
          },
          "dhcpd_stat": {
            "type": "object",
            "additionalProperties": {
              "title": "dhcpd_stat_lan",
              "type": "object",
              "properties": {
                "num_ips": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    100
                  ]
                },
                "num_leased": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    20
                  ]
                }
              }
            },
            "description": "Property key is the network name"
          },
          "evpntopo_id": {
            "type": [
              "string",
              "null"
            ],
            "contentEncoding": "uuid",
            "readOnly": true
          },
          "ext_ip": {
            "type": "string"
          },
          "fw_versions_outofsync": {
            "type": "boolean",
            "readOnly": true
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
          "has_pcap": {
            "type": "boolean",
            "description": "Whether the switch supports packet capture",
            "readOnly": true,
            "examples": [
              false
            ]
          },
          "hostname": {
            "type": "string",
            "description": "Hostname reported by the device",
            "readOnly": true,
            "examples": [
              "sj-sw1"
            ]
          },
          "hw_rev": {
            "type": "string",
            "description": "Device hardware revision number"
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
          "if_stat": {
            "type": "object",
            "additionalProperties": {
              "title": "if_stat_property",
              "type": "object",
              "properties": {
                "address_mode": {
                  "type": "string"
                },
                "ips": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": ""
                },
                "nat_addresses": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": ""
                },
                "network_name": {
                  "type": "string"
                },
                "port_id": {
                  "type": "string"
                },
                "port_usage": {
                  "type": "string"
                },
                "redundancy_state": {
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
                "servp_info": {
                  "title": "if_stat_property_servp_info",
                  "type": "object",
                  "properties": {
                    "asn": {
                      "type": "string"
                    },
                    "city": {
                      "type": "string"
                    },
                    "country_code": {
                      "type": "string"
                    },
                    "latitude": {
                      "type": "number"
                    },
                    "longitude": {
                      "type": "number"
                    },
                    "org": {
                      "type": "string"
                    },
                    "region_code": {
                      "type": "string"
                    }
                  }
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
                },
                "vlan": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "wan_name": {
                  "type": "string"
                },
                "wan_type": {
                  "type": "string"
                }
              }
            },
            "description": "Property key is the interface name"
          },
          "ip": {
            "type": "string",
            "readOnly": true,
            "examples": [
              "10.2.11.137"
            ]
          },
          "ip_stat": {
            "title": "ip_stat",
            "type": "object",
            "properties": {
              "dhcp_server": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "192.168.95.1"
                ]
              },
              "dns": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "dns_suffix": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "gateway": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true
              },
              "gateway6": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "fdad:b0bc:f29e::1"
                ]
              },
              "ip": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "10.3.3.1"
                ]
              },
              "ip6": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "fdad:b0bc:f29e::3d16"
                ]
              },
              "ips": {
                "type": "object",
                "additionalProperties": {
                  "type": "string",
                  "nullable": true
                }
              },
              "netmask": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "255.255.255.0"
                ]
              },
              "netmask6": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "/64"
                ]
              }
            }
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
          "last_trouble": {
            "type": "object",
            "properties": {
              "code": {
                "type": "string",
                "description": "Code definitions list at [List Ap Led Definition]($e/Constants%20Definitions/listApLedDefinition)",
                "examples": [
                  "03"
                ]
              },
              "timestamp": {
                "type": "number",
                "description": "Epoch (seconds)",
                "readOnly": true
              }
            },
            "description": "Last trouble code of switch"
          },
          "mac": {
            "type": "string",
            "readOnly": true
          },
          "mac_table_stats": {
            "title": "mac_table_stats",
            "type": "object",
            "properties": {
              "mac_table_count": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "max_mac_entries_supported": {
                "type": "integer",
                "contentEncoding": "int32"
              }
            }
          },
          "map_id": {
            "type": [
              "string",
              "null"
            ],
            "contentEncoding": "uuid",
            "readOnly": true
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
            "type": "string",
            "readOnly": true,
            "examples": [
              "EX4600"
            ]
          },
          "modified_time": {
            "type": "number",
            "description": "When the object has been modified for the last time, in epoch",
            "readOnly": true
          },
          "module_stat": {
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
          "name": {
            "type": "string",
            "description": "Device name if configured",
            "readOnly": true,
            "examples": [
              "sj-sw1"
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
          "ports": {
            "type": "array",
            "items": {
              "title": "stats_switch_port",
              "required": [
                "mac",
                "org_id",
                "port_id",
                "site_id"
              ],
              "type": "object",
              "properties": {
                "active": {
                  "type": "boolean",
                  "description": "Indicates if interface is active/inactive",
                  "readOnly": true
                },
                "auth_state": {
                  "type": "string",
                  "description": "enum: `authenticated`, `authenticating`, `held`, `init`"
                },
                "disabled": {
                  "type": "boolean",
                  "description": "Indicates if interface is disabled",
                  "readOnly": true
                },
                "for_site": {
                  "type": "boolean",
                  "readOnly": true
                },
                "full_duplex": {
                  "type": "boolean",
                  "description": "Indicates full or half duplex",
                  "examples": [
                    true
                  ]
                },
                "jitter": {
                  "type": "number",
                  "description": "Last sampled jitter of the interface",
                  "readOnly": true
                },
                "last_flapped": {
                  "type": "number",
                  "description": "Indicates when the port was last flapped",
                  "readOnly": true
                },
                "latency": {
                  "type": "number",
                  "description": "Last sampled latency of the interface",
                  "readOnly": true
                },
                "loss": {
                  "type": "number",
                  "description": "Last sampled loss of the interface",
                  "readOnly": true
                },
                "lte_iccid": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "description": "LTE ICCID value, Check for null/empty"
                },
                "lte_imei": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "description": "LTE IMEI value, Check for null/empty"
                },
                "lte_imsi": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "description": "LTE IMSI value, Check for null/empty"
                },
                "mac": {
                  "type": "string",
                  "readOnly": true,
                  "examples": [
                    "5c4527a96580"
                  ]
                },
                "mac_count": {
                  "type": "integer",
                  "description": "Number of mac addresses in the forwarding table",
                  "contentEncoding": "int32",
                  "readOnly": true
                },
                "mac_limit": {
                  "minimum": 0.0,
                  "type": "integer",
                  "description": "Limit on number of dynamically learned macs",
                  "contentEncoding": "int32",
                  "readOnly": true
                },
                "neighbor_mac": {
                  "type": "string",
                  "description": "chassis identifier of the chassis type listed",
                  "readOnly": true,
                  "examples": [
                    "64d814353400"
                  ]
                },
                "neighbor_port_desc": {
                  "type": "string",
                  "description": "Description supplied by the system on the interface E.g. \"GigabitEthernet2/0/39\"",
                  "readOnly": true,
                  "examples": [
                    "GigabitEthernet1/0/21"
                  ]
                },
                "neighbor_system_name": {
                  "type": "string",
                  "description": "Name supplied by the system on the interface E.g. neighbor system name E.g. \"Kumar-Acc-SW.mist.local\"",
                  "readOnly": true,
                  "examples": [
                    "CORP-D-SW-2"
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
                "poe_disabled": {
                  "type": "boolean",
                  "description": "Is the POE disabled",
                  "readOnly": true
                },
                "poe_mode": {
                  "type": "string",
                  "description": "enum: `802.3af`, `802.3at`, `802.3bt`"
                },
                "poe_on": {
                  "type": "boolean",
                  "description": "Is the device attached to POE",
                  "readOnly": true
                },
                "poe_priority": {
                  "type": "string",
                  "description": "PoE priority. enum: `low`, `high`"
                },
                "port_id": {
                  "type": "string",
                  "readOnly": true,
                  "examples": [
                    "ge-0/0/0"
                  ]
                },
                "port_mac": {
                  "type": "string",
                  "description": "Interface MAC address",
                  "readOnly": true,
                  "examples": [
                    "5c4527a96580"
                  ]
                },
                "port_usage": {
                  "type": "string",
                  "examples": [
                    "lan"
                  ]
                },
                "power_draw": {
                  "type": "number",
                  "description": "Amount of power being used by the interface at the time the command is executed. Unit in watts.",
                  "readOnly": true
                },
                "rx_bcast_pkts": {
                  "type": "integer",
                  "description": "Broadcast input packets",
                  "contentEncoding": "int32",
                  "readOnly": true
                },
                "rx_bps": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "description": "Rate of receiving traffic, bits/seconds, last known",
                  "contentEncoding": "int64",
                  "readOnly": true,
                  "examples": [
                    60003
                  ]
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
                  "description": "Input errors",
                  "contentEncoding": "int32",
                  "readOnly": true
                },
                "rx_mcast_pkts": {
                  "type": "integer",
                  "description": "Multicast input packets",
                  "contentEncoding": "int32",
                  "readOnly": true
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
                "site_id": {
                  "type": "string",
                  "contentEncoding": "uuid",
                  "readOnly": true,
                  "examples": [
                    "441a1214-6928-442a-8e92-e1d34b8ec6a6"
                  ]
                },
                "speed": {
                  "type": "integer",
                  "description": "Port speed",
                  "contentEncoding": "int32",
                  "readOnly": true,
                  "examples": [
                    1000
                  ]
                },
                "stp_role": {
                  "type": "string",
                  "description": "enum: `alternate`, `backup`, `designated`, `disabled`, `root`, `root-prevented`"
                },
                "stp_state": {
                  "type": "string",
                  "description": "enum: `blocking`, `disabled`, `forwarding`, `learning`, `listening`"
                },
                "tx_bcast_pkts": {
                  "type": "integer",
                  "description": "Broadcast output packets",
                  "contentEncoding": "int32",
                  "readOnly": true
                },
                "tx_bps": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "description": "Rate of transmitting traffic, bits/seconds, last known",
                  "contentEncoding": "int64",
                  "readOnly": true,
                  "examples": [
                    634301
                  ]
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
                  "description": "Output errors",
                  "contentEncoding": "int32",
                  "readOnly": true
                },
                "tx_mcast_pkts": {
                  "type": "integer",
                  "description": "Multicast output packets",
                  "contentEncoding": "int32",
                  "readOnly": true
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
                "type": {
                  "type": "string",
                  "description": "device type. enum: `ap`, `ble`, `gateway`, `mxedge`, `nac`, `switch`"
                },
                "unconfigured": {
                  "type": "boolean",
                  "description": "Indicates if interface is unconfigured",
                  "readOnly": true
                },
                "up": {
                  "type": "boolean",
                  "description": "Indicates if interface is up",
                  "readOnly": true
                },
                "xcvr_model": {
                  "type": "string",
                  "description": "Optic Slot ModelName, Check for null/empty",
                  "readOnly": true,
                  "examples": [
                    "SFP+-10G-SR"
                  ]
                },
                "xcvr_part_number": {
                  "type": "string",
                  "description": "Optic Slot Partnumber, Check for null/empty",
                  "readOnly": true,
                  "examples": [
                    "740-021487"
                  ]
                },
                "xcvr_serial": {
                  "type": "string",
                  "description": "Optic Slot SerialNumber, Check for null/empty",
                  "readOnly": true,
                  "examples": [
                    "N6AA9HT"
                  ]
                }
              },
              "description": "Switch port statistics"
            },
            "description": ""
          },
          "route_summary_stats": {
            "title": "route_summary_stats",
            "type": "object",
            "properties": {
              "fib_routes": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "max_unicast_routes_supported": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "rib_routes": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "total_routes": {
                "type": "integer",
                "contentEncoding": "int32"
              }
            }
          },
          "serial": {
            "type": "string",
            "readOnly": true,
            "examples": [
              "TC3714190003"
            ]
          },
          "service_stat": {
            "type": "object",
            "additionalProperties": {
              "title": "service_stat_property",
              "type": "object",
              "properties": {
                "ash_version": {
                  "type": "string"
                },
                "cia_version": {
                  "type": "string"
                },
                "ember_version": {
                  "type": "string"
                },
                "ipsec_client_version": {
                  "type": "string"
                },
                "mist_agent_version": {
                  "type": "string"
                },
                "package_version": {
                  "type": "string"
                },
                "testing_tools_version": {
                  "type": "string"
                },
                "wheeljack_version": {
                  "type": "string"
                }
              }
            }
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
            "readOnly": true,
            "examples": [
              "connected"
            ]
          },
          "tag_id": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "tag_uuid": {
            "type": "string",
            "contentEncoding": "uuid"
          },
          "type": {
            "const": "switch",
            "type": "string",
            "description": "Device Type. enum: `switch`"
          },
          "uptime": {
            "type": [
              "number",
              "null"
            ],
            "readOnly": true,
            "examples": [
              13501
            ]
          },
          "vc_mac": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true
          },
          "vc_setup_info": {
            "title": "stats_switch_vc_setup_info",
            "type": "object",
            "properties": {
              "config_type": {
                "type": "string",
                "readOnly": true,
                "examples": [
                  "nonprovisioned"
                ]
              },
              "current_stats": {
                "type": "string",
                "readOnly": true,
                "examples": [
                  "VCSETUP_WAITING"
                ]
              },
              "err_missing_dev_id_fpc": {
                "type": "boolean",
                "readOnly": true
              },
              "last_update": {
                "type": "number",
                "readOnly": true
              },
              "request_time": {
                "type": "number",
                "readOnly": true
              },
              "request_type": {
                "type": "string",
                "readOnly": true,
                "examples": [
                  "vc_create"
                ]
              }
            }
          },
          "version": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true,
            "examples": [
              "18.4R1.8"
            ]
          }
        },
        "description": "Switch statistics"
      },
      {
        "title": "stats_gateway",
        "required": [
          "mac",
          "type"
        ],
        "type": "object",
        "properties": {
          "ap_redundancy": {
            "title": "ap_redundancy",
            "type": "object",
            "properties": {
              "modules": {
                "type": "object",
                "additionalProperties": {
                  "title": "ap_redundancy_module",
                  "type": "object",
                  "properties": {
                    "num_aps": {
                      "type": "integer",
                      "contentEncoding": "int32",
                      "examples": [
                        15
                      ]
                    },
                    "num_aps_with_switch_redundancy": {
                      "type": "integer",
                      "contentEncoding": "int32",
                      "examples": [
                        8
                      ]
                    }
                  }
                },
                "description": "Property key is the node id"
              },
              "num_aps": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  15
                ]
              },
              "num_aps_with_switch_redundancy": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  8
                ]
              }
            }
          },
          "arp_table_stats": {
            "title": "arp_table_stats",
            "type": "object",
            "properties": {
              "arp_table_count": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "max_entries_supported": {
                "type": "integer",
                "contentEncoding": "int32"
              }
            }
          },
          "auto_upgrade_stat": {
            "title": "stats_ap_auto_upgrade",
            "type": "object",
            "properties": {
              "lastcheck": {
                "type": [
                  "integer",
                  "null"
                ],
                "contentEncoding": "int64",
                "readOnly": true,
                "examples": [
                  1720594762
                ]
              }
            }
          },
          "bgp_peers": {
            "type": "array",
            "items": {
              "title": "bgp_peer",
              "type": "object",
              "properties": {
                "evpn_overlay": {
                  "type": "boolean",
                  "description": "If this is created for evpn overlay"
                },
                "for_overlay": {
                  "type": "boolean",
                  "description": "If this is created for overlay"
                },
                "local_as": {
                  "type": "object",
                  "description": "BGP AS, value in range 1-4294967294. Can be a Variable (e.g. `{{bgp_as}}` )"
                },
                "neighbor": {
                  "type": "string",
                  "examples": [
                    "15.8.3.5"
                  ]
                },
                "neighbor_as": {
                  "type": "object",
                  "description": "BGP AS, value in range 1-4294967294. Can be a Variable (e.g. `{{bgp_as}}` )"
                },
                "neighbor_mac": {
                  "type": "string",
                  "description": "If it's another device in the same org",
                  "examples": [
                    "020001c04600"
                  ]
                },
                "node": {
                  "type": "string",
                  "description": "Node0/node1",
                  "examples": [
                    "node0"
                  ]
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
                "rx_routes": {
                  "type": "integer",
                  "description": "Number of received routes",
                  "contentEncoding": "int32",
                  "examples": [
                    60
                  ]
                },
                "state": {
                  "type": "string",
                  "description": "enum: `active`, `connect`, `established`, `idle`, `open_config`, `open_sent`"
                },
                "timestamp": {
                  "type": "number",
                  "description": "Epoch (seconds)",
                  "readOnly": true
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
                "tx_routes": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    60
                  ]
                },
                "up": {
                  "type": "boolean"
                },
                "uptime": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    31355
                  ]
                },
                "vrf_name": {
                  "type": "string",
                  "examples": [
                    "default"
                  ]
                }
              },
              "description": "Only present when `bgp_peers` in `fields` query parameter"
            },
            "description": "Only present when `bgp_peers` in `fields` query parameter. Each port object is same as `GET /api/v1/sites/{site_id}/stats/bgp_peers/search` result object, except that org_id, site_id, mac, model are removed"
          },
          "cert_expiry": {
            "type": "integer",
            "contentEncoding": "int64"
          },
          "cluster_config": {
            "title": "stats_cluster_config",
            "type": "object",
            "properties": {
              "configuration": {
                "type": "string"
              },
              "control_link_info": {
                "title": "stats_cluster_config_control_link_info",
                "type": "object",
                "properties": {
                  "name": {
                    "type": "string"
                  },
                  "status": {
                    "type": "string"
                  }
                }
              },
              "ethernet_connection": {
                "type": "array",
                "items": {
                  "title": "stats_cluster_config_ethernet_connection_item",
                  "type": "object",
                  "properties": {
                    "name": {
                      "type": "string"
                    },
                    "status": {
                      "type": "string"
                    }
                  }
                },
                "description": ""
              },
              "fabric_link_info": {
                "title": "stats_cluster_config_fabric_link_info",
                "type": "object",
                "properties": {
                  "DataPlaneNotifiedStatus": {
                    "type": "string"
                  },
                  "Interface": {
                    "uniqueItems": true,
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "description": ""
                  },
                  "InternalStatus": {
                    "type": "string"
                  },
                  "State": {
                    "type": "string"
                  },
                  "Status": {
                    "type": "string"
                  }
                }
              },
              "last_status_change_reason": {
                "type": "string"
              },
              "operational": {
                "type": "string"
              },
              "primary_node_health": {
                "type": "string"
              },
              "redundancy_group_information": {
                "type": "array",
                "items": {
                  "title": "stats_cluster_config_redundancy_group_info_item",
                  "type": "object",
                  "properties": {
                    "Id": {
                      "type": "integer",
                      "contentEncoding": "int32"
                    },
                    "MonitoringFailure": {
                      "type": "string"
                    },
                    "Threshold": {
                      "type": "integer",
                      "contentEncoding": "int32"
                    }
                  }
                },
                "description": ""
              },
              "secondary_node_health": {
                "type": "string"
              },
              "status": {
                "type": "string"
              }
            }
          },
          "cluster_stat": {
            "title": "stats_gateway_cluster",
            "type": "object",
            "properties": {
              "state": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true
              }
            }
          },
          "conductor_name": {
            "type": "string",
            "readOnly": true
          },
          "config_status": {
            "type": "string",
            "readOnly": true
          },
          "config_timestamp": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "config_version": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "cpu2_stat": {
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
          "created_time": {
            "type": "number",
            "description": "When the object has been created, in epoch",
            "readOnly": true
          },
          "deviceprofile_id": {
            "type": [
              "string",
              "null"
            ],
            "contentEncoding": "uuid",
            "readOnly": true
          },
          "deviceprofile_name": {
            "type": "string"
          },
          "dhcpd2_stat": {
            "type": "object",
            "additionalProperties": {
              "title": "dhcpd_stat_lan",
              "type": "object",
              "properties": {
                "num_ips": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    100
                  ]
                },
                "num_leased": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    20
                  ]
                }
              }
            },
            "description": "Property key is the network name"
          },
          "dhcpd_stat": {
            "type": "object",
            "additionalProperties": {
              "title": "dhcpd_stat_lan",
              "type": "object",
              "properties": {
                "num_ips": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    100
                  ]
                },
                "num_leased": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    20
                  ]
                }
              }
            },
            "description": "Property key is the network name"
          },
          "evpntopo_id": {
            "type": [
              "string",
              "null"
            ],
            "contentEncoding": "uuid",
            "readOnly": true
          },
          "ext_ip": {
            "type": [
              "string",
              "null"
            ],
            "description": "IP address",
            "readOnly": true,
            "examples": [
              "66.129.234.224"
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
          "has_pcap": {
            "type": [
              "boolean",
              "null"
            ],
            "readOnly": true
          },
          "hostname": {
            "type": "string",
            "description": "Hostname reported by the device",
            "examples": [
              "sj1"
            ]
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
          "if2_stat": {
            "type": "object",
            "additionalProperties": {
              "title": "if_stat_property",
              "type": "object",
              "properties": {
                "address_mode": {
                  "type": "string"
                },
                "ips": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": ""
                },
                "nat_addresses": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": ""
                },
                "network_name": {
                  "type": "string"
                },
                "port_id": {
                  "type": "string"
                },
                "port_usage": {
                  "type": "string"
                },
                "redundancy_state": {
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
                "servp_info": {
                  "title": "if_stat_property_servp_info",
                  "type": "object",
                  "properties": {
                    "asn": {
                      "type": "string"
                    },
                    "city": {
                      "type": "string"
                    },
                    "country_code": {
                      "type": "string"
                    },
                    "latitude": {
                      "type": "number"
                    },
                    "longitude": {
                      "type": "number"
                    },
                    "org": {
                      "type": "string"
                    },
                    "region_code": {
                      "type": "string"
                    }
                  }
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
                },
                "vlan": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "wan_name": {
                  "type": "string"
                },
                "wan_type": {
                  "type": "string"
                }
              }
            },
            "description": "Property key is the interface name"
          },
          "if_stat": {
            "type": "object",
            "additionalProperties": {
              "title": "if_stat_property",
              "type": "object",
              "properties": {
                "address_mode": {
                  "type": "string"
                },
                "ips": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": ""
                },
                "nat_addresses": {
                  "uniqueItems": true,
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": ""
                },
                "network_name": {
                  "type": "string"
                },
                "port_id": {
                  "type": "string"
                },
                "port_usage": {
                  "type": "string"
                },
                "redundancy_state": {
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
                "servp_info": {
                  "title": "if_stat_property_servp_info",
                  "type": "object",
                  "properties": {
                    "asn": {
                      "type": "string"
                    },
                    "city": {
                      "type": "string"
                    },
                    "country_code": {
                      "type": "string"
                    },
                    "latitude": {
                      "type": "number"
                    },
                    "longitude": {
                      "type": "number"
                    },
                    "org": {
                      "type": "string"
                    },
                    "region_code": {
                      "type": "string"
                    }
                  }
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
                },
                "vlan": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "wan_name": {
                  "type": "string"
                },
                "wan_type": {
                  "type": "string"
                }
              }
            },
            "description": "Property key is the interface name"
          },
          "ip": {
            "type": [
              "string",
              "null"
            ],
            "description": "IP address",
            "readOnly": true,
            "examples": [
              "10.2.11.137"
            ]
          },
          "ip2_stat": {
            "title": "ip_stat",
            "type": "object",
            "properties": {
              "dhcp_server": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "192.168.95.1"
                ]
              },
              "dns": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "dns_suffix": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "gateway": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true
              },
              "gateway6": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "fdad:b0bc:f29e::1"
                ]
              },
              "ip": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "10.3.3.1"
                ]
              },
              "ip6": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "fdad:b0bc:f29e::3d16"
                ]
              },
              "ips": {
                "type": "object",
                "additionalProperties": {
                  "type": "string",
                  "nullable": true
                }
              },
              "netmask": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "255.255.255.0"
                ]
              },
              "netmask6": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "/64"
                ]
              }
            }
          },
          "ip_stat": {
            "title": "ip_stat",
            "type": "object",
            "properties": {
              "dhcp_server": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "192.168.95.1"
                ]
              },
              "dns": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "dns_suffix": {
                "uniqueItems": true,
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": ""
              },
              "gateway": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true
              },
              "gateway6": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "fdad:b0bc:f29e::1"
                ]
              },
              "ip": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "10.3.3.1"
                ]
              },
              "ip6": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "fdad:b0bc:f29e::3d16"
                ]
              },
              "ips": {
                "type": "object",
                "additionalProperties": {
                  "type": "string",
                  "nullable": true
                }
              },
              "netmask": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "255.255.255.0"
                ]
              },
              "netmask6": {
                "type": [
                  "string",
                  "null"
                ],
                "readOnly": true,
                "examples": [
                  "/64"
                ]
              }
            }
          },
          "is_ha": {
            "type": [
              "boolean",
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
          "mac": {
            "type": "string",
            "description": "Device mac",
            "examples": [
              "dc38e1dbf3cd"
            ]
          },
          "mac_table_stats": {
            "title": "stats_gateway_mac_table_stats",
            "type": "object",
            "properties": {
              "mac_table_count": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "max_mac_entries_supported": {
                "type": "integer",
                "contentEncoding": "int32"
              }
            }
          },
          "map_id": {
            "type": [
              "string",
              "null"
            ],
            "description": "Serial Number",
            "contentEncoding": "uuid",
            "readOnly": true
          },
          "memory2_stat": {
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
            "type": "string",
            "description": "Device model",
            "examples": [
              "SRX320"
            ]
          },
          "modified_time": {
            "type": "number",
            "description": "When the object has been modified for the last time, in epoch",
            "readOnly": true
          },
          "module2_stat": {
            "maxItems": 1,
            "minItems": 0,
            "type": "array",
            "items": {
              "title": "stats_gateway_module_stat_item",
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
                "network_resources": {
                  "type": "array",
                  "items": {
                    "title": "module_stat_item_network_resource",
                    "type": "object",
                    "properties": {
                      "count": {
                        "minimum": 0.0,
                        "type": "integer",
                        "description": "current usage of the network resource",
                        "contentEncoding": "int32",
                        "examples": [
                          17
                        ]
                      },
                      "limit": {
                        "minimum": 0.0,
                        "type": "integer",
                        "description": "maximum usage of the network resource",
                        "contentEncoding": "int32",
                        "examples": [
                          768000
                        ]
                      },
                      "type": {
                        "type": "string",
                        "description": "type of the network resource (e.g. FIB, FLOW, ...)",
                        "examples": [
                          "FIB"
                        ]
                      }
                    }
                  },
                  "description": ""
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
          "module_stat": {
            "maxItems": 1,
            "minItems": 0,
            "type": "array",
            "items": {
              "title": "stats_gateway_module_stat_item",
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
                "network_resources": {
                  "type": "array",
                  "items": {
                    "title": "module_stat_item_network_resource",
                    "type": "object",
                    "properties": {
                      "count": {
                        "minimum": 0.0,
                        "type": "integer",
                        "description": "current usage of the network resource",
                        "contentEncoding": "int32",
                        "examples": [
                          17
                        ]
                      },
                      "limit": {
                        "minimum": 0.0,
                        "type": "integer",
                        "description": "maximum usage of the network resource",
                        "contentEncoding": "int32",
                        "examples": [
                          768000
                        ]
                      },
                      "type": {
                        "type": "string",
                        "description": "type of the network resource (e.g. FIB, FLOW, ...)",
                        "examples": [
                          "FIB"
                        ]
                      }
                    }
                  },
                  "description": ""
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
          "name": {
            "type": "string",
            "description": "Device name if configured",
            "readOnly": true,
            "examples": [
              "sj1"
            ]
          },
          "node_name": {
            "type": "string",
            "readOnly": true,
            "examples": [
              "node0"
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
          "ports": {
            "type": "array",
            "items": {
              "title": "stats_gateway_port",
              "required": [
                "neighbor_mac",
                "port_id",
                "port_mac"
              ],
              "type": "object",
              "properties": {
                "active": {
                  "type": "boolean",
                  "description": "Indicates if interface is active/inactive",
                  "readOnly": true
                },
                "auth_state": {
                  "type": "string",
                  "description": "enum: `authenticated`, `authenticating`, `held`, `init`"
                },
                "disabled": {
                  "type": "boolean",
                  "description": "Indicates if interface is disabled",
                  "readOnly": true
                },
                "for_site": {
                  "type": "boolean",
                  "readOnly": true
                },
                "full_duplex": {
                  "type": "boolean",
                  "description": "Indicates full or half duplex",
                  "examples": [
                    true
                  ]
                },
                "jitter": {
                  "type": "number",
                  "description": "Last sampled jitter of the interface",
                  "readOnly": true
                },
                "latency": {
                  "type": "number",
                  "description": "Last sampled latency of the interface",
                  "readOnly": true
                },
                "loss": {
                  "type": "number",
                  "description": "Last sampled loss of the interface",
                  "readOnly": true
                },
                "lte_iccid": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "description": "LTE ICCID value, Check for null/empty"
                },
                "lte_imei": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "description": "LTE IMEI value, Check for null/empty"
                },
                "lte_imsi": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "description": "LTE IMSI value, Check for null/empty"
                },
                "mac_count": {
                  "type": "integer",
                  "description": "Number of mac addresses in the forwarding table",
                  "contentEncoding": "int32",
                  "readOnly": true
                },
                "mac_limit": {
                  "minimum": 0.0,
                  "type": "integer",
                  "description": "Limit on number of dynamically learned macs",
                  "contentEncoding": "int32",
                  "readOnly": true
                },
                "neighbor_mac": {
                  "type": "string",
                  "description": "chassis identifier of the chassis type listed",
                  "readOnly": true,
                  "examples": [
                    "64d814353400"
                  ]
                },
                "neighbor_port_desc": {
                  "type": "string",
                  "description": "Description supplied by the system on the interface E.g. \"GigabitEthernet2/0/39\"",
                  "readOnly": true,
                  "examples": [
                    "GigabitEthernet1/0/21"
                  ]
                },
                "neighbor_system_name": {
                  "type": "string",
                  "description": "Name supplied by the system on the interface E.g. neighbor system name E.g. \"Kumar-Acc-SW.mist.local\"",
                  "readOnly": true,
                  "examples": [
                    "CORP-D-SW-2"
                  ]
                },
                "poe_disabled": {
                  "type": "boolean",
                  "description": "Is the POE configured not be disabled.",
                  "readOnly": true
                },
                "poe_mode": {
                  "type": "string",
                  "description": "enum: `802.3af`, `802.3at`, `802.3bt`"
                },
                "poe_on": {
                  "type": "boolean",
                  "description": "Is the device attached to POE",
                  "readOnly": true
                },
                "port_id": {
                  "type": "string",
                  "readOnly": true,
                  "examples": [
                    "ge-0/0/0"
                  ]
                },
                "port_mac": {
                  "type": "string",
                  "description": "Interface mac address",
                  "readOnly": true,
                  "examples": [
                    "5c4527a96580"
                  ]
                },
                "port_usage": {
                  "type": "string",
                  "examples": [
                    "lan"
                  ]
                },
                "power_draw": {
                  "type": "number",
                  "description": "Amount of power being used by the interface at the time the command is executed. Unit in watts.",
                  "readOnly": true
                },
                "rx_bcast_pkts": {
                  "type": "integer",
                  "description": "Broadcast input packets",
                  "contentEncoding": "int32",
                  "readOnly": true
                },
                "rx_bps": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "description": "Rate of receiving traffic, bits/seconds, last known",
                  "contentEncoding": "int64",
                  "readOnly": true,
                  "examples": [
                    60003
                  ]
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
                  "description": "Input errors",
                  "contentEncoding": "int32",
                  "readOnly": true
                },
                "rx_mcast_pkts": {
                  "type": "integer",
                  "description": "Multicast input packets",
                  "contentEncoding": "int32",
                  "readOnly": true
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
                "speed": {
                  "type": "integer",
                  "description": "Port speed",
                  "contentEncoding": "int32",
                  "readOnly": true,
                  "examples": [
                    1000
                  ]
                },
                "stp_role": {
                  "type": "string",
                  "description": "enum: `alternate`, `backup`, `designated`, `disabled`, `root`, `root-prevented`"
                },
                "stp_state": {
                  "type": "string",
                  "description": "enum: `blocking`, `disabled`, `forwarding`, `learning`, `listening`"
                },
                "tx_bcast_pkts": {
                  "type": "integer",
                  "description": "Broadcast output packets",
                  "contentEncoding": "int32",
                  "readOnly": true
                },
                "tx_bps": {
                  "type": [
                    "integer",
                    "null"
                  ],
                  "description": "Rate of transmitting traffic, bits/seconds, last known",
                  "contentEncoding": "int64",
                  "readOnly": true,
                  "examples": [
                    634301
                  ]
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
                  "description": "Output errors",
                  "contentEncoding": "int32",
                  "readOnly": true
                },
                "tx_mcast_pkts": {
                  "type": "integer",
                  "description": "Multicast output packets",
                  "contentEncoding": "int32",
                  "readOnly": true
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
                "type": {
                  "type": "string",
                  "description": "device type. enum: `ap`, `ble`, `gateway`, `mxedge`, `nac`, `switch`"
                },
                "unconfigured": {
                  "type": "boolean",
                  "description": "Indicates if interface is unconfigured",
                  "readOnly": true
                },
                "up": {
                  "type": "boolean",
                  "description": "Indicates if interface is up",
                  "readOnly": true
                },
                "xcvr_model": {
                  "type": "string",
                  "description": "Optic Slot ModelName, Check for null/empty",
                  "readOnly": true,
                  "examples": [
                    "SFP+-10G-SR"
                  ]
                },
                "xcvr_part_number": {
                  "type": "string",
                  "description": "Optic Slot Partnumber, Check for null/empty",
                  "readOnly": true,
                  "examples": [
                    "740-021487"
                  ]
                },
                "xcvr_serial": {
                  "type": "string",
                  "description": "Optic Slot SerialNumber, Check for null/empty",
                  "readOnly": true,
                  "examples": [
                    "N6AA9HT"
                  ]
                }
              },
              "description": "Port statistics"
            },
            "description": "Only present when `ports` in `fields` query parameter. Each port object is same as `GET /api/v1/sites/{site_id}/stats/ports/search` result object, except that org_id, site_id, mac, model are removed"
          },
          "route_summary_stats": {
            "title": "route_summary_stats",
            "type": "object",
            "properties": {
              "fib_routes": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "max_unicast_routes_supported": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "rib_routes": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "total_routes": {
                "type": "integer",
                "contentEncoding": "int32"
              }
            }
          },
          "router_name": {
            "type": "string",
            "description": "Device name if configured",
            "readOnly": true,
            "examples": [
              "sj1"
            ]
          },
          "serial": {
            "type": "string",
            "description": "Serial Number",
            "readOnly": true,
            "examples": [
              "TC3714190003"
            ]
          },
          "service2_stat": {
            "type": "object",
            "additionalProperties": {
              "title": "service_stat_property",
              "type": "object",
              "properties": {
                "ash_version": {
                  "type": "string"
                },
                "cia_version": {
                  "type": "string"
                },
                "ember_version": {
                  "type": "string"
                },
                "ipsec_client_version": {
                  "type": "string"
                },
                "mist_agent_version": {
                  "type": "string"
                },
                "package_version": {
                  "type": "string"
                },
                "testing_tools_version": {
                  "type": "string"
                },
                "wheeljack_version": {
                  "type": "string"
                }
              }
            }
          },
          "service_stat": {
            "type": "object",
            "additionalProperties": {
              "title": "service_stat_property",
              "type": "object",
              "properties": {
                "ash_version": {
                  "type": "string"
                },
                "cia_version": {
                  "type": "string"
                },
                "ember_version": {
                  "type": "string"
                },
                "ipsec_client_version": {
                  "type": "string"
                },
                "mist_agent_version": {
                  "type": "string"
                },
                "package_version": {
                  "type": "string"
                },
                "testing_tools_version": {
                  "type": "string"
                },
                "wheeljack_version": {
                  "type": "string"
                }
              }
            }
          },
          "service_status": {
            "title": "stats_gateway_service_status",
            "type": "object",
            "properties": {
              "appid_install_result": {
                "type": "string"
              },
              "appid_install_timestamp": {
                "type": "string"
              },
              "appid_status": {
                "type": "string"
              },
              "appid_version": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "ewf_status": {
                "type": "string"
              },
              "idp_install_result": {
                "type": "string"
              },
              "idp_install_timestamp": {
                "type": "string"
              },
              "idp_policy": {
                "type": "string"
              },
              "idp_status": {
                "type": "string"
              },
              "idp_update_timestamp": {
                "type": "string"
              }
            }
          },
          "site_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "441a1214-6928-442a-8e92-e1d34b8ec6a6"
            ]
          },
          "spu2_stat": {
            "type": "array",
            "items": {
              "title": "stats_gateway_spu_item",
              "type": "object",
              "properties": {
                "spu_cpu": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    3670632
                  ]
                },
                "spu_current_session": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    215
                  ]
                },
                "spu_max_session": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    131072
                  ]
                },
                "spu_memory": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    46
                  ]
                },
                "spu_pending_session": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    0
                  ]
                },
                "spu_uptime": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    0
                  ]
                },
                "spu_valid_session": {
                  "type": "integer",
                  "contentEncoding": "int32"
                }
              }
            },
            "description": ""
          },
          "spu_stat": {
            "type": "array",
            "items": {
              "title": "stats_gateway_spu_item",
              "type": "object",
              "properties": {
                "spu_cpu": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    3670632
                  ]
                },
                "spu_current_session": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    215
                  ]
                },
                "spu_max_session": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    131072
                  ]
                },
                "spu_memory": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    46
                  ]
                },
                "spu_pending_session": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    0
                  ]
                },
                "spu_uptime": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    0
                  ]
                },
                "spu_valid_session": {
                  "type": "integer",
                  "contentEncoding": "int32"
                }
              }
            },
            "description": ""
          },
          "status": {
            "type": "string",
            "readOnly": true,
            "examples": [
              "connected"
            ]
          },
          "tag_id": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "tag_uuid": {
            "type": "string",
            "contentEncoding": "uuid"
          },
          "tunnels": {
            "type": "array",
            "items": {
              "title": "stats_gateway_wan_tunnel",
              "type": "object",
              "properties": {
                "auth_algo": {
                  "type": "string",
                  "description": "Authentication algorithm"
                },
                "encrypt_algo": {
                  "type": "string",
                  "description": "Encryption algorithm"
                },
                "ike_version": {
                  "type": "string",
                  "description": "IKE version"
                },
                "ip": {
                  "type": "string",
                  "description": "IP Address"
                },
                "last_event": {
                  "type": "string",
                  "description": "Reason of why the tunnel is down"
                },
                "last_flapped": {
                  "type": "number",
                  "description": "Indicates when the port was last flapped"
                },
                "node": {
                  "type": "string",
                  "description": "Node0/node1"
                },
                "peer_host": {
                  "type": "string",
                  "description": "Peer host"
                },
                "peer_ip": {
                  "type": "string",
                  "description": "Peer ip address"
                },
                "priority": {
                  "type": "string",
                  "description": "enum: `primary`, `secondary`"
                },
                "protocol": {
                  "type": "string",
                  "description": "enum: `gre`, `ipsec`"
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
                "tunnel_name": {
                  "type": "string",
                  "description": "Mist Tunnel Name"
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
                },
                "uptime": {
                  "type": "integer",
                  "description": "Duration from first (or last) SA was established",
                  "contentEncoding": "int32"
                },
                "wan_name": {
                  "type": "string",
                  "description": "WAN interface name",
                  "examples": [
                    "wan"
                  ]
                }
              }
            },
            "description": "Only present when `tunnels` in `fields` query parameter. Each port object is same as `GET /api/v1/sites/{site_id}/stats/tunnels/search` result object, except that org_id, site_id, mac, model are removed"
          },
          "type": {
            "const": "gateway",
            "type": "string",
            "description": "Device Type. enum: `gateway`",
            "readOnly": true
          },
          "uptime": {
            "type": [
              "number",
              "null"
            ],
            "readOnly": true,
            "examples": [
              3671219
            ]
          },
          "version": {
            "type": [
              "string",
              "null"
            ],
            "readOnly": true,
            "examples": [
              "18.4R1.8"
            ]
          },
          "vpn_peers": {
            "type": "array",
            "items": {
              "title": "stats_gateway_vpn_peer",
              "type": "object",
              "properties": {
                "is_active": {
                  "type": "boolean",
                  "description": "Redundancy status of the associated interface"
                },
                "jitter": {
                  "minimum": 0.0,
                  "type": "number",
                  "description": "Jitter in milliseconds"
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
                "latency": {
                  "minimum": 0.0,
                  "type": "number",
                  "description": "Latency in milliseconds"
                },
                "loss": {
                  "maximum": 100.0,
                  "minimum": 0.0,
                  "type": "number",
                  "description": "Packet loss in percentage"
                },
                "mos": {
                  "maximum": 5.0,
                  "minimum": 0.0,
                  "type": "number",
                  "description": "Mean Opinion Score, a measure of the quality of the VPN link"
                },
                "mtu": {
                  "type": "integer",
                  "contentEncoding": "int32"
                },
                "peer_mac": {
                  "minLength": 1,
                  "type": "string",
                  "description": "Peer router mac address"
                },
                "peer_port_id": {
                  "minLength": 1,
                  "type": "string",
                  "description": "Peer router device interface"
                },
                "peer_router_name": {
                  "minLength": 1,
                  "type": "string"
                },
                "peer_site_id": {
                  "type": "string",
                  "contentEncoding": "uuid",
                  "readOnly": true,
                  "examples": [
                    "441a1214-6928-442a-8e92-e1d34b8ec6a6"
                  ]
                },
                "port_id": {
                  "minLength": 1,
                  "type": "string",
                  "description": "Router device interface"
                },
                "router_name": {
                  "minLength": 1,
                  "type": "string"
                },
                "type": {
                  "minLength": 1,
                  "type": "string",
                  "description": "`ipsec`for SRX, `svr` for 128T"
                },
                "up": {
                  "type": "boolean"
                },
                "uptime": {
                  "type": "integer",
                  "contentEncoding": "int32"
                }
              }
            },
            "description": "Only present when `vpn_peers` in `fields` query parameter. Each port object is same as `GET /api/v1/sites/{site_id}/stats/vpn_peers/search` result object, except that org_id, site_id, mac, model are removed"
          }
        },
        "description": "Gateway statistics"
      }
    ],
    "discriminator": {
      "propertyName": "type",
      "mapping": {
        "ap": "stats_ap",
        "gateway": "stats_gateway",
        "switch": "stats_switch"
      }
    }
  },
  "description": "",
  "examples": [
    "[{\"auto_upgrade_stat\":{\"lastcheck\":1720594762},\"ble_stat\":{\"beacon_enabled\":true,\"beacon_rate\":4,\"eddystone_uid_enabled\":false,\"eddystone_uid_freq_msec\":1000,\"eddystone_uid_instance\":\"5c5b35d0077b\",\"eddystone_uid_namespace\":\"9777c1a06ef611e68bbf\",\"eddystone_url_enabled\":false,\"eddystone_url_freq_msec\":1000,\"eddystone_url_url\":\"\",\"ibeacon_enabled\":false,\"ibeacon_freq_msec\":1000,\"ibeacon_major\":894,\"ibeacon_minor\":9328,\"ibeacon_uuid\":\"af010e2b-f829-4975-b49e-2e896ed1d627\",\"major\":894,\"minors\":[9328,9329,9330,9331,9332,9333,9334,9335,-1],\"power\":8,\"rx_bytes\":158500843,\"rx_pkts\":3549163,\"tx_bytes\":509640,\"tx_pkts\":85411,\"tx_resets\":0,\"uuid\":\"af010e2b-f829-4975-b49e-2e896ed1d627\"},\"config_reverted\":false,\"cpu_system\":21921854,\"cpu_user\":7496631,\"cpu_util\":5,\"created_time\":1718228350,\"env_stat\":{\"accel_x\":-0.092,\"accel_y\":0.004,\"accel_z\":-1.02,\"ambient_temp\":43,\"attitude\":0,\"cpu_temp\":53,\"humidity\":9,\"magne_x\":0,\"magne_y\":0,\"magne_z\":0,\"pressure\":968,\"vcore_voltage\":0},\"ext_ip\":\"66.129.234.28\",\"hw_rev\":\"C02\",\"id\":\"00000000-0000-0000-1000-5c5b35d0077b\",\"inactive_wired_vlans\":[],\"ip\":\"192.168.95.3\",\"ip_stat\":{\"dhcp_server\":\"192.168.95.1\",\"dns\":[\"8.8.8.8\"],\"gateway\":\"192.168.95.1\",\"ip\":\"192.168.95.3\",\"ip6\":\"fe80:0:0:0:5e5b:35ff:fed0:77b\",\"ips\":{\"vlan1\":\"192.168.95.3/24,fe80:0:0:0:5e5b:35ff:fed0:77b/64\"},\"netmask\":\"255.255.255.0\",\"netmask6\":\"/64\"},\"last_seen\":1720595866,\"last_trouble\":{\"code\":\"07\",\"timestamp\":1720039666},\"lldp_stat\":{\"chassis_id\":\"d0:07:ca:f5:21:00\",\"lldp_med_supported\":false,\"mgmt_addr\":\"100.123.105.1\",\"mgmt_addrs\":[\"100.123.105.1\"],\"port_desc\":\"ge-0/0/4\",\"port_id\":\"ge-0/0/4\",\"power_allocated\":0,\"power_draw\":0,\"power_request_count\":0,\"power_requested\":0,\"system_desc\":\"Juniper Networks, Inc. ex4300-48t internet router, kernel JUNOS 20.4R3-S7.2, Build date: 2023-04-21 19:47:18 UTC Copyright (c) 1996-2023 Juniper Networks, Inc.\",\"system_name\":\"Phoenix-Switch\"},\"mac\":\"5c5b35d0077b\",\"mem_total_kb\":505468,\"mem_used_kb\":202096,\"model\":\"AP43\",\"modified_time\":1718530662,\"mount\":\"faceup\",\"name\":\"Phoenix\",\"notes\":\"\",\"num_clients\":1,\"org_id\":\"af010e2b-f829-4975-b49e-2e896ed1d627\",\"port_stat\":{\"eth0\":{\"full_duplex\":true,\"rx_bytes\":1284143195,\"rx_errors\":0,\"rx_peak_bps\":17585,\"rx_pkts\":5199816,\"speed\":1000,\"tx_bytes\":1283744961,\"tx_peak_bps\":26484,\"tx_pkts\":3990463,\"up\":true},\"eth1\":{\"full_duplex\":false,\"rx_bytes\":0,\"rx_errors\":0,\"rx_peak_bps\":0,\"rx_pkts\":0,\"speed\":0,\"tx_bytes\":0,\"tx_peak_bps\":0,\"tx_pkts\":0,\"up\":false}},\"power_budget\":8400,\"power_constrained\":false,\"power_src\":\"DC Input\",\"radio_config\":{},\"radio_stat\":{\"band_24\":{\"bandwidth\":20,\"channel\":11,\"mac\":\"5c5b35dea810\",\"noise_floor\":-80,\"num_clients\":0,\"power\":17,\"rx_bytes\":12948211,\"rx_pkts\":65292,\"tx_bytes\":19071943,\"tx_pkts\":76926,\"usage\":\"24\",\"util_all\":24,\"util_non_wifi\":2,\"util_rx_in_bss\":0,\"util_rx_other_bss\":17,\"util_tx\":4,\"util_undecodable_wifi\":0,\"util_unknown_wifi\":1},\"band_5\":{\"bandwidth\":40,\"channel\":36,\"mac\":\"5c5b35dea7f0\",\"noise_floor\":-90,\"num_clients\":1,\"power\":17,\"rx_bytes\":578362619,\"rx_pkts\":2687577,\"tx_bytes\":1199571353,\"tx_pkts\":2479302,\"usage\":\"5\",\"util_all\":13,\"util_non_wifi\":0,\"util_rx_in_bss\":0,\"util_rx_other_bss\":10,\"util_tx\":1,\"util_undecodable_wifi\":0,\"util_unknown_wifi\":1}},\"rx_bps\":9276,\"rx_bytes\":591310830,\"rx_pkts\":2752869,\"serial\":\"A0703200709E6\",\"site_id\":\"46fc665e-9706-4296-8fe2-78f42f2e67e4\",\"status\":\"connected\",\"switch_redundancy\":{\"num_redundant_aps\":1},\"tx_bps\":8067,\"tx_bytes\":1218643296,\"tx_pkts\":2556228,\"type\":\"ap\",\"uptime\":1593120,\"version\":\"0.14.29313\"}]",
    "[{\"arp_table_stats\":{\"arp_table_count\":21,\"max_entries_supported\":64000},\"auto_upgrade_stat\":{\"lastcheck\":1720595477},\"cert_expiry\":1743292763,\"cluster_config\":{\"configuration\":\"active-active\",\"control_link_info\":{\"name\":\"fxp1\",\"status\":\"Up\"},\"ethernet_connection\":[{\"name\":\"reth0\",\"status\":\"Up\"},{\"name\":\"reth1\",\"status\":\"Up\"},{\"name\":\"reth2\",\"status\":\"Down\"},{\"name\":\"reth3\",\"status\":\"Down\"},{\"name\":\"reth4\",\"status\":\"Up\"}],\"fabric_link_info\":{\"DataPlaneNotifiedStatus\":\"Up\",\"Interface\":[],\"InternalStatus\":\"Up\",\"State\":\"Enabled\",\"Status\":\"Enabled\"},\"last_status_change_reason\":\"No failures\",\"operational\":\"active-active\",\"primary_node_health\":\"Healthy\",\"redundancy_group_information\":[{\"Id\":0,\"MonitoringFailure\":\"none\",\"Threshold\":255},{\"Id\":1,\"MonitoringFailure\":\"interface-monitoring\",\"Threshold\":0},{\"Id\":2,\"MonitoringFailure\":\"none\",\"Threshold\":255}],\"secondary_node_health\":\"Not healthy\",\"status\":\"Green\"},\"config_status\":\"COMMITED\",\"config_timestamp\":1720182848,\"config_version\":1720182848,\"cpu2_stat\":{\"idle\":86,\"interrupt\":0,\"load_avg\":[0.13,0.17,0.16],\"system\":5,\"user\":9},\"cpu_stat\":{\"idle\":76,\"interrupt\":0,\"load_avg\":[0.18,0.31,0.39],\"system\":10,\"user\":14},\"created_time\":1711756611,\"deviceprofile_id\":\"5e5daedf-e650-4013-b41c-845f0d2b9414\",\"deviceprofile_name\":\"wan_srx_tor_hub1\",\"dhcpd_stat\":{\"byod_dc1\":{\"num_ips\":100,\"num_leased\":0},\"corp_dc1\":{\"num_ips\":100,\"num_leased\":4},\"guest_dc1\":{\"num_ips\":241,\"num_leased\":0},\"iot_dc1\":{\"num_ips\":100,\"num_leased\":0},\"mgmt_dc1\":{\"num_ips\":100,\"num_leased\":2},\"teleworker\":{\"num_ips\":140,\"num_leased\":0}},\"ext_ip\":\"69.196.157.189\",\"fwupdate\":{\"progress\":100,\"status\":\"upgraded\",\"status_id\":3037,\"timestamp\":1718392692.580769,\"will_retry\":false},\"has_pcap\":false,\"hostname\":\"wan_srx_tor_hub1-srx\",\"id\":\"00000000-0000-0000-1000-4db14e107134\",\"if_stat\":{\"ge-0/0/5.130\":{\"address_mode\":\"Unknown\",\"nat_addresses\":[],\"network_name\":\"\",\"port_id\":\"ge-0/0/5\",\"port_usage\":\"lan\",\"rx_bytes\":0,\"rx_pkts\":0,\"tx_bytes\":0,\"tx_pkts\":0,\"up\":true,\"vlan\":0},\"ge-1/0/5.120\":{\"address_mode\":\"Unknown\",\"nat_addresses\":[],\"network_name\":\"\",\"port_id\":\"ge-1/0/5\",\"port_usage\":\"lan\",\"rx_bytes\":0,\"rx_pkts\":0,\"tx_bytes\":0,\"tx_pkts\":0,\"up\":true,\"vlan\":0}},\"ip\":\"69.196.157.190\",\"ip_stat\":{\"gateway\":\"69.196.157.185\",\"ip\":\"69.196.157.190\",\"ips\":{\"vlan1\":\"69.196.157.190,69.196.157.190\"},\"netmask\":\"255.255.255.255\"},\"is_ha\":true,\"last_seen\":1720598726,\"mac\":\"4db14e107134\",\"mac_table_stats\":{\"mac_table_count\":0,\"max_mac_entries_supported\":160000},\"memory2_stat\":{\"usage\":32},\"memory_stat\":{\"usage\":39},\"model\":\"SRX300\",\"modified_time\":1720092942,\"module2_stat\":[{\"backup_version\":\"21.2R3-S7.7\",\"fans\":[],\"last_seen\":1720598717,\"mac\":\"ec38739270c0\",\"model\":\"SRX300\",\"psus\":[{\"name\":\"Power Supply 0\",\"status\":\"ok\"}],\"recovery_version\":\"21.2R3-S7.7\",\"serial\":\"CV2218AF1505\",\"status\":\"connected\",\"temperatures\":[{\"celsius\":49,\"name\":\"Routing Engine\",\"status\":\"ok\"},{\"celsius\":64,\"name\":\"Routing Engine CPU\",\"status\":\"ok\"}],\"uptime\":580964,\"vc_links\":[{\"neighbor_module_idx\":0,\"neighbor_port_id\":\"fxp1\",\"port_id\":\"fxp1\"}],\"vc_role\":\"secondary\",\"vc_state\":\"active\",\"version\":\"21.2R3-S6.11\"}],\"module_stat\":[{\"backup_version\":\"21.2R3-S7.7\",\"fans\":[],\"last_seen\":1720598716.999985,\"mac\":\"4db14e107134\",\"model\":\"SRX300\",\"psus\":[{\"name\":\"Power Supply 0\",\"status\":\"ok\"}],\"recovery_version\":\"21.2R3-S7.7\",\"serial\":\"CV0219AN0335\",\"status\":\"connected\",\"temperatures\":[{\"celsius\":49,\"name\":\"Routing Engine\",\"status\":\"ok\"},{\"celsius\":65,\"name\":\"Routing Engine CPU\",\"status\":\"ok\"}],\"uptime\":1945193,\"vc_links\":[{\"neighbor_module_idx\":1,\"neighbor_port_id\":\"fxp1\",\"port_id\":\"fxp1\"}],\"vc_role\":\"primary\",\"vc_state\":\"active\",\"version\":\"21.2R3-S6.11\"}],\"name\":\"wan_srx_tor_hub1-srx\",\"org_id\":\"af010e2b-f829-4975-b49e-2e896ed1d627\",\"route_summary_stats\":{\"fib_routes\":0,\"max_unicast_routes_supported\":1240000,\"rib_routes\":0,\"total_routes\":0},\"serial\":\"CV0219AN0335\",\"service_stat\":{},\"service_status\":{\"appid_status\":\"enabled\",\"appid_version\":3720,\"ewf_status\":\"disabled\",\"idp_install_result\":\"successful\",\"idp_install_timestamp\":\"2024-07-10T06:29:11.708164029Z\",\"idp_status\":\"disabled\",\"idp_update_timestamp\":\"2024-07-10T06:28:28.567046244Z\"},\"site_id\":\"83c31971-ad70-4419-ae20-7f2b90748986\",\"spu2_stat\":[{\"spu_cpu\":0,\"spu_current_session\":39,\"spu_max_session\":32768,\"spu_memory\":31,\"spu_pending_session\":0,\"spu_uptime\":1944572,\"spu_valid_session\":0}],\"spu_stat\":[{\"spu_cpu\":1,\"spu_current_session\":47,\"spu_max_session\":32768,\"spu_memory\":34,\"spu_pending_session\":0,\"spu_uptime\":1944572,\"spu_valid_session\":0}],\"status\":\"connected\",\"tag_id\":3550217,\"tag_uuid\":\"af010e2b-f829-4975-b49e-2e896ed1d627\",\"type\":\"gateway\",\"uptime\":581259,\"version\":\"21.2R3-S6.11\"}]",
    "[{\"ap_redundancy\":{\"num_aps\":1,\"num_aps_with_switch_redundancy\":1},\"arp_table_stats\":{\"arp_table_count\":16,\"max_entries_supported\":32000},\"auto_upgrade_stat\":{\"lastcheck\":1720600596},\"cert_expiry\":1743932274,\"clients\":[{\"device_mac\":\"0912f561b653\",\"mac\":\"001132f5ad23\",\"port_id\":\"ge-1/0/11\"}],\"clients_stats\":{\"total\":{\"num_aps\":[0,0],\"num_wired_clients\":13}},\"config_status\":\"COMMITED\",\"config_timestamp\":1720552389,\"config_version\":1720552389,\"cpu_stat\":{\"idle\":74,\"interrupt\":0,\"load_avg\":[0.8,0.75,0.78],\"system\":13,\"user\":13},\"created_time\":1712346090,\"dhcpd_stat\":{\"ifo\":{\"num_ips\":5,\"num_leased\":0}},\"ext_ip\":\"153.142.221.41\",\"fw_versions_outofsync\":false,\"fwupdate\":{\"progress\":100,\"status\":\"upgraded\",\"status_id\":3037,\"timestamp\":1712409702.9714448,\"will_retry\":false},\"has_pcap\":true,\"hostname\":\"SW-HLAB-ea2e00\",\"hw_rev\":\"A\",\"id\":\"00000000-0000-0000-1000-0912f561b653\",\"if_stat\":{\"ge-0/0/5.0\":{\"port_id\":\"ge-0/0/5\",\"rx_bytes\":0,\"rx_pkts\":78110,\"tx_bytes\":0,\"tx_pkts\":61037,\"up\":true},\"ge-1/0/0.0\":{\"port_id\":\"ge-1/0/0\",\"rx_bytes\":0,\"rx_pkts\":56415,\"tx_bytes\":0,\"tx_pkts\":72209,\"up\":true},\"irb.172\":{\"ips\":[\"10.3.172.41/24\"],\"port_id\":\"irb\",\"rx_bytes\":0,\"rx_pkts\":1291755,\"servp_info\":{},\"tx_bytes\":0,\"tx_pkts\":990327,\"up\":true,\"vlan\":172},\"vme.0\":{\"port_id\":\"vme\",\"rx_bytes\":0,\"rx_pkts\":0,\"tx_bytes\":0,\"tx_pkts\":0,\"up\":true}},\"ip\":\"10.3.10.10\",\"ip_stat\":{\"gateway\":\"10.3.172.9\",\"ip\":\"10.3.10.10\",\"ips\":{\"vlan172\":\"10.3.172.41\"},\"netmask\":\"255.255.255.255\"},\"last_seen\":1720601189,\"last_trouble\":{\"code\":\"103\",\"timestamp\":1712412455215},\"mac\":\"0912f561b653\",\"mac_table_stats\":{\"mac_table_count\":58,\"max_mac_entries_supported\":64000},\"memory_stat\":{\"usage\":16},\"model\":\"EX4100-F-12P\",\"modified_time\":1720552388,\"module_stat\":[{\"boot_partition\":\"junos\",\"cpu_stat\":{\"idle\":74,\"interrupt\":0,\"load_avg\":[0.8,0.75,0.78],\"system\":13,\"user\":13},\"fpc_idx\":0,\"mac\":\"0912f561b653\",\"memory_stat\":{\"usage\":16},\"model\":\"EX4100-F-12P\",\"pics\":[{\"index\":0,\"model_number\":\"EX4100-F-12P\",\"port_groups\":[{\"count\":12,\"type\":\"GE\"}]},{\"index\":1,\"model_number\":\"EX4100-F-12P\",\"port_groups\":[{\"count\":4,\"type\":\"SFP/SFP+\"}]},{\"index\":2,\"model_number\":\"EX4100-F-12P\",\"port_groups\":[{\"count\":2,\"type\":\"GE\"}]}],\"poe\":{\"max_power\":180,\"power_draw\":7.3},\"psus\":[{\"name\":\"Power Supply 0\",\"status\":\"ok\"},{\"name\":\"Power Supply 1\",\"status\":\"absent\"},{\"name\":\"Power Supply 2\",\"status\":\"absent\"}],\"serial\":\"FJ0324AV0077\",\"temperatures\":[{\"celsius\":51,\"name\":\"Thermal board Sensor 1\",\"status\":\"ok\"},{\"celsius\":51,\"name\":\"Thermal board Sensor 2\",\"status\":\"ok\"},{\"celsius\":50,\"name\":\"Thermal board Sensor 3\",\"status\":\"ok\"},{\"celsius\":57,\"name\":\"PFE Die Sensor\",\"status\":\"ok\"}],\"type\":\"fpc\",\"uptime\":1692720,\"vc_links\":[{\"neighbor_module_idx\":1,\"neighbor_port_id\":\"vcp-1/1/1\",\"port_id\":\"vcp-0/1/0\"},{\"neighbor_module_idx\":1,\"neighbor_port_id\":\"vcp-1/1/0\",\"port_id\":\"vcp-0/1/1\"}],\"vc_mode\":\"HiGiG\",\"vc_role\":\"master\",\"vc_state\":\"present\",\"version\":\"22.4R3.25\"},{\"boot_partition\":\"junos\",\"cpu_stat\":{\"idle\":79,\"interrupt\":0,\"load_avg\":[0.52,0.46,0.46],\"system\":6,\"user\":15},\"fpc_idx\":1,\"mac\":\"485a0deb2380\",\"memory_stat\":{\"usage\":14},\"model\":\"EX4100-F-12P\",\"pics\":[{\"index\":0,\"model_number\":\"EX4100-F-12P\",\"port_groups\":[{\"count\":12,\"type\":\"GE\"}]},{\"index\":1,\"model_number\":\"EX4100-F-12P\",\"port_groups\":[{\"count\":4,\"type\":\"SFP/SFP+\"}]},{\"index\":2,\"model_number\":\"EX4100-F-12P\",\"port_groups\":[{\"count\":2,\"type\":\"GE\"}]}],\"poe\":{\"max_power\":180,\"power_draw\":22.1},\"psus\":[{\"name\":\"Power Supply 0\",\"status\":\"ok\"},{\"name\":\"Power Supply 1\",\"status\":\"absent\"},{\"name\":\"Power Supply 2\",\"status\":\"absent\"}],\"serial\":\"FJ0424AV0101\",\"temperatures\":[{\"celsius\":52,\"name\":\"Thermal board Sensor 1\",\"status\":\"ok\"},{\"celsius\":53,\"name\":\"Thermal board Sensor 2\",\"status\":\"ok\"},{\"celsius\":52,\"name\":\"Thermal board Sensor 3\",\"status\":\"ok\"},{\"celsius\":59,\"name\":\"PFE Die Sensor\",\"status\":\"ok\"}],\"type\":\"fpc\",\"uptime\":1692720,\"vc_links\":[{\"neighbor_module_idx\":0,\"neighbor_port_id\":\"vcp-0/1/1\",\"port_id\":\"vcp-1/1/0\"},{\"neighbor_module_idx\":0,\"neighbor_port_id\":\"vcp-0/1/0\",\"port_id\":\"vcp-1/1/1\"}],\"vc_mode\":\"HiGiG\",\"vc_role\":\"backup\",\"vc_state\":\"present\",\"version\":\"22.4R3.25\"}],\"name\":\"SW-HLAB-ea2e00\",\"org_id\":\"c5324060-19da-48fa-af28-2b530bd08765\",\"route_summary_stats\":{\"fib_routes\":7,\"max_unicast_routes_supported\":32150,\"rib_routes\":40,\"total_routes\":3},\"serial\":\"FJ0324AV0077\",\"site_id\":\"a0e43ffb-94a6-4f27-92aa-9cf832e1143d\",\"status\":\"connected\",\"tag_id\":3564806,\"tag_uuid\":\"507604a4-6b34-449c-acb3-87955430b006\",\"type\":\"switch\",\"uptime\":1692720,\"vc_mac\":\"0912f561b653\",\"vc_setup_info\":{\"config_type\":\"nonprovisioned\",\"err_missing_dev_id_fpc\":false},\"version\":\"22.4R3.25\"}]"
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

`mistapi.api.v1.sites.stats_-_devices.listSiteDevicesStats()`

## Usage Context

Retrieves device statistics for all devices at a site. The primary endpoint for device health monitoring and inventory.

## Gotchas

- By default returns only AP stats. Use `type=all` to include switches and gateways.
- Returns a large payload for sites with many devices.

## Related Endpoints

- [GET_sites_site_id_stats_devices_device_id.md](GET_sites_site_id_stats_devices_device_id.md) — Single device stats
- [GET_sites_site_id_devices.md](GET_sites_site_id_devices.md) — Device configuration list

## MistHelper Notes

Used by Menus **13, 29, 31, 32, 90, 95, 99, 112** via `listSiteDevicesStats` for device inventory, firmware management, and health monitoring.
