# listInstallerSites

> listInstallerSites

## HTTP

`GET /api/v1/installer/orgs/{org_id}/sites`

## Description

Get List of Sites

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

## Request Body

None.

## Response

### 200

List of Sites

```json
{
  "type": "array",
  "items": {
    "title": "installer_site",
    "required": [
      "address",
      "country_code",
      "latlng",
      "name"
    ],
    "type": "object",
    "properties": {
      "address": {
        "type": "string",
        "examples": [
          "1601 S. Deanza Blvd., Cupertino, CA, 95014"
        ]
      },
      "country_code": {
        "type": "string",
        "examples": [
          "US"
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
      "latlng": {
        "title": "lat_lng",
        "required": [
          "lat",
          "lng"
        ],
        "type": "object",
        "properties": {
          "lat": {
            "type": "number",
            "examples": [
              37.295833
            ]
          },
          "lng": {
            "type": "number",
            "examples": [
              -122.032946
            ]
          }
        }
      },
      "name": {
        "type": "string",
        "examples": [
          "Mist Office"
        ]
      },
      "rftemplate_name": {
        "type": "string",
        "examples": [
          "rftemplate1"
        ]
      },
      "sitegroup_names": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "",
        "examples": [
          [
            "sg1",
            "sg2"
          ]
        ]
      },
      "timezone": {
        "type": "string",
        "examples": [
          "America/Los_Angeles"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "address": "1601 S. Deanza Blvd., Cupertino, CA, 95014",
        "country_code": "US",
        "id": "4ac1dcf4-9d8b-7211-65c4-057819f0862b",
        "latlng": {
          "lat": 37.295833,
          "lng": -122.032946
        },
        "name": "Mist Office",
        "rftemplate_name": "rftemplate1",
        "sitegroup_names": [
          "sg1",
          "sg2"
        ],
        "timezone": "America/Los_Angeles"
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

`mistapi.api.v1.installer.installer.listInstallerSites()`

## Usage Context

Use this endpoint to list sites in the organization available to the installer. Common use cases:

- Browsing available sites during field installation to select the target site
- Populating the site selection list in the Mist mobile installer app

## Gotchas

- Returns a simplified site list scoped to installer privileges
- For full site details and configuration, use the admin-level site APIs
- Sites may be filtered based on the installer's access permissions

## Related Endpoints

- [PUT_installer_orgs_org_id_sites_site_name.md](PUT_installer_orgs_org_id_sites_site_name.md) -- Update a site or assign devices to it
- [GET_installer_orgs_org_id_sites_site_name_maps.md](GET_installer_orgs_org_id_sites_site_name_maps.md) -- List maps for a site
- [../orgs/GET_orgs_org_id_sites.md](../orgs/GET_orgs_org_id_sites.md) -- Full admin site list

## MistHelper Notes

Not currently used by MistHelper. MistHelper uses the full admin-level site APIs (Menu **11**, **20**, **27**).
