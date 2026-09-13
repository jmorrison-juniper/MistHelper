# listOrgSiteStats

> listOrgSiteStats

## HTTP

`GET /api/v1/orgs/{org_id}/stats/sites`

## Description

Get List of Org Site Stats

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
| start | string | No |  |  | Start time (epoch timestamp in seconds, or relative string like "-1d", "-1w") |
| end | string | No |  |  | End time (epoch timestamp in seconds, or relative string like "-1d", "-2h", "now") |
| duration | string | No | 1d |  | Duration like 7d, 2w |
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
    "title": "stats_site",
    "required": [
      "country_code",
      "created_time",
      "id",
      "latlng",
      "modified_time",
      "name",
      "num_ap",
      "num_ap_connected",
      "num_clients",
      "num_devices",
      "num_devices_connected",
      "num_gateway",
      "num_gateway_connected",
      "num_switch",
      "num_switch_connected",
      "org_id",
      "timezone",
      "tzoffset"
    ],
    "type": "object",
    "properties": {
      "address": {
        "type": "string"
      },
      "alarmtemplate_id": {
        "type": [
          "string",
          "null"
        ],
        "contentEncoding": "uuid"
      },
      "analyticEnabled": {
        "type": "boolean"
      },
      "aptemplate_id": {
        "type": [
          "string",
          "null"
        ],
        "contentEncoding": "uuid"
      },
      "country_code": {
        "type": "string"
      },
      "created_time": {
        "type": "number",
        "description": "When the object has been created, in epoch",
        "readOnly": true
      },
      "engagementEnabled": {
        "type": "boolean"
      },
      "gatewaytemplate_id": {
        "type": [
          "string",
          "null"
        ],
        "contentEncoding": "uuid"
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
      "lat": {
        "type": "number"
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
      "lng": {
        "type": "number"
      },
      "modified_time": {
        "type": "number",
        "description": "When the object has been modified for the last time, in epoch",
        "readOnly": true
      },
      "msp_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "b9d42c2e-88ee-41f8-b798-f009ce7fe909"
        ]
      },
      "name": {
        "type": "string"
      },
      "networktemplate_id": {
        "type": [
          "string",
          "null"
        ],
        "contentEncoding": "uuid"
      },
      "notes": {
        "type": "string"
      },
      "num_ap": {
        "type": "integer",
        "contentEncoding": "int32"
      },
      "num_ap_connected": {
        "type": "integer",
        "contentEncoding": "int32"
      },
      "num_clients": {
        "type": "integer",
        "contentEncoding": "int32"
      },
      "num_devices": {
        "type": "integer",
        "contentEncoding": "int32"
      },
      "num_devices_connected": {
        "type": "integer",
        "contentEncoding": "int32"
      },
      "num_gateway": {
        "type": "integer",
        "contentEncoding": "int32"
      },
      "num_gateway_connected": {
        "type": "integer",
        "contentEncoding": "int32"
      },
      "num_switch": {
        "type": "integer",
        "contentEncoding": "int32"
      },
      "num_switch_connected": {
        "type": "integer",
        "contentEncoding": "int32"
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
        "contentEncoding": "uuid"
      },
      "secpolicy_id": {
        "type": [
          "string",
          "null"
        ],
        "contentEncoding": "uuid"
      },
      "sitegroup_ids": {
        "type": "array",
        "items": {
          "type": "string",
          "contentEncoding": "uuid"
        },
        "description": ""
      },
      "sitetemplate_id": {
        "type": [
          "string",
          "null"
        ],
        "contentEncoding": "uuid"
      },
      "timezone": {
        "type": "string"
      },
      "tzoffset": {
        "type": "integer",
        "contentEncoding": "int32"
      }
    },
    "description": "Site statistics"
  },
  "description": "",
  "examples": [
    [
      {
        "address": "1601 S De Anza Blvd, Cupertino, CA 95014, USA",
        "alarmtemplate_id": null,
        "analyticEnabled": true,
        "aptemplate_id": null,
        "country_code": "US",
        "created_time": 1472591606,
        "engagementEnabled": true,
        "gatewaytemplate_id": "e571f2a2-d748-4ad4-bd6c-895467957c21",
        "id": "83bc290a-b76d-47fa-a294-d34e47f30f7f",
        "lat": 37.295553,
        "latlng": {
          "lat": 37.295553,
          "lng": -122.033007
        },
        "lng": -122.033007,
        "modified_time": 1728057857,
        "msp_id": "a9af4951-a1de-4520-b398-c95a58947349",
        "name": "Live-Demo",
        "networktemplate_id": "964cb213-deb2-469d-8c1e-a5f8661c6886",
        "notes": "This site is used for demonstration purposes.",
        "num_ap": 17,
        "num_ap_connected": 14,
        "num_clients": 14,
        "num_devices": 26,
        "num_devices_connected": 22,
        "num_gateway": 1,
        "num_gateway_connected": 1,
        "num_switch": 8,
        "num_switch_connected": 7,
        "org_id": "b9814b40-ac4b-4424-86a8-b787eb68b86a",
        "rftemplate_id": "2c134c07-3c57-46b3-a53b-8aea92ed7234",
        "secpolicy_id": null,
        "sitegroup_ids": [
          "5644a432-eea9-4a2f-a30a-ddaf4dbc79cf",
          "5fc0f305-f626-49db-8869-10b87f201bba",
          "882796ef-190b-405e-98ef-cb487140cf64"
        ],
        "sitetemplate_id": null,
        "timezone": "America/Los_Angeles",
        "tzoffset": 960
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

`mistapi.api.v1.orgs.stats_-_sites.listOrgSiteStats()`

## Usage Context

Retrieves site-level statistics for all sites in the organization.

## Gotchas

- Includes device counts, client counts, and health scores per site.

## Related Endpoints

- [GET_orgs_org_id_sites.md](GET_orgs_org_id_sites.md) — List sites
- [GET_orgs_org_id_stats_devices.md](GET_orgs_org_id_stats_devices.md) — Device stats

## MistHelper Notes

Not currently used by MistHelper directly.
