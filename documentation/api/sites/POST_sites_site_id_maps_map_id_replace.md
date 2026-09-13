# replaceSiteMapImage

> replaceSiteMapImage

## HTTP

`POST /api/v1/sites/{site_id}/maps/{map_id}/replace`

## Description

Replace Map Image


This works like an PUT where the image will be replaced. If transform is provided, all the locations of the objects on the map (AP, Zone, Vbeacon, Beacon) will be transformed as well (relative to the new Map)

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
  "required": [
    "file"
  ],
  "type": "object",
  "properties": {
    "file": {
      "type": "string",
      "contentEncoding": "base64"
    },
    "json": {
      "title": "map_site_replace_file_json",
      "type": "object",
      "properties": {
        "transform": {
          "type": "object",
          "properties": {
            "rotation": {
              "type": "number",
              "description": "Whether to rotate the replacing image, in degrees",
              "default": 0
            },
            "scale": {
              "type": "number",
              "description": "Whether to scale the replacing image",
              "default": 1,
              "examples": [
                0.98
              ]
            },
            "x": {
              "type": "number",
              "description": "Where the (0, 0) of the new image is relative to the original map",
              "default": 0,
              "examples": [
                3.16
              ]
            },
            "y": {
              "type": "number",
              "description": "Where the (0, 0) of the new image is relative to the original map",
              "default": 0,
              "examples": [
                12
              ]
            }
          },
          "description": "If `transform` is provided, all the locations of the objects on the map (AP, Zone, Vbeacon, Beacon) will be transformed as well (relative to the new Map)"
        }
      }
    }
  }
}
```

## Response

### 200

OK

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

`mistapi.api.v1.sites.maps.replaceSiteMapImage()`

## Usage Context

Replaces a map's floor plan image and metadata. Used when updating floor plans after renovations.

## Gotchas

- Replacing a map may invalidate AP positions if the floor plan geometry changed.

## Related Endpoints

- [POST_sites_site_id_maps_map_id_image.md](POST_sites_site_id_maps_map_id_image.md) — Upload image only
- [GET_sites_site_id_maps_map_id.md](GET_sites_site_id_maps_map_id.md) — Map details

## MistHelper Notes

Not currently used by MistHelper directly.
