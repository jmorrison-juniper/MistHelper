# listSiteAssets

> listSiteAssets

## HTTP

`GET /api/v1/sites/{site_id}/assets`

## Description

Get List of Site Assets

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
    "title": "asset",
    "required": [
      "mac",
      "name"
    ],
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
    "description": "Asset"
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

`mistapi.api.v1.sites.assets.listSiteAssets()`

## Usage Context

Lists BLE assets tracked at a site. Returns discovered asset beacons matching configured filters.

## Gotchas

- Requires BLE scanning enabled on APs and at least one asset filter configured.

## Related Endpoints

- [POST_sites_site_id_assets.md](POST_sites_site_id_assets.md) — Create asset record
- [GET_sites_site_id_assetfilters.md](GET_sites_site_id_assetfilters.md) — Asset filter configuration
- [GET_sites_site_id_assets_search.md](GET_sites_site_id_stats_assets_search.md) — Search assets

## MistHelper Notes

Not currently used by MistHelper directly.
