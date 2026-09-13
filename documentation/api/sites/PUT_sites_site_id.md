# updateSiteInfo

> updateSiteInfo

## HTTP

`PUT /api/v1/sites/{site_id}`

## Description

Updates the configuration and metadata for an existing site. 


This endpoint allows modification of site properties including location details (address, coordinates, timezone), template associations (alarm, network, RF, security policy templates), site group memberships, and general information (name, notes).


All fields are optional and only provided fields will be updated.

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
    "address": {
      "type": [
        "string",
        "null"
      ],
      "description": "full address of the site",
      "examples": [
        "1601 S. Deanza Blvd., Cupertino, CA, 95014"
      ]
    },
    "alarmtemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "Alarm Template ID, this takes precedence over the Org-level alarmtemplate_id",
      "contentEncoding": "uuid",
      "examples": [
        "684dfc5c-fe77-2290-eb1d-ef3d677fe168"
      ]
    },
    "aptemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "AP Template ID, used by APs",
      "contentEncoding": "uuid",
      "examples": [
        "16bdf952-ade2-4491-80b0-85ce506c760b"
      ]
    },
    "country_code": {
      "type": "string",
      "description": "Country code for the site (for AP config generation), in two-character",
      "examples": [
        "US"
      ]
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "gatewaytemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "Gateway Template ID, used by gateways",
      "contentEncoding": "uuid",
      "examples": [
        "6f9b2e75-9b2f-b5ae-81e3-e14c76f1a90f"
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
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "examples": [
        "Mist Office"
      ]
    },
    "networktemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "Network Template ID, this takes precedence over Site Settings",
      "contentEncoding": "uuid",
      "examples": [
        "12ae9bd2-e0ab-107b-72e8-a7a005565ec2"
      ]
    },
    "notes": {
      "type": [
        "string",
        "null"
      ],
      "description": "Optional, any notes about the site"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "rftemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "RF Template ID, this takes precedence over Site Settings",
      "contentEncoding": "uuid",
      "examples": [
        "bb8a9017-1e36-5d6c-6f2b-551abe8a76a2"
      ]
    },
    "routertemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "Router Template ID, used by gateways",
      "contentEncoding": "uuid",
      "examples": [
        "6f9b2e75-9b2f-b5ae-81e3-e14c76f1a90f"
      ]
    },
    "secpolicy_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "SecPolicy ID",
      "contentEncoding": "uuid",
      "examples": [
        "3bcd0beb-5d0a-4cbd-92c1-14aea91e98ef"
      ]
    },
    "sitegroup_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "Sitegroups this site belongs to"
    },
    "sitetemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "Site Template ID",
      "contentEncoding": "uuid"
    },
    "timezone": {
      "type": "string",
      "description": "Timezone the site is at",
      "default": "UTC",
      "examples": [
        "America/Los_Angeles"
      ]
    },
    "tzoffset": {
      "type": "integer",
      "contentEncoding": "int32",
      "default": 0
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
    "address": {
      "type": [
        "string",
        "null"
      ],
      "description": "full address of the site",
      "examples": [
        "1601 S. Deanza Blvd., Cupertino, CA, 95014"
      ]
    },
    "alarmtemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "Alarm Template ID, this takes precedence over the Org-level alarmtemplate_id",
      "contentEncoding": "uuid",
      "examples": [
        "684dfc5c-fe77-2290-eb1d-ef3d677fe168"
      ]
    },
    "aptemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "AP Template ID, used by APs",
      "contentEncoding": "uuid",
      "examples": [
        "16bdf952-ade2-4491-80b0-85ce506c760b"
      ]
    },
    "country_code": {
      "type": "string",
      "description": "Country code for the site (for AP config generation), in two-character",
      "examples": [
        "US"
      ]
    },
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "gatewaytemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "Gateway Template ID, used by gateways",
      "contentEncoding": "uuid",
      "examples": [
        "6f9b2e75-9b2f-b5ae-81e3-e14c76f1a90f"
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
    "modified_time": {
      "type": "number",
      "description": "When the object has been modified for the last time, in epoch",
      "readOnly": true
    },
    "name": {
      "type": "string",
      "examples": [
        "Mist Office"
      ]
    },
    "networktemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "Network Template ID, this takes precedence over Site Settings",
      "contentEncoding": "uuid",
      "examples": [
        "12ae9bd2-e0ab-107b-72e8-a7a005565ec2"
      ]
    },
    "notes": {
      "type": [
        "string",
        "null"
      ],
      "description": "Optional, any notes about the site"
    },
    "org_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": [
        "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
      ]
    },
    "rftemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "RF Template ID, this takes precedence over Site Settings",
      "contentEncoding": "uuid",
      "examples": [
        "bb8a9017-1e36-5d6c-6f2b-551abe8a76a2"
      ]
    },
    "routertemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "Router Template ID, used by gateways",
      "contentEncoding": "uuid",
      "examples": [
        "6f9b2e75-9b2f-b5ae-81e3-e14c76f1a90f"
      ]
    },
    "secpolicy_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "SecPolicy ID",
      "contentEncoding": "uuid",
      "examples": [
        "3bcd0beb-5d0a-4cbd-92c1-14aea91e98ef"
      ]
    },
    "sitegroup_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "contentEncoding": "uuid"
      },
      "description": "Sitegroups this site belongs to"
    },
    "sitetemplate_id": {
      "type": [
        "string",
        "null"
      ],
      "description": "Site Template ID",
      "contentEncoding": "uuid"
    },
    "timezone": {
      "type": "string",
      "description": "Timezone the site is at",
      "default": "UTC",
      "examples": [
        "America/Los_Angeles"
      ]
    },
    "tzoffset": {
      "type": "integer",
      "contentEncoding": "int32",
      "default": 0
    }
  },
  "required": [
    "name"
  ],
  "description": "Site"
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

`mistapi.api.v1.sites.sites.updateSiteInfo()`

## Usage Context

Updates site-level properties (name, address, timezone, country code, location coordinates).

## Gotchas

- Changing timezone affects all scheduled operations at the site.

## Related Endpoints

- [GET_sites_site_id.md](GET_sites_site_id.md) — Site details
- [PUT_sites_site_id_setting.md](PUT_sites_site_id_setting.md) — Update settings

## MistHelper Notes

Used by MistHelper for site management operations.
