# listApplications

> listApplications

## HTTP

`GET /api/v1/const/applications`

## Description

Get List of a list of applications that Juniper-Mist APs recognize

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of Applications

```json
{
  "type": "array",
  "items": {
    "title": "const_application_definition",
    "type": "object",
    "properties": {
      "app_id": {
        "type": "boolean"
      },
      "app_image_url": {
        "type": "string",
        "examples": [
          "\"\""
        ]
      },
      "app_probe": {
        "type": "boolean"
      },
      "category": {
        "type": "string",
        "examples": [
          "FileSharing"
        ]
      },
      "group": {
        "type": "string",
        "examples": [
          "File Sharing"
        ]
      },
      "key": {
        "type": "string",
        "examples": [
          "dropbox"
        ]
      },
      "name": {
        "type": "string",
        "examples": [
          "Dropbox"
        ]
      },
      "signature_based": {
        "type": "boolean"
      },
      "ssr_app_id": {
        "type": "boolean"
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "app_id": true,
        "app_image_url": "",
        "app_probe": true,
        "category": "FileSharing",
        "group": "File Sharing",
        "key": "dropbox",
        "name": "Dropbox",
        "signature_based": true,
        "ssr_app_id": true
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

`mistapi.api.v1.constants.definitions.listApplications()`

## Usage Context

Returns the master list of recognized network applications (e.g., Office 365, Zoom, YouTube) that can be referenced in service policies and application-aware firewall rules. Use this to look up application identifiers when creating or interpreting WAN/security policies.

## Gotchas

- The application list is large (hundreds of entries). Filter by category or search by name for efficiency.
- Application definitions are Juniper-maintained and updated periodically; do not cache indefinitely.

## Related Endpoints

- [GET_const_app_categories.md](GET_const_app_categories.md) — High-level application categories
- [GET_const_app_subcategories.md](GET_const_app_subcategories.md) — Application subcategories
- [GET_const_gateway_applications.md](GET_const_gateway_applications.md) — Gateway-specific application definitions
- [../orgs/GET_orgs_org_id_services.md](../orgs/GET_orgs_org_id_services.md) — Service definitions that reference applications

## MistHelper Notes

Not currently used by MistHelper directly.
