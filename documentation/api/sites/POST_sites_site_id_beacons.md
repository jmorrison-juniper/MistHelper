# createSiteBeacon

> createSiteBeacon

## HTTP

`POST /api/v1/sites/{site_id}/beacons`

## Description

Create Site Beacon

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
    "eddystone_instance": {
      "type": "string",
      "description": "Eddystone-UID instance (6 bytes) in hexstring format"
    },
    "eddystone_namespace": {
      "type": "string",
      "description": "Eddystone-UID namespace (10 bytes) in hexstring format"
    },
    "eddystone_url": {
      "type": "string",
      "description": "Eddystone-URL url"
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
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
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    },
    "mac": {
      "type": "string",
      "description": "Optional, MAC of the beacon, currently used only to identify battery voltage"
    },
    "map_id": {
      "type": "string",
      "description": "Map where the device belongs to",
      "contentEncoding": "uuid"
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "description": "Name / label of the device"
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
      "minimum": -12.0,
      "type": "integer",
      "description": "In dBm",
      "contentEncoding": "int32",
      "default": -12
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "type": {
      "type": "string",
      "description": "enum: `eddystone-uid`, `eddystone-url`, `ibeacon`"
    },
    "x": {
      "type": "number",
      "description": "X in pixel"
    },
    "y": {
      "type": "number",
      "description": "Y in pixel"
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
    "eddystone_instance": {
      "type": "string",
      "description": "Eddystone-UID instance (6 bytes) in hexstring format"
    },
    "eddystone_namespace": {
      "type": "string",
      "description": "Eddystone-UID namespace (10 bytes) in hexstring format"
    },
    "eddystone_url": {
      "type": "string",
      "description": "Eddystone-URL url"
    },
    "for_site": {
      "type": "boolean",
      "readOnly": true
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
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "53f10664-3ce8-4c27-b382-0ef66432349f"
      ]
    },
    "mac": {
      "type": "string",
      "description": "Optional, MAC of the beacon, currently used only to identify battery voltage"
    },
    "map_id": {
      "type": "string",
      "description": "Map where the device belongs to",
      "contentEncoding": "uuid"
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "description": "Name / label of the device"
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
      "minimum": -12.0,
      "type": "integer",
      "description": "In dBm",
      "contentEncoding": "int32",
      "default": -12
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "type": {
      "type": "string",
      "description": "enum: `eddystone-uid`, `eddystone-url`, `ibeacon`"
    },
    "x": {
      "type": "number",
      "description": "X in pixel"
    },
    "y": {
      "type": "number",
      "description": "Y in pixel"
    }
  },
  "description": "Beacon"
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

`mistapi.api.v1.sites.beacons.createSiteBeacon()`

## Usage Context

Creates a new BLE beacon at a site. Beacons are physical BLE devices configured for indoor positioning.

## Gotchas

- Beacon UUID/major/minor combination must be unique.

## Related Endpoints

- [GET_sites_site_id_beacons.md](GET_sites_site_id_beacons.md) — List beacons
- [POST_sites_site_id_vbeacons.md](POST_sites_site_id_vbeacons.md) — Create virtual beacon

## MistHelper Notes

Not currently used by MistHelper directly.
