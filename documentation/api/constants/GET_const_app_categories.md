# listAppCategoryDefinitions

> listAppCategoryDefinitions

## HTTP

`GET /api/v1/const/app_categories`

## Description

Get List of definitions of all the supported Application Categories. The example field contains an example payload as you would receive in the alarm webhook output.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of Application Categories Definitions

```json
{
  "type": "array",
  "items": {
    "title": "const_app_category_definition",
    "required": [
      "display",
      "key"
    ],
    "type": "object",
    "properties": {
      "display": {
        "type": "string",
        "description": "Description of the app category",
        "examples": [
          "Images"
        ]
      },
      "filters": {
        "type": "object",
        "properties": {
          "srx": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          },
          "ssr": {
            "uniqueItems": true,
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": ""
          }
        }
      },
      "includes": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "List of other App Categories contained by this one"
      },
      "key": {
        "type": "string",
        "description": "Key name of the app category",
        "examples": [
          "Images"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "display": "Images",
        "filters": {
          "srx": [
            "Enhanced_Images_Media",
            "Enhanced_Web_Images",
            "Enhanced_Image_Servers"
          ]
        },
        "key": "Images"
      },
      {
        "display": "Standard",
        "includes": [
          "Adult",
          "FileSharing",
          "Games",
          "Images",
          "Malware",
          "NewsAndReference",
          "Recreation",
          "Religion",
          "Security",
          "Sports",
          "Technology",
          "Violence"
        ],
        "key": "Standard"
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

`mistapi.api.v1.constants.definitions.listAppCategoryDefinitions()`

## Usage Context

Returns the list of high-level application categories (e.g., "Productivity", "Social Media", "Video Streaming") used to group applications for policy management. Use this to build category-based filtering in service policies or traffic analysis.

## Gotchas

- No known gotchas; the response is a small static reference list.

## Related Endpoints

- [GET_const_applications.md](GET_const_applications.md) — Individual application definitions within these categories
- [GET_const_app_subcategories.md](GET_const_app_subcategories.md) — Subcategories for finer-grained grouping
- [GET_const_gateway_applications.md](GET_const_gateway_applications.md) — Gateway-specific application list

## MistHelper Notes

Not currently used by MistHelper directly.
