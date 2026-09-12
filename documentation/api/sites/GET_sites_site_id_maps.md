# listSiteMaps

> listSiteMaps

## HTTP

`GET /api/v1/sites/{site_id}/maps`

## Description

Get List of Site Maps

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
    "title": "map",
    "type": "object",
    "properties": {
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "flags": {
        "type": "object",
        "additionalProperties": {
          "type": "integer",
          "format": "int32"
        },
        "description": "Name/val pair objects for location engine to use",
        "readOnly": true,
        "examples": [
          {
            "assetHoldTime": 5,
            "storeTime": 10
          }
        ]
      },
      "for_site": {
        "type": "boolean",
        "readOnly": true
      },
      "geofences": {
        "type": "array",
        "items": {
          "title": "map_geofence",
          "type": "object",
          "properties": {
            "name": {
              "type": "string",
              "description": "Name of the geofence",
              "examples": [
                "example"
              ]
            },
            "vertices": {
              "type": "array",
              "items": {
                "title": "map_geofence_vertice",
                "type": "object",
                "properties": {
                  "X": {
                    "type": "number",
                    "description": "X coordinate",
                    "examples": [
                      700
                    ]
                  },
                  "Y": {
                    "type": "number",
                    "description": "Y coordinate",
                    "examples": [
                      100
                    ]
                  }
                }
              },
              "description": "List of vertices defining the geofence"
            }
          }
        },
        "description": "List of geofences for the map"
      },
      "group_idx": {
        "type": "integer",
        "description": "maps grouping, typically used for floor, optional",
        "contentEncoding": "int32",
        "examples": [
          1
        ]
      },
      "group_name": {
        "type": "string",
        "description": "maps grouping, optional",
        "examples": [
          "East Wing"
        ]
      },
      "height": {
        "type": "integer",
        "description": "When type=image, height of the image map",
        "contentEncoding": "int32",
        "examples": [
          1500
        ]
      },
      "height_m": {
        "type": "number"
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
      "latlng_br": {
        "type": "object",
        "properties": {
          "lat": {
            "type": "string"
          },
          "lng": {
            "type": "string"
          }
        },
        "description": "When type=google, latitude / longitude of the bottom-right corner"
      },
      "latlng_tl": {
        "type": "object",
        "properties": {
          "lat": {
            "type": "string"
          },
          "lng": {
            "type": "string"
          }
        },
        "description": "When type=google, latitude / longitude of the top-left corner"
      },
      "locked": {
        "type": "boolean",
        "description": "Whether this map is considered locked down",
        "default": false
      },
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "name": {
        "type": "string",
        "description": "The name of the map",
        "examples": [
          "Mist Office"
        ]
      },
      "occupancy_limit": {
        "type": "integer",
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
      "orientation": {
        "maximum": 359.0,
        "minimum": 0.0,
        "type": "integer",
        "description": "Orientation of the map, 0 means up is north, 90 means up is west",
        "contentEncoding": "int32",
        "default": 0,
        "examples": [
          30
        ]
      },
      "origin_x": {
        "type": "integer",
        "description": "User-annotated X origin, pixels",
        "contentEncoding": "int32",
        "examples": [
          35
        ]
      },
      "origin_y": {
        "type": "integer",
        "description": "User-annotated Y origin, pixels",
        "contentEncoding": "int32",
        "examples": [
          60
        ]
      },
      "ppm": {
        "type": "number",
        "description": "When type=image, pixels per meter",
        "examples": [
          40.94
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
      "sitesurvey_path": {
        "minItems": 0,
        "type": "array",
        "items": {
          "title": "map_sitesurvey_path_items",
          "type": "object",
          "properties": {
            "coordinate": {
              "type": "string",
              "examples": [
                "actual"
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
            "name": {
              "type": "string",
              "examples": [
                "Default"
              ]
            },
            "nodes": {
              "minItems": 0,
              "type": "array",
              "items": {
                "title": "map_node",
                "required": [
                  "name"
                ],
                "type": "object",
                "properties": {
                  "edges": {
                    "type": "object",
                    "additionalProperties": {
                      "type": "string"
                    },
                    "examples": [
                      {
                        "N1": "1"
                      }
                    ]
                  },
                  "name": {
                    "type": "string",
                    "examples": [
                      "N1"
                    ]
                  },
                  "position": {
                    "title": "map_node_position",
                    "required": [
                      "x",
                      "y"
                    ],
                    "type": "object",
                    "properties": {
                      "x": {
                        "type": "number",
                        "examples": [
                          746
                        ]
                      },
                      "y": {
                        "type": "number",
                        "examples": [
                          104
                        ]
                      }
                    }
                  }
                },
                "description": "Nodes on maps"
              },
              "description": ""
            }
          }
        },
        "description": "Sitesurvey_path"
      },
      "thumbnail_url": {
        "type": "string",
        "description": "When type=image, the url for the thumbnail image / preview",
        "readOnly": true,
        "examples": [
          "https://url/to/image.png"
        ]
      },
      "type": {
        "type": "string",
        "description": "enum: `google`, `image`"
      },
      "url": {
        "type": "string",
        "description": "When type=image, the url",
        "readOnly": true,
        "examples": [
          "https://url/to/image.png"
        ]
      },
      "view": {
        "type": "object",
        "description": "if `type`==`google`. enum: `hybrid`, `roadmap`, `satellite`, `terrain`"
      },
      "wall_path": {
        "type": "object",
        "properties": {
          "coordinate": {
            "type": "string",
            "examples": [
              "actual"
            ]
          },
          "nodes": {
            "minItems": 0,
            "type": "array",
            "items": {
              "title": "map_node",
              "required": [
                "name"
              ],
              "type": "object",
              "properties": {
                "edges": {
                  "type": "object",
                  "additionalProperties": {
                    "type": "string"
                  },
                  "examples": [
                    {
                      "N1": "1"
                    }
                  ]
                },
                "name": {
                  "type": "string",
                  "examples": [
                    "N1"
                  ]
                },
                "position": {
                  "title": "map_node_position",
                  "required": [
                    "x",
                    "y"
                  ],
                  "type": "object",
                  "properties": {
                    "x": {
                      "type": "number",
                      "examples": [
                        746
                      ]
                    },
                    "y": {
                      "type": "number",
                      "examples": [
                        104
                      ]
                    }
                  }
                }
              },
              "description": "Nodes on maps"
            },
            "description": ""
          }
        },
        "description": "JSON blob for wall definition (same format as wayfinding_path)"
      },
      "wayfinding": {
        "type": "object",
        "properties": {
          "micello": {
            "title": "map_wayfinding_micello",
            "type": "object",
            "properties": {
              "account_key": {
                "type": "string",
                "examples": [
                  "adasdf"
                ]
              },
              "default_level_id": {
                "type": "integer",
                "contentEncoding": "int32",
                "examples": [
                  5
                ]
              },
              "map_id": {
                "type": "string",
                "examples": [
                  "c660f81dd250c"
                ]
              }
            }
          },
          "snap_to_path": {
            "type": "boolean"
          }
        },
        "description": "Properties related to wayfinding"
      },
      "wayfinding_path": {
        "type": "object",
        "properties": {
          "coordinate": {
            "type": "string",
            "examples": [
              "actual"
            ]
          },
          "nodes": {
            "minItems": 0,
            "type": "array",
            "items": {
              "title": "map_node",
              "required": [
                "name"
              ],
              "type": "object",
              "properties": {
                "edges": {
                  "type": "object",
                  "additionalProperties": {
                    "type": "string"
                  },
                  "examples": [
                    {
                      "N1": "1"
                    }
                  ]
                },
                "name": {
                  "type": "string",
                  "examples": [
                    "N1"
                  ]
                },
                "position": {
                  "title": "map_node_position",
                  "required": [
                    "x",
                    "y"
                  ],
                  "type": "object",
                  "properties": {
                    "x": {
                      "type": "number",
                      "examples": [
                        746
                      ]
                    },
                    "y": {
                      "type": "number",
                      "examples": [
                        104
                      ]
                    }
                  }
                }
              },
              "description": "Nodes on maps"
            },
            "description": ""
          }
        },
        "description": "JSON blob for wayfinding (using Dijkstra\u2019s algorithm)"
      },
      "width": {
        "type": "integer",
        "description": "When type=image, width of the image map",
        "contentEncoding": "int32",
        "examples": [
          1250
        ]
      },
      "width_m": {
        "type": "number"
      }
    },
    "description": "Map"
  },
  "description": ""
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

`mistapi.api.v1.sites.maps.listSiteMaps()`

## Usage Context

Lists all maps (floor plans) at a site. Returns map names, dimensions, coordinates, and image references.

## Gotchas

- Maps without uploaded images still appear in the list but have no visual reference.
- Large sites may have many maps; consider pagination.

## Related Endpoints

- [GET_sites_site_id_maps_map_id.md](GET_sites_site_id_maps_map_id.md) — Get specific map
- [POST_sites_site_id_maps.md](POST_sites_site_id_maps.md) — Create map
- [GET_sites_site_id_mapstacks.md](GET_sites_site_id_mapstacks.md) — Map stacks (multi-floor)

## MistHelper Notes

Used by Menu **51** and Menu **112** (`MapsManagerLauncher`) via `listSiteMaps`.
