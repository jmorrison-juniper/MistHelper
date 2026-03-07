# listAppSubCategoryDefinitions

> listAppSubCategoryDefinitions

## HTTP

`GET /api/v1/const/app_subcategories`

## Description

Get List of definitions of all the supported Application sub-categories. The example field contains an example payload as you would receive in the alarm webhook output.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of Application Sub-categories Definitions

```json
{
  "type": "array",
  "items": {
    "title": "const_app_subcategory_definition",
    "required": [
      "display",
      "key",
      "traffic_type"
    ],
    "type": "object",
    "properties": {
      "display": {
        "type": "string",
        "description": "Description of the app subcategory",
        "examples": [
          "Office Document"
        ]
      },
      "key": {
        "type": "string",
        "description": "Key name of the app subcategory",
        "examples": [
          "Office_Documents"
        ]
      },
      "traffic_type": {
        "type": "string",
        "description": "Type of traffic (QoS) of the app subcategory",
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
        "display": "Office Documents",
        "key": "Office_Documents",
        "traffic_type": "data_interactive"
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

`mistapi.api.v1.constants.definitions.listAppSubCategoryDefinitions()`

## Usage Context

Returns the list of application subcategories used for finer-grained classification within application categories. Use this when building granular service policies that need to differentiate between types of traffic within a broad category.

## Gotchas

- No known gotchas; the response is a small static reference list.

## Related Endpoints

- [GET_const_app_categories.md](GET_const_app_categories.md) — Parent application categories
- [GET_const_applications.md](GET_const_applications.md) — Individual application definitions

## MistHelper Notes

Not currently used by MistHelper directly.
