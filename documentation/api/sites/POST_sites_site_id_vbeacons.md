# createSiteVBeacon

> createSiteVBeacon

## HTTP

`POST /api/v1/sites/{site_id}/vbeacons`

## Description

Create Virtual Beacon

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
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
    "major": {
      "type": "integer",
      "description": "Bluetooth tag major",
      "contentEncoding": "int32",
      "examples": [
        1356
      ]
    },
    "map_id": {
      "type": "string",
      "description": "Map where the device belongs to",
      "contentEncoding": "uuid",
      "examples": [
        "63eda950-c6da-11e4-a628-60f81dd250cc"
      ]
    },
    "message": {
      "type": "string",
      "description": "Message that can be displayed when the sdkclient gets near the vbeacon",
      "examples": [
        "Welcome to Mist"
      ]
    },
    "minor": {
      "type": "integer",
      "description": "Bluetooth tag minor",
      "contentEncoding": "int32",
      "examples": [
        21
      ]
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "description": "Name / label of the device",
      "examples": [
        "conference room"
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
    "power": {
      "maximum": 100.0,
      "minimum": -30.0,
      "type": "integer",
      "description": "Required if `power_mode`==`custom`, -30 - 100, in dBm. For default power_mode, power = 4 dBm.",
      "contentEncoding": "int32",
      "default": 4
    },
    "power_mode": {
      "type": "string",
      "description": "enum: `custom`, `default`"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "url": {
      "type": "string",
      "description": "URL to show, optional",
      "examples": [
        "https://www.mist.com/any"
      ]
    },
    "uuid": {
      "type": "string",
      "description": "Bluetooth tag UUID",
      "contentEncoding": "uuid",
      "examples": [
        "31375aeb-b8d3-1ea6-83bf-a31eb04e1c38"
      ]
    },
    "wayfinding_nodename": {
      "type": "string",
      "description": "Name to be used in wayfinding_path or wayfinding_grid blob",
      "examples": [
        "node1"
      ]
    },
    "x": {
      "type": "number",
      "description": "X in pixel",
      "examples": [
        53.5
      ]
    },
    "y": {
      "type": "number",
      "description": "Y in pixel",
      "examples": [
        173.1
      ]
    }
  },
  "description": "Request Body"
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
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
    "major": {
      "type": "integer",
      "description": "Bluetooth tag major",
      "contentEncoding": "int32",
      "examples": [
        1356
      ]
    },
    "map_id": {
      "type": "string",
      "description": "Map where the device belongs to",
      "contentEncoding": "uuid",
      "examples": [
        "63eda950-c6da-11e4-a628-60f81dd250cc"
      ]
    },
    "message": {
      "type": "string",
      "description": "Message that can be displayed when the sdkclient gets near the vbeacon",
      "examples": [
        "Welcome to Mist"
      ]
    },
    "minor": {
      "type": "integer",
      "description": "Bluetooth tag minor",
      "contentEncoding": "int32",
      "examples": [
        21
      ]
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "description": "Name / label of the device",
      "examples": [
        "conference room"
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
    "power": {
      "maximum": 100.0,
      "minimum": -30.0,
      "type": "integer",
      "description": "Required if `power_mode`==`custom`, -30 - 100, in dBm. For default power_mode, power = 4 dBm.",
      "contentEncoding": "int32",
      "default": 4
    },
    "power_mode": {
      "type": "string",
      "description": "enum: `custom`, `default`"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "url": {
      "type": "string",
      "description": "URL to show, optional",
      "examples": [
        "https://www.mist.com/any"
      ]
    },
    "uuid": {
      "type": "string",
      "description": "Bluetooth tag UUID",
      "contentEncoding": "uuid",
      "examples": [
        "31375aeb-b8d3-1ea6-83bf-a31eb04e1c38"
      ]
    },
    "wayfinding_nodename": {
      "type": "string",
      "description": "Name to be used in wayfinding_path or wayfinding_grid blob",
      "examples": [
        "node1"
      ]
    },
    "x": {
      "type": "number",
      "description": "X in pixel",
      "examples": [
        53.5
      ]
    },
    "y": {
      "type": "number",
      "description": "Y in pixel",
      "examples": [
        173.1
      ]
    }
  },
  "description": "vBeacon"
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

`mistapi.api.v1.sites.vbeacons.createSiteVBeacon()`

## Usage Context

Creates a new virtual beacon at a site. Virtual beacons enable proximity notifications without physical hardware.

## Gotchas

- Requires accurate map coordinates. Beacons placed outside map boundaries are ignored.

## Related Endpoints

- [GET_sites_site_id_vbeacons.md](GET_sites_site_id_vbeacons.md) — List virtual beacons
- [GET_sites_site_id_vbeacons_vbeacon_id.md](GET_sites_site_id_vbeacons_vbeacon_id.md) — Get beacon

## MistHelper Notes

Not currently used by MistHelper directly.
