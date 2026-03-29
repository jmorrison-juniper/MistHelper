# startSiteApAutoOrientation

> startSiteApAutoOrientation

## HTTP

`POST /api/v1/sites/{site_id}/maps/{map_id}/auto_orient`

## Description

This API is called to trigger a map for auto orient. For auto orient feature to work, BLE data needs to be collected from the APs on the map. This precess is not disruptive unlike FTM collection. Repeated POST requests to this endpoint while a map is still running will be rejected.


`force_collection` is set to `false` by default. If `force_collection`==`false`, the API attempts to start orientation with existing data. If no data exists, the API attempts to start collecting orientation data. If `force_collection`==`true`, the API attempts to start collecting orientation data.


Providing a list of device macs is optional. If provided, auto orientation suggestions will be made only for the specified devices. If no list is provided, all APs associated with the map are considered by default.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| map_id | string | Yes |  |
| site_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "title": "auto_orient",
  "type": "object",
  "properties": {
    "dryrun": {
      "type": "boolean",
      "description": "Set to `true` to perform an invalid AP check and provide an estimated run time without enqueuing the run into the auto orient service."
    },
    "force_collection": {
      "type": "boolean",
      "description": "If `force_collection`==`false`, the API attempts to start auto orientation with existing BLE data. \nIf `force_collection`==`true`, the API attempts to start BLE orchestration.",
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
      "description": "Set to `true` to run auto orient even if there are invalid APs in the selected APs."
    }
  }
}
```

## Response

### 200

Map queued for auto orientation

```json
{
  "type": "object",
  "properties": {
    "devices": {
      "type": "object",
      "additionalProperties": {
        "title": "response_auto_orientation_device",
        "type": "object",
        "properties": {
          "reason": {
            "type": "string",
            "description": "Provides the reason for the status if the AP is invalid."
          },
          "valid": {
            "type": "boolean",
            "description": "Indicates whether the auto orient request is valid for the device."
          }
        }
      },
      "description": "Contains the validation status of each device. The Property Key is the device MAC Address."
    },
    "estimated_runtime": {
      "type": "integer",
      "description": "Estimated runtime for the process in seconds",
      "contentEncoding": "int32"
    },
    "reason": {
      "type": "string",
      "description": "Provides the reason for the status."
    },
    "started": {
      "type": "boolean",
      "description": "Indicates whether the auto orient process has started."
    },
    "valid": {
      "type": "boolean",
      "description": "Indicates whether the auto orient request is valid."
    },
    "wifi_interrupting": {
      "type": "boolean",
      "description": "Indicates whether the auto orient process will interrupt WiFi traffic."
    }
  }
}
```

## Errors

| Status | Description |
|--------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.sites.maps_-_auto-placement.startSiteApAutoOrientation()`

## Usage Context

Triggers auto-orientation of the floor plan image, aligning it to true north based on AP data.

## Gotchas

- Requires sufficient AP deployment for accurate orientation. Results may need manual verification.

## Related Endpoints

- [GET_sites_site_id_maps_map_id_auto_orient.md](GET_sites_site_id_maps_map_id_auto_orient.md) — Get auto-orient results
- [POST_sites_site_id_maps_map_id_clear_auto_orient.md](POST_sites_site_id_maps_map_id_clear_auto_orient.md) — Clear auto-orient

## MistHelper Notes

Not currently used by MistHelper directly.
