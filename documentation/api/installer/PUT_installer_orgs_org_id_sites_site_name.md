# createOrUpdateInstallerSites

> createOrUpdateInstallerSites

## HTTP

`PUT /api/v1/installer/orgs/{org_id}/sites/{site_name}`

## Description

Often the Installers are asked to assign Devices to Sites. The Sites can either be pre-created or created/modified by the Installer. If this is an update, the same grace period also applies.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| site_name | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
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
  },
  "required": [
    "address",
    "country_code",
    "latlng",
    "name"
  ],
  "description": "Request Body"
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

`mistapi.api.v1.installer.installer.createOrUpdateInstallerSites()`

## Usage Context

Use this endpoint to update a site or assign devices to it during installation. Common use cases:

- Assigning newly claimed devices to a specific site
- Creating a new site if it does not already exist (installers can create sites)
- Updating site metadata during field deployment

## Gotchas

- The `{site_name}` parameter uses the site name, not the site ID (unlike admin APIs)
- If the site does not exist, it may be auto-created depending on organization settings
- Site assignment moves the device config to the new site

## Related Endpoints

- [GET_installer_orgs_org_id_sites.md](GET_installer_orgs_org_id_sites.md) -- List available sites
- [PUT_installer_orgs_org_id_devices_device_mac.md](PUT_installer_orgs_org_id_devices_device_mac.md) -- Provision device at the site
- [GET_installer_orgs_org_id_sites_site_name_maps.md](GET_installer_orgs_org_id_sites_site_name_maps.md) -- List maps for the site

## MistHelper Notes

Not currently used by MistHelper.
