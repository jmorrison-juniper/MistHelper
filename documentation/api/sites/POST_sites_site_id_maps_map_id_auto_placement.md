# runSiteApAutoplacement

> runSiteApAutoplacement

## HTTP

`POST /api/v1/sites/{site_id}/maps/{map_id}/auto_placement`

## Description

This API is called to trigger auto placement for a map. For the auto placement feature to work, RTT-FTM data needs to be collected from the APs on the map.  
This scan is disruptive, and users must be notified of service disruption during the auto placement process. Repeated POST requests to this endpoint while a map is still running will be rejected.


`force_collection` is set to `false` by default. If `force_collection` is set to `false`, the API attempts to start localization with existing data. If no data exists, the API attempts to start orchestration.  
If `force_collection` is set to `true`, the API attempts to start orchestration.


Providing a list of devices is optional. If provided, autoplacement suggestions will be made only for the specified devices. If no list is provided, all APs associated with the map are considered by default.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| map_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "title": "auto_placement",
  "type": "object",
  "properties": {
    "dryrun": {
      "type": "boolean",
      "description": "Set to `true` to perform an invalid AP check and provide an estimated run time without enqueuing the run into the auto placement service.",
      "default": false
    },
    "force_collection": {
      "type": "boolean",
      "description": "* If `force_collection`==`false`: the API attempts to start localization with existing data. \n* If `force_collection`==`true`: maintenance the API attempts to start orchestration.",
      "default": false
    },
    "macs": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of device macs"
    },
    "override": {
      "type": "boolean",
      "description": "Set to `true` to run auto placement even if there are invalid APs in the selected APs.",
      "default": false
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
    "devices": {
      "type": "object",
      "additionalProperties": {
        "title": "response_autoplacement_device",
        "type": "object",
        "properties": {
          "reason": {
            "type": "string",
            "description": "Provides the reason for the status if the AP is invalid.",
            "readOnly": true
          },
          "valid": {
            "type": "boolean",
            "description": "Indicates whether the ap is valid.",
            "readOnly": true
          }
        }
      },
      "description": "Property key is the AP MAC Address. Contains the validation status of each device.",
      "readOnly": true
    },
    "estimated_runtime": {
      "type": "integer",
      "description": "Estimated runtime for the process in seconds.",
      "contentEncoding": "int32",
      "readOnly": true
    },
    "reason": {
      "type": "string",
      "description": "Provides the reason for the status.",
      "readOnly": true
    },
    "started": {
      "type": "boolean",
      "description": "Indicates whether the autoplacement process has started.",
      "readOnly": true
    },
    "valid": {
      "type": "boolean",
      "description": "Indicates whether the autoplacement request is valid.",
      "readOnly": true
    },
    "wifi_interrupting": {
      "type": "boolean",
      "description": "Indicates whether the auto placement process will interrupt WiFi traffic."
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

`mistapi.api.v1.sites.maps_-_auto-placement.runSiteApAutoplacement()`

## Usage Context

Triggers auto-placement of APs on the floor plan based on RF fingerprinting data.

## Gotchas

- Requires APs to be powered on and reporting. Placement accuracy depends on AP density.

## Related Endpoints

- [GET_sites_site_id_maps_map_id_auto_placement.md](GET_sites_site_id_maps_map_id_auto_placement.md) — Get placement results
- [POST_sites_site_id_maps_map_id_clear_autoplacement.md](POST_sites_site_id_maps_map_id_clear_autoplacement.md) — Clear placement

## MistHelper Notes

Not currently used by MistHelper directly.
