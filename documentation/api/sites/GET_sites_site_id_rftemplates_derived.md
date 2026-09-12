# listSiteRfTemplatesDerived

> listSiteRfTemplatesDerived

## HTTP

`GET /api/v1/sites/{site_id}/rftemplates/derived`

## Description

Get the list of derived RF Templates a Site

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
| resolve | boolean | No |  |  | Whether resolve the site variables |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "array",
  "items": {
    "title": "rf_template",
    "required": [
      "name"
    ],
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
    "description": "RF Template"
  },
  "description": "",
  "examples": [
    [
      {
        "ant_gain_24": 0,
        "ant_gain_5": 0,
        "band_24": {
          "allow_rrm_disable": true,
          "ant_gain": 0,
          "bandwidth": 20,
          "channels": [
            1,
            6,
            11
          ],
          "disabled": false,
          "power_max": 11,
          "power_min": 3,
          "preamble": "short"
        },
        "band_24_usage": "auto",
        "band_5": {
          "allow_rrm_disable": false,
          "ant_gain": 0,
          "bandwidth": 80,
          "channels": [
            36,
            40,
            44,
            48,
            52,
            56,
            60,
            64,
            100,
            104,
            149,
            153,
            157,
            161
          ],
          "disabled": false,
          "power_max": 16,
          "power_min": 9,
          "preamble": "short"
        },
        "country_code": "FR",
        "created_time": 1594743723,
        "id": "b3f20330-f76a-49f1-bc65-0d8727140b1d",
        "model_specific": {},
        "modified_time": 1613582192,
        "name": "Lab",
        "org_id": "203d3d02-dbc0-4c1b-9f41-76896a3330f4"
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

`mistapi.api.v1.sites.rf_templates.listSiteRfTemplatesDerived()`

## Usage Context

Retrieves the effective (derived/resolved) RF template for a site, merging org and site-group RF settings.

## Gotchas

- RF templates control radio channels, power, and band steering. The derived view shows what APs actually apply.

## Related Endpoints

- [../orgs/GET_orgs_org_id_rftemplates.md](../orgs/GET_orgs_org_id_rftemplates.md) — Org RF templates
- [GET_sites_site_id_setting.md](GET_sites_site_id_setting.md) — Site settings

## MistHelper Notes

Not currently used by MistHelper directly. Menu **48** uses `listOrgRfTemplates` at org level.
