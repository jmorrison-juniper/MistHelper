# listOrgSites

> listOrgSites

## HTTP

`GET /api/v1/orgs/{org_id}/sites`

## Description

Get List of Org Sites

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

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
    "title": "site",
    "required": [
      "name"
    ],
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
    "description": "Site"
  },
  "description": "",
  "examples": [
    [
      {
        "address": "1601 S. Deanza Blvd., Cupertino, CA, 95014",
        "alarmtemplate_id": "684dfc5c-fe77-2290-eb1d-ef3d677fe168",
        "aptemplate_id": "16bdf952-ade2-4491-80b0-85ce506c760b",
        "country_code": "US",
        "created_time": 0,
        "gatewaytemplate_id": "6f9b2e75-9b2f-b5ae-81e3-e14c76f1a90f",
        "id": "497f6eca-6276-5007-bfeb-53cbbbba6f19",
        "latlng": {
          "lat": 37.295833,
          "lng": -122.032946
        },
        "modified_time": 0,
        "name": "Mist Office",
        "networktemplate_id": "12ae9bd2-e0ab-107b-72e8-a7a005565ec2",
        "notes": "string",
        "org_id": "a40f5d1f-d889-42e9-94ea-b9b33585fc6b",
        "rftemplate_id": "bb8a9017-1e36-5d6c-6f2b-551abe8a76a2",
        "secpolicy_id": "3bcd0beb-5d0a-4cbd-92c1-14aea91e98ef",
        "sitegroup_ids": [
          "497f6eca-6276-5008-bfeb-53cbbbba6f1a"
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

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.sites.listOrgSites()`

## Usage Context

Lists all sites in the organization.

## Gotchas

- This is one of the most frequently called endpoints.
- Returns all site metadata including name, address, timezone, country_code, and latlng.

## Related Endpoints

- [GET_orgs_org_id_sites_search.md](GET_orgs_org_id_sites_search.md) — Search sites
- [POST_orgs_org_id_sites.md](POST_orgs_org_id_sites.md) — Create site

## MistHelper Notes

Used by MistHelper via `listOrgSites` in Menu 11, 20, 27, and many data collection operations. This is a core building-block call used extensively throughout MistHelper.
