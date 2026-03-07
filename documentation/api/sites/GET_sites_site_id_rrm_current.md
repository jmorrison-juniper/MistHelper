# getSiteCurrentChannelPlanning

> getSiteCurrentChannelPlanning

## HTTP

`GET /api/v1/sites/{site_id}/rrm/current`

## Description

Get Current Channel Planning

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "band_24": {
      "type": "object",
      "additionalProperties": {
        "title": "rrm_band",
        "type": "object",
        "properties": {
          "bandwidth": {
            "type": "integer",
            "description": "channel width for the band.enum: `0`(disabled, response only), `20`, `40`, `80` (only applicable for band_5 and band_6), `160` (only for band_6)"
          },
          "channel": {
            "type": "integer",
            "description": "proposed channel",
            "contentEncoding": "int32"
          },
          "curr_bandwidth": {
            "type": "integer",
            "description": "channel width for the band.enum: `0`(disabled, response only), `20`, `40`, `80` (only applicable for band_5 and band_6), `160` (only for band_6)"
          },
          "curr_channel": {
            "type": "integer",
            "description": "Current channel",
            "contentEncoding": "int32"
          },
          "curr_power": {
            "type": "integer",
            "description": "Current tx power",
            "contentEncoding": "int32"
          },
          "curr_usage": {
            "minLength": 1,
            "type": "string",
            "description": "Current radio band"
          },
          "power": {
            "type": "integer",
            "description": "proposed tx power",
            "contentEncoding": "int32"
          },
          "usage": {
            "minLength": 1,
            "type": "string",
            "description": "proposed radio band"
          }
        }
      },
      "description": "proposal on band 2.4G, key is ap_id, value is the proposal"
    },
    "band_24_metric": {
      "title": "rrm_band_metric",
      "required": [
        "cochannel_neighbors",
        "density",
        "neighbors",
        "noise"
      ],
      "type": "object",
      "properties": {
        "avg_aps_per_channel": {
          "type": "number",
          "description": "Average number of APs per channel"
        },
        "channel_distribution_uniformity": {
          "type": "number",
          "description": "Distribution of channel across the Access Points"
        },
        "cochannel_neighbors": {
          "type": "number",
          "description": "Average number of co-channel neighbors"
        },
        "density": {
          "maximum": 1.0,
          "minimum": 0.0,
          "type": "number",
          "description": "defined by how APs can hear from one and another, 0 - 1 (everyone can hear everyone)"
        },
        "interferences": {
          "type": "object",
          "additionalProperties": {
            "title": "rrm_band_metric_interference",
            "type": "object",
            "properties": {
              "radar": {
                "type": "number"
              }
            }
          },
          "description": "Property key is the channel number",
          "examples": [
            {
              "149": {
                "radar": 0.3
              },
              "153": {
                "radar": 0.2
              }
            }
          ]
        },
        "naps_by_channel": {
          "type": "object",
          "additionalProperties": {
            "type": "number"
          },
          "description": "Property key is the channel number, value is number of APs on that channel"
        },
        "naps_by_power": {
          "type": "object",
          "additionalProperties": {
            "type": "number"
          },
          "description": "Property key is the power level, value is number of APs on that power level"
        },
        "neighbors": {
          "type": "number",
          "description": "Average number of neighbors"
        },
        "noise": {
          "type": "number",
          "description": "Average noise in dBm"
        }
      }
    },
    "band_5": {
      "type": "object",
      "additionalProperties": {
        "title": "rrm_band",
        "type": "object",
        "properties": {
          "bandwidth": {
            "type": "integer",
            "description": "channel width for the band.enum: `0`(disabled, response only), `20`, `40`, `80` (only applicable for band_5 and band_6), `160` (only for band_6)"
          },
          "channel": {
            "type": "integer",
            "description": "proposed channel",
            "contentEncoding": "int32"
          },
          "curr_bandwidth": {
            "type": "integer",
            "description": "channel width for the band.enum: `0`(disabled, response only), `20`, `40`, `80` (only applicable for band_5 and band_6), `160` (only for band_6)"
          },
          "curr_channel": {
            "type": "integer",
            "description": "Current channel",
            "contentEncoding": "int32"
          },
          "curr_power": {
            "type": "integer",
            "description": "Current tx power",
            "contentEncoding": "int32"
          },
          "curr_usage": {
            "minLength": 1,
            "type": "string",
            "description": "Current radio band"
          },
          "power": {
            "type": "integer",
            "description": "proposed tx power",
            "contentEncoding": "int32"
          },
          "usage": {
            "minLength": 1,
            "type": "string",
            "description": "proposed radio band"
          }
        }
      },
      "description": "proposal on band 5G, key is ap_id, value is the proposal"
    },
    "band_5_metric": {
      "title": "rrm_band_metric",
      "required": [
        "cochannel_neighbors",
        "density",
        "neighbors",
        "noise"
      ],
      "type": "object",
      "properties": {
        "avg_aps_per_channel": {
          "type": "number",
          "description": "Average number of APs per channel"
        },
        "channel_distribution_uniformity": {
          "type": "number",
          "description": "Distribution of channel across the Access Points"
        },
        "cochannel_neighbors": {
          "type": "number",
          "description": "Average number of co-channel neighbors"
        },
        "density": {
          "maximum": 1.0,
          "minimum": 0.0,
          "type": "number",
          "description": "defined by how APs can hear from one and another, 0 - 1 (everyone can hear everyone)"
        },
        "interferences": {
          "type": "object",
          "additionalProperties": {
            "title": "rrm_band_metric_interference",
            "type": "object",
            "properties": {
              "radar": {
                "type": "number"
              }
            }
          },
          "description": "Property key is the channel number",
          "examples": [
            {
              "149": {
                "radar": 0.3
              },
              "153": {
                "radar": 0.2
              }
            }
          ]
        },
        "naps_by_channel": {
          "type": "object",
          "additionalProperties": {
            "type": "number"
          },
          "description": "Property key is the channel number, value is number of APs on that channel"
        },
        "naps_by_power": {
          "type": "object",
          "additionalProperties": {
            "type": "number"
          },
          "description": "Property key is the power level, value is number of APs on that power level"
        },
        "neighbors": {
          "type": "number",
          "description": "Average number of neighbors"
        },
        "noise": {
          "type": "number",
          "description": "Average noise in dBm"
        }
      }
    },
    "band_6": {
      "type": "object",
      "additionalProperties": {
        "title": "rrm_band",
        "type": "object",
        "properties": {
          "bandwidth": {
            "type": "integer",
            "description": "channel width for the band.enum: `0`(disabled, response only), `20`, `40`, `80` (only applicable for band_5 and band_6), `160` (only for band_6)"
          },
          "channel": {
            "type": "integer",
            "description": "proposed channel",
            "contentEncoding": "int32"
          },
          "curr_bandwidth": {
            "type": "integer",
            "description": "channel width for the band.enum: `0`(disabled, response only), `20`, `40`, `80` (only applicable for band_5 and band_6), `160` (only for band_6)"
          },
          "curr_channel": {
            "type": "integer",
            "description": "Current channel",
            "contentEncoding": "int32"
          },
          "curr_power": {
            "type": "integer",
            "description": "Current tx power",
            "contentEncoding": "int32"
          },
          "curr_usage": {
            "minLength": 1,
            "type": "string",
            "description": "Current radio band"
          },
          "power": {
            "type": "integer",
            "description": "proposed tx power",
            "contentEncoding": "int32"
          },
          "usage": {
            "minLength": 1,
            "type": "string",
            "description": "proposed radio band"
          }
        }
      },
      "description": "proposal on band 6G, key is ap_id, value is the proposal"
    },
    "band_6_metric": {
      "title": "rrm_band_metric",
      "required": [
        "cochannel_neighbors",
        "density",
        "neighbors",
        "noise"
      ],
      "type": "object",
      "properties": {
        "avg_aps_per_channel": {
          "type": "number",
          "description": "Average number of APs per channel"
        },
        "channel_distribution_uniformity": {
          "type": "number",
          "description": "Distribution of channel across the Access Points"
        },
        "cochannel_neighbors": {
          "type": "number",
          "description": "Average number of co-channel neighbors"
        },
        "density": {
          "maximum": 1.0,
          "minimum": 0.0,
          "type": "number",
          "description": "defined by how APs can hear from one and another, 0 - 1 (everyone can hear everyone)"
        },
        "interferences": {
          "type": "object",
          "additionalProperties": {
            "title": "rrm_band_metric_interference",
            "type": "object",
            "properties": {
              "radar": {
                "type": "number"
              }
            }
          },
          "description": "Property key is the channel number",
          "examples": [
            {
              "149": {
                "radar": 0.3
              },
              "153": {
                "radar": 0.2
              }
            }
          ]
        },
        "naps_by_channel": {
          "type": "object",
          "additionalProperties": {
            "type": "number"
          },
          "description": "Property key is the channel number, value is number of APs on that channel"
        },
        "naps_by_power": {
          "type": "object",
          "additionalProperties": {
            "type": "number"
          },
          "description": "Property key is the power level, value is number of APs on that power level"
        },
        "neighbors": {
          "type": "number",
          "description": "Average number of neighbors"
        },
        "noise": {
          "type": "number",
          "description": "Average noise in dBm"
        }
      }
    },
    "rftemplate": {
      "type": "object",
      "properties": {
        "ant_gain_24": {
          "type": "integer",
          "contentEncoding": "int32"
        },
        "ant_gain_5": {
          "type": "integer",
          "contentEncoding": "int32"
        },
        "ant_gain_6": {
          "type": "integer",
          "contentEncoding": "int32"
        },
        "band_24": {
          "type": "object",
          "properties": {
            "allow_rrm_disable": {
              "type": "boolean",
              "default": false
            },
            "ant_gain": {
              "maximum": 10.0,
              "minimum": 0.0,
              "type": [
                "integer",
                "null"
              ],
              "contentEncoding": "int32",
              "default": 0
            },
            "antenna_mode": {
              "type": "string",
              "description": "enum: `1x1`, `2x2`, `3x3`, `4x4`, `default`"
            },
            "bandwidth": {
              "type": "integer",
              "description": "channel width for the 2.4GHz band. enum: `0`(disabled, response only), `20`, `40`"
            },
            "channels": {
              "type": [
                "array",
                "null"
              ],
              "items": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "description": "For RFTemplates. List of channels, null or empty array means auto",
              "default": []
            },
            "disabled": {
              "type": "boolean",
              "description": "Whether to disable the radio",
              "default": false
            },
            "power": {
              "maximum": 25.0,
              "minimum": 3.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "tx power of the radio, null or 0 means auto, when power_min=power_max=power=0 to indicate power=0",
              "contentEncoding": "int32",
              "examples": [
                3
              ]
            },
            "power_max": {
              "maximum": 18.0,
              "minimum": 3.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "When power=0, max tx power to use, HW-specific values will be used if not set",
              "contentEncoding": "int32",
              "default": 17
            },
            "power_min": {
              "maximum": 18.0,
              "minimum": 3.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "When power=0, min tx power to use, HW-specific values will be used if not set",
              "contentEncoding": "int32",
              "default": 8
            },
            "preamble": {
              "type": "string",
              "description": "enum: `auto`, `long`, `short`"
            }
          },
          "description": "Radio Band AP settings"
        },
        "band_24_usage": {
          "type": "string",
          "description": "enum: `24`, `5`, `6`, `auto`"
        },
        "band_5": {
          "type": "object",
          "properties": {
            "allow_rrm_disable": {
              "type": "boolean",
              "default": false
            },
            "ant_gain": {
              "maximum": 10.0,
              "minimum": 0.0,
              "type": [
                "integer",
                "null"
              ],
              "contentEncoding": "int32",
              "default": 0
            },
            "antenna_mode": {
              "type": "string",
              "description": "enum: `1x1`, `2x2`, `3x3`, `4x4`, `default`"
            },
            "bandwidth": {
              "type": "integer",
              "description": "channel width for the 5GHz band. enum: `0`(disabled, response only), `20`, `40`, `80`"
            },
            "channels": {
              "type": [
                "array",
                "null"
              ],
              "items": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "description": "For RFTemplates. List of channels, null or empty array means auto",
              "default": []
            },
            "disabled": {
              "type": "boolean",
              "description": "Whether to disable the radio",
              "default": false
            },
            "power": {
              "maximum": 25.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "Tx power of the radio. For Devices, 0 means auto. -1 / -2 / -3 / \u2026: treated as 0 / -1 / -2 / \u2026",
              "contentEncoding": "int32",
              "examples": [
                6
              ]
            },
            "power_max": {
              "maximum": 17.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "When power=0, max tx power to use, HW-specific values will be used if not set",
              "contentEncoding": "int32",
              "default": 17
            },
            "power_min": {
              "maximum": 17.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "When power=0, min tx power to use, HW-specific values will be used if not set",
              "contentEncoding": "int32",
              "default": 8
            },
            "preamble": {
              "type": "string",
              "description": "enum: `auto`, `long`, `short`"
            }
          },
          "description": "Radio Band AP settings"
        },
        "band_5_on_24_radio": {
          "type": "object",
          "properties": {
            "allow_rrm_disable": {
              "type": "boolean",
              "default": false
            },
            "ant_gain": {
              "maximum": 10.0,
              "minimum": 0.0,
              "type": [
                "integer",
                "null"
              ],
              "contentEncoding": "int32",
              "default": 0
            },
            "antenna_mode": {
              "type": "string",
              "description": "enum: `1x1`, `2x2`, `3x3`, `4x4`, `default`"
            },
            "bandwidth": {
              "type": "integer",
              "description": "channel width for the 5GHz band. enum: `0`(disabled, response only), `20`, `40`, `80`"
            },
            "channels": {
              "type": [
                "array",
                "null"
              ],
              "items": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "description": "For RFTemplates. List of channels, null or empty array means auto",
              "default": []
            },
            "disabled": {
              "type": "boolean",
              "description": "Whether to disable the radio",
              "default": false
            },
            "power": {
              "maximum": 25.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "Tx power of the radio. For Devices, 0 means auto. -1 / -2 / -3 / \u2026: treated as 0 / -1 / -2 / \u2026",
              "contentEncoding": "int32",
              "examples": [
                6
              ]
            },
            "power_max": {
              "maximum": 17.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "When power=0, max tx power to use, HW-specific values will be used if not set",
              "contentEncoding": "int32",
              "default": 17
            },
            "power_min": {
              "maximum": 17.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "When power=0, min tx power to use, HW-specific values will be used if not set",
              "contentEncoding": "int32",
              "default": 8
            },
            "preamble": {
              "type": "string",
              "description": "enum: `auto`, `long`, `short`"
            }
          },
          "description": "Radio Band AP settings"
        },
        "band_6": {
          "type": "object",
          "properties": {
            "allow_rrm_disable": {
              "type": "boolean",
              "default": false
            },
            "ant_gain": {
              "maximum": 10.0,
              "minimum": 0.0,
              "type": [
                "integer",
                "null"
              ],
              "contentEncoding": "int32",
              "default": 0
            },
            "antenna_mode": {
              "type": "string",
              "description": "enum: `1x1`, `2x2`, `3x3`, `4x4`, `default`"
            },
            "bandwidth": {
              "type": "integer",
              "description": "channel width for the 6GHz band. enum: `0`(disabled, response only), `20`, `40`, `80`, `160`"
            },
            "channels": {
              "type": [
                "array",
                "null"
              ],
              "items": {
                "type": "integer",
                "contentEncoding": "int32"
              },
              "description": "For RFTemplates. List of channels, null or empty array means auto",
              "default": []
            },
            "disabled": {
              "type": "boolean",
              "description": "Whether to disable the radio",
              "default": false
            },
            "power": {
              "maximum": 25.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "Tx power of the radio. For Devices, 0 means auto. -1 / -2 / -3 / \u2026: treated as 0 / -1 / -2 / \u2026",
              "contentEncoding": "int32",
              "examples": [
                7
              ]
            },
            "power_max": {
              "maximum": 18.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "When power=0, max tx power to use, HW-specific values will be used if not set",
              "contentEncoding": "int32",
              "default": 18
            },
            "power_min": {
              "maximum": 18.0,
              "minimum": 5.0,
              "type": [
                "integer",
                "null"
              ],
              "description": "When power=0, min tx power to use, HW-specific values will be used if not set",
              "contentEncoding": "int32",
              "default": 8
            },
            "preamble": {
              "type": "string",
              "description": "enum: `auto`, `long`, `short`"
            },
            "standard_power": {
              "type": "boolean",
              "description": "For 6GHz Only, standard-power operation, AFC (Automatic Frequency Coordination) will be performed, and we'll fall back to Low Power Indoor if AFC failed",
              "default": false
            }
          },
          "description": "Radio Band AP settings"
        },
        "country_code": {
          "type": "string",
          "description": "Optional, country code to use. If specified, this gets applied to all sites using the RF Template"
        },
        "created_time": {
          "type": "number",
          "description": "When the object has been created, in epoch",
          "readOnly": true
        },
        "for_site": {
          "type": "boolean",
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
        "model_specific": {
          "type": "object",
          "additionalProperties": {
            "title": "rf_template_model_specific_property",
            "type": "object",
            "properties": {
              "ant_gain_24": {
                "type": "integer",
                "contentEncoding": "int32",
                "default": 0
              },
              "ant_gain_5": {
                "type": "integer",
                "contentEncoding": "int32",
                "default": 0
              },
              "ant_gain_6": {
                "type": "integer",
                "contentEncoding": "int32",
                "default": 0
              },
              "band_24": {
                "type": "object",
                "properties": {
                  "allow_rrm_disable": {
                    "type": "boolean",
                    "default": false
                  },
                  "ant_gain": {
                    "maximum": 10.0,
                    "minimum": 0.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "default": 0
                  },
                  "antenna_mode": {
                    "type": "string",
                    "description": "enum: `1x1`, `2x2`, `3x3`, `4x4`, `default`"
                  },
                  "bandwidth": {
                    "type": "integer",
                    "description": "channel width for the 2.4GHz band. enum: `0`(disabled, response only), `20`, `40`"
                  },
                  "channels": {
                    "type": [
                      "array",
                      "null"
                    ],
                    "items": {
                      "type": "integer",
                      "contentEncoding": "int32"
                    },
                    "description": "For RFTemplates. List of channels, null or empty array means auto",
                    "default": []
                  },
                  "disabled": {
                    "type": "boolean",
                    "description": "Whether to disable the radio",
                    "default": false
                  },
                  "power": {
                    "maximum": 25.0,
                    "minimum": 3.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "tx power of the radio, null or 0 means auto, when power_min=power_max=power=0 to indicate power=0",
                    "contentEncoding": "int32",
                    "examples": [
                      3
                    ]
                  },
                  "power_max": {
                    "maximum": 18.0,
                    "minimum": 3.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "When power=0, max tx power to use, HW-specific values will be used if not set",
                    "contentEncoding": "int32",
                    "default": 17
                  },
                  "power_min": {
                    "maximum": 18.0,
                    "minimum": 3.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "When power=0, min tx power to use, HW-specific values will be used if not set",
                    "contentEncoding": "int32",
                    "default": 8
                  },
                  "preamble": {
                    "type": "string",
                    "description": "enum: `auto`, `long`, `short`"
                  }
                },
                "description": "Radio Band AP settings"
              },
              "band_24_usage": {
                "type": "string",
                "description": "enum: `24`, `5`, `6`, `auto`"
              },
              "band_5": {
                "type": "object",
                "properties": {
                  "allow_rrm_disable": {
                    "type": "boolean",
                    "default": false
                  },
                  "ant_gain": {
                    "maximum": 10.0,
                    "minimum": 0.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "default": 0
                  },
                  "antenna_mode": {
                    "type": "string",
                    "description": "enum: `1x1`, `2x2`, `3x3`, `4x4`, `default`"
                  },
                  "bandwidth": {
                    "type": "integer",
                    "description": "channel width for the 5GHz band. enum: `0`(disabled, response only), `20`, `40`, `80`"
                  },
                  "channels": {
                    "type": [
                      "array",
                      "null"
                    ],
                    "items": {
                      "type": "integer",
                      "contentEncoding": "int32"
                    },
                    "description": "For RFTemplates. List of channels, null or empty array means auto",
                    "default": []
                  },
                  "disabled": {
                    "type": "boolean",
                    "description": "Whether to disable the radio",
                    "default": false
                  },
                  "power": {
                    "maximum": 25.0,
                    "minimum": 5.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Tx power of the radio. For Devices, 0 means auto. -1 / -2 / -3 / \u2026: treated as 0 / -1 / -2 / \u2026",
                    "contentEncoding": "int32",
                    "examples": [
                      6
                    ]
                  },
                  "power_max": {
                    "maximum": 17.0,
                    "minimum": 5.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "When power=0, max tx power to use, HW-specific values will be used if not set",
                    "contentEncoding": "int32",
                    "default": 17
                  },
                  "power_min": {
                    "maximum": 17.0,
                    "minimum": 5.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "When power=0, min tx power to use, HW-specific values will be used if not set",
                    "contentEncoding": "int32",
                    "default": 8
                  },
                  "preamble": {
                    "type": "string",
                    "description": "enum: `auto`, `long`, `short`"
                  }
                },
                "description": "Radio Band AP settings"
              },
              "band_5_on_24_radio": {
                "type": "object",
                "properties": {
                  "allow_rrm_disable": {
                    "type": "boolean",
                    "default": false
                  },
                  "ant_gain": {
                    "maximum": 10.0,
                    "minimum": 0.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "default": 0
                  },
                  "antenna_mode": {
                    "type": "string",
                    "description": "enum: `1x1`, `2x2`, `3x3`, `4x4`, `default`"
                  },
                  "bandwidth": {
                    "type": "integer",
                    "description": "channel width for the 5GHz band. enum: `0`(disabled, response only), `20`, `40`, `80`"
                  },
                  "channels": {
                    "type": [
                      "array",
                      "null"
                    ],
                    "items": {
                      "type": "integer",
                      "contentEncoding": "int32"
                    },
                    "description": "For RFTemplates. List of channels, null or empty array means auto",
                    "default": []
                  },
                  "disabled": {
                    "type": "boolean",
                    "description": "Whether to disable the radio",
                    "default": false
                  },
                  "power": {
                    "maximum": 25.0,
                    "minimum": 5.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Tx power of the radio. For Devices, 0 means auto. -1 / -2 / -3 / \u2026: treated as 0 / -1 / -2 / \u2026",
                    "contentEncoding": "int32",
                    "examples": [
                      6
                    ]
                  },
                  "power_max": {
                    "maximum": 17.0,
                    "minimum": 5.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "When power=0, max tx power to use, HW-specific values will be used if not set",
                    "contentEncoding": "int32",
                    "default": 17
                  },
                  "power_min": {
                    "maximum": 17.0,
                    "minimum": 5.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "When power=0, min tx power to use, HW-specific values will be used if not set",
                    "contentEncoding": "int32",
                    "default": 8
                  },
                  "preamble": {
                    "type": "string",
                    "description": "enum: `auto`, `long`, `short`"
                  }
                },
                "description": "Radio Band AP settings"
              },
              "band_6": {
                "type": "object",
                "properties": {
                  "allow_rrm_disable": {
                    "type": "boolean",
                    "default": false
                  },
                  "ant_gain": {
                    "maximum": 10.0,
                    "minimum": 0.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "contentEncoding": "int32",
                    "default": 0
                  },
                  "antenna_mode": {
                    "type": "string",
                    "description": "enum: `1x1`, `2x2`, `3x3`, `4x4`, `default`"
                  },
                  "bandwidth": {
                    "type": "integer",
                    "description": "channel width for the 6GHz band. enum: `0`(disabled, response only), `20`, `40`, `80`, `160`"
                  },
                  "channels": {
                    "type": [
                      "array",
                      "null"
                    ],
                    "items": {
                      "type": "integer",
                      "contentEncoding": "int32"
                    },
                    "description": "For RFTemplates. List of channels, null or empty array means auto",
                    "default": []
                  },
                  "disabled": {
                    "type": "boolean",
                    "description": "Whether to disable the radio",
                    "default": false
                  },
                  "power": {
                    "maximum": 25.0,
                    "minimum": 5.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "Tx power of the radio. For Devices, 0 means auto. -1 / -2 / -3 / \u2026: treated as 0 / -1 / -2 / \u2026",
                    "contentEncoding": "int32",
                    "examples": [
                      7
                    ]
                  },
                  "power_max": {
                    "maximum": 18.0,
                    "minimum": 5.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "When power=0, max tx power to use, HW-specific values will be used if not set",
                    "contentEncoding": "int32",
                    "default": 18
                  },
                  "power_min": {
                    "maximum": 18.0,
                    "minimum": 5.0,
                    "type": [
                      "integer",
                      "null"
                    ],
                    "description": "When power=0, min tx power to use, HW-specific values will be used if not set",
                    "contentEncoding": "int32",
                    "default": 8
                  },
                  "preamble": {
                    "type": "string",
                    "description": "enum: `auto`, `long`, `short`"
                  },
                  "standard_power": {
                    "type": "boolean",
                    "description": "For 6GHz Only, standard-power operation, AFC (Automatic Frequency Coordination) will be performed, and we'll fall back to Low Power Indoor if AFC failed",
                    "default": false
                  }
                },
                "description": "Radio Band AP settings"
              }
            }
          },
          "description": "overwrites for a specific model. If a band is specified, it will shadow the default. Property key is the model name (e.g. \"AP63\")"
        },
        "modified_time": {
          "type": "number",
          "description": "When the object has been modified for the last time, in epoch",
          "readOnly": true
        },
        "name": {
          "type": "string",
          "description": "The name of the RF template"
        },
        "org_id": {
          "type": "string",
          "contentEncoding": "uuid",
          "readOnly": true,
          "examples": [
            "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
          ]
        },
        "scanning_enabled": {
          "type": "boolean",
          "description": "Whether scanning radio is enabled"
        }
      },
      "required": [
        "name"
      ],
      "description": "RF Template"
    },
    "rftemplate_id": {
      "type": "string",
      "contentEncoding": "uuid"
    },
    "rftemplate_name": {
      "type": "string"
    },
    "status": {
      "type": "string",
      "description": "enum: `ready`, `unknown`, `updating`"
    },
    "timestamp": {
      "type": "number",
      "description": "Epoch (seconds)",
      "readOnly": true
    }
  },
  "required": [
    "band_24",
    "band_24_metric",
    "band_5",
    "band_5_metric",
    "rftemplate",
    "rftemplate_id",
    "rftemplate_name",
    "status",
    "timestamp"
  ],
  "description": "RRM"
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

`mistapi.api.v1.sites.rrm.getSiteCurrentChannelPlanning()`

## Usage Context

Retrieves the current RRM (Radio Resource Management) state for a site, including channel and power assignments for all APs.

## Gotchas

- RRM data is a snapshot. Channel/power values may change with each RRM optimization cycle.

## Related Endpoints

- [GET_sites_site_id_rrm_events.md](GET_sites_site_id_rrm_events.md) — RRM change events
- [GET_sites_site_id_rrm_neighbors.md](GET_sites_site_id_rrm_neighbors.md) — RF neighbor data

## MistHelper Notes

Not currently used by MistHelper directly.
