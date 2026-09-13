# importOrgUserMacs

> importOrgUserMacs

## HTTP

`POST /api/v1/orgs/{org_id}/usermacs/import`

## Description

Import Org User MACs

### CSV Import example
```csv 
mac,labels,vlan,notes,name,radius_group
921b638445cd,"bldg1,flor1",vlan-100
721b638445ef,"bldg2,flor2",vlan-101,Canon Printers
721b638445ee,"bldg3,flor3",vlan-102,Printer2,VIP
921b638445ce,"bldg4,flor4",vlan-103
921b638445cf,"bldg5,flor5",vlan-104
````

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

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
      "description": "File to upload",
      "contentEncoding": "base64"
    }
  }
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "added": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "examples": [
        [
          "921b638445cd"
        ]
      ]
    },
    "errors": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "examples": [
        [
          "921b638445ce - mac invalid",
          "921b638445cf - mac already provided"
        ]
      ]
    },
    "updated": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "examples": [
        [
          "721b638445ef",
          "721b638445ee"
        ]
      ]
    }
  }
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

`mistapi.api.v1.orgs.user_macs.importOrgUserMacs()`

## Usage Context

Bulk-imports user MAC entries into the organization.

## Gotchas

- Accepts CSV format. Duplicate MACs update existing entries.

## Related Endpoints

- [GET_orgs_org_id_usermacs_search.md](GET_orgs_org_id_usermacs_search.md) — Search user MACs
- [POST_orgs_org_id_usermacs_delete.md](POST_orgs_org_id_usermacs_delete.md) — Bulk delete

## MistHelper Notes

Not currently used by MistHelper directly.
