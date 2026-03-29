# updateOrgAssetFilter

> updateOrgAssetFilter

## HTTP

`PUT /api/v1/orgs/{org_id}/assetfilters/{assetfilter_id}`

## Description

Updates an existing BLE asset filter for the given site.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| assetfilter_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "ap_mac": {
      "type": "string"
    },
    "beam": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "disabled": {
      "type": "boolean",
      "description": "Whether the asset filter is disabled",
      "default": false
    },
    "eddystone_uid_namespace": {
      "type": "string",
      "description": "Eddystone uid namespace used to filter assets",
      "examples": [
        "2818e3868dec25629ede"
      ]
    },
    "eddystone_url": {
      "type": "string",
      "description": "Eddystone url used to filter assets",
      "examples": [
        "https://www.abc.com"
      ]
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
    "mfg_company_id": {
      "type": "integer",
      "description": "BLE manufacturing-specific company-id used to filter assets",
      "contentEncoding": "int32",
      "examples": [
        935
      ]
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "examples": [
        "Visitor Tags"
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
    "rssi": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "service_uuid": {
      "type": "string",
      "description": "BLE service data uuid used to filter assets",
      "contentEncoding": "uuid",
      "examples": [
        "0000fe6a-0000-1000-8000-0030459b3cfb"
      ]
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    }
  },
  "required": [
    "name"
  ],
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
    "ap_mac": {
      "type": "string"
    },
    "beam": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "disabled": {
      "type": "boolean",
      "description": "Whether the asset filter is disabled",
      "default": false
    },
    "eddystone_uid_namespace": {
      "type": "string",
      "description": "Eddystone uid namespace used to filter assets",
      "examples": [
        "2818e3868dec25629ede"
      ]
    },
    "eddystone_url": {
      "type": "string",
      "description": "Eddystone url used to filter assets",
      "examples": [
        "https://www.abc.com"
      ]
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
    "mfg_company_id": {
      "type": "integer",
      "description": "BLE manufacturing-specific company-id used to filter assets",
      "contentEncoding": "int32",
      "examples": [
        935
      ]
    },
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "examples": [
        "Visitor Tags"
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
    "rssi": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "service_uuid": {
      "type": "string",
      "description": "BLE service data uuid used to filter assets",
      "contentEncoding": "uuid",
      "examples": [
        "0000fe6a-0000-1000-8000-0030459b3cfb"
      ]
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    }
  },
  "required": [
    "name"
  ],
  "description": "Asset Filter"
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

`mistapi.api.v1.orgs.asset_filters.updateOrgAssetFilter()`

## Usage Context

Updates an existing asset filter for BLE asset tracking.

## Gotchas

- Asset filters control which BLE beacons are tracked.

## Related Endpoints

- [GET_orgs_org_id_assetfilters_assetfilter_id.md](GET_orgs_org_id_assetfilters_assetfilter_id.md) — Get filter
- [POST_orgs_org_id_assetfilters.md](POST_orgs_org_id_assetfilters.md) — Create filter

## MistHelper Notes

Not currently used by MistHelper directly.
