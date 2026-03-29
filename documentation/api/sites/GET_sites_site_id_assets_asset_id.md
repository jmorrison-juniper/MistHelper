# getSiteAsset

> getSiteAsset

## HTTP

`GET /api/v1/sites/{site_id}/assets/{asset_id}`

## Description

Get Site Asset Details

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |
| asset_id | string | Yes |  |

## Request Body

None.

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
    "mac": {
      "type": "string",
      "description": "Bluetooth MAC"
    },
    "map_id": {
      "type": "string",
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
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "441a1214-6928-442a-8e92-e1d34b8ec6a6"
      ]
    },
    "tag_id": {
      "type": "string",
      "contentEncoding": "uuid"
    }
  },
  "required": [
    "mac",
    "name"
  ],
  "description": "Asset"
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

`mistapi.api.v1.sites.assets.getSiteAsset()`

## Usage Context

Retrieves details of a specific BLE asset, including its last known location and signal data.

## Gotchas

- Location data is only accurate if APs have BLE scanning enabled and calibration is current.

## Related Endpoints

- [PUT_sites_site_id_assets_asset_id.md](PUT_sites_site_id_assets_asset_id.md) — Update asset
- [DELETE_sites_site_id_assets_asset_id.md](DELETE_sites_site_id_assets_asset_id.md) — Delete asset
- [GET_sites_site_id_assets.md](GET_sites_site_id_assets.md) — List all assets

## MistHelper Notes

Not currently used by MistHelper directly.
