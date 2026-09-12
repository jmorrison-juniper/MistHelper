# listSiteUiSettings

> listSiteUiSettings

## HTTP

`GET /api/v1/sites/{site_id}/uisettings`

## Description

List the Site UI settings/databoard

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

List of Site UI Setting

```json
{
  "type": "array",
  "items": {
    "title": "ui_settings",
    "required": [
      "description",
      "purpose"
    ],
    "type": "object",
    "properties": {
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "defaultScopeId": {
        "type": "string",
        "examples": [
          "67970e46-4e12-11e6-9188-0242ad112847"
        ]
      },
      "defaultScopeType": {
        "type": "string",
        "examples": [
          "site"
        ]
      },
      "defaultTimeRange": {
        "title": "ui_settings_default_time_range",
        "type": "object",
        "properties": {
          "end": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              1508828400
            ]
          },
          "endDate": {
            "type": "string",
            "examples": [
              "10/23/2017"
            ]
          },
          "interval": {
            "type": "string",
            "examples": [
              "1d"
            ]
          },
          "name": {
            "type": "string",
            "examples": [
              "This Week"
            ]
          },
          "shortName": {
            "type": "string",
            "examples": [
              "thisWeek"
            ]
          },
          "start": {
            "type": "integer",
            "contentEncoding": "int32",
            "examples": [
              1508655600
            ]
          },
          "usePreset": {
            "type": "boolean",
            "examples": [
              true
            ]
          }
        }
      },
      "description": {
        "type": "string",
        "examples": [
          "Description of the databoard"
        ]
      },
      "for_site": {
        "type": "boolean",
        "readOnly": true,
        "examples": [
          true
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
      "isCustomDataboard": {
        "type": "boolean"
      },
      "isScopeLinked": {
        "type": "boolean"
      },
      "isTimeRangeLinked": {
        "type": "boolean"
      },
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "name": {
        "type": "string",
        "examples": [
          "New Databoard"
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
      "purpose": {
        "type": "string",
        "examples": [
          "databoard"
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
      "tiles": {
        "uniqueItems": true,
        "type": "array",
        "items": {
          "title": "ui_settings_tile",
          "type": "object",
          "properties": {
            "chartBand": {
              "type": "string",
              "examples": [
                "2.4 ghz"
              ]
            },
            "chartColor": {
              "type": "string",
              "examples": [
                "#00B4AD"
              ]
            },
            "chartDirection": {
              "type": "string",
              "examples": [
                "tx + rx"
              ]
            },
            "chartRankBy": {
              "type": "string"
            },
            "chartType": {
              "type": "string",
              "examples": [
                "timeSeries"
              ]
            },
            "colspan": {
              "type": "integer",
              "contentEncoding": "int32",
              "examples": [
                5
              ]
            },
            "column": {
              "type": "integer",
              "contentEncoding": "int32",
              "examples": [
                1
              ]
            },
            "hideEmptyRows": {
              "type": "boolean"
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
            "metric": {
              "title": "ui_settings_tile_metric",
              "type": "object",
              "properties": {
                "apiName": {
                  "type": "string",
                  "examples": [
                    "client_dhcp_latency"
                  ]
                }
              }
            },
            "name": {
              "type": "string",
              "examples": [
                "New Analysis"
              ]
            },
            "row": {
              "type": "integer",
              "contentEncoding": "int32",
              "examples": [
                1
              ]
            },
            "rowspan": {
              "type": "integer",
              "contentEncoding": "int32",
              "examples": [
                2
              ]
            },
            "scopeId": {
              "type": "string",
              "examples": [
                "e0c767834b4c"
              ]
            },
            "scopeType": {
              "type": "string",
              "examples": [
                "client"
              ]
            },
            "sortedColumnIds": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": ""
            },
            "timeRange": {
              "title": "ui_settings_tile_time_range",
              "type": "object",
              "properties": {
                "end": {
                  "type": "number",
                  "examples": [
                    1508823743
                  ]
                },
                "endDate": {
                  "type": "string",
                  "examples": [
                    "10/23/2017"
                  ]
                },
                "interval": {
                  "type": "string",
                  "examples": [
                    "1d"
                  ]
                },
                "name": {
                  "type": "string",
                  "examples": [
                    "Past 7 Days"
                  ]
                },
                "shortName": {
                  "type": "string",
                  "examples": [
                    "7d"
                  ]
                },
                "start": {
                  "type": "integer",
                  "contentEncoding": "int32",
                  "examples": [
                    1508223600
                  ]
                },
                "usePreset": {
                  "type": "boolean",
                  "examples": [
                    true
                  ]
                }
              }
            },
            "trendType": {
              "type": "string",
              "examples": [
                "line"
              ]
            },
            "vizType": {
              "type": "string",
              "examples": [
                "averageTimeSeriesChart"
              ]
            }
          }
        },
        "description": ""
      }
    },
    "description": "UI Settings"
  },
  "description": "",
  "examples": [
    [
      {
        "created_time": 1508823803,
        "defaultScopeId": "67970e46-4e12-11e6-9188-0242ad112847",
        "defaultScopeType": "site",
        "defaultTimeRange": {
          "end": 1508828400,
          "endDate": "10/23/2017",
          "interval": "1d",
          "name": "This Week",
          "shortName": "thisWeek",
          "start": 1508655600,
          "usePreset": true
        },
        "description": "Description of the databoard",
        "for_site": true,
        "id": "3bdcc7e8-c04d-4512-b4fc-093da9057eb0",
        "isCustomDataboard": true,
        "isScopeLinked": true,
        "isTimeRangeLinked": true,
        "modified_time": 0,
        "name": "New Databoard",
        "org_id": "cc079380-5029-4d4a-9125-858de85731ff",
        "purpose": "databoard",
        "site_id": "67970e46-4e12-11e6-9188-0242ad112847",
        "tiles": [
          {
            "chartBand": "2.4 ghz",
            "chartColor": "#00B4AD",
            "chartDirection": "tx + rx",
            "chartRankBy": "string",
            "chartType": "timeSeries",
            "colspan": 5,
            "column": 1,
            "hideEmptyRows": true,
            "id": "7a9ab38c-cfc3-483d-b51a-0aec571fadc0",
            "metric": {
              "apiName": "client_dhcp_latency"
            },
            "name": "New Analysis",
            "row": 1,
            "rowspan": 2,
            "scopeId": "e0c767834b4c",
            "scopeType": "client",
            "timeRange": {
              "end": 1508823743,
              "endDate": "10/23/2017",
              "interval": "1d",
              "name": "Past 7 Days",
              "shortName": "7d",
              "start": 1508223600,
              "usePreset": true
            },
            "trendType": "line",
            "vizType": "averageTimeSeriesChart"
          }
        ]
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

`mistapi.api.v1.sites.ui_settings.listSiteUiSettings()`

## Usage Context

Lists UI settings (dashboard customizations) at a site. UI settings store user interface preferences.

## Gotchas

- UI settings are typically managed by the Mist Dashboard itself, not via direct API calls.

## Related Endpoints

- [GET_sites_site_id_uisettings_uisetting_id.md](GET_sites_site_id_uisettings_uisetting_id.md) — Get specific UI setting
- [GET_sites_site_id_uisettings_derived.md](GET_sites_site_id_uisettings_derived.md) — Derived UI settings

## MistHelper Notes

Not currently used by MistHelper directly.
