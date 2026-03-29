# createOrgWirelessClientsBlocklist

> createOrgWirelessClientsBlocklist

## HTTP

`POST /api/v1/orgs/{org_id}/setting/blacklist`

## Description

Create Org Blacklist Client List. 

If there is already a blacklist, this API will replace it with the new one. 

Max number of blacklist clients is 1000. 

Retrieve the current blacklisted clients from `blacklist_url` under Org:Setting


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
  "type": "object",
  "properties": {
    "macs": {
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "examples": [
        [
          "683b679ac024"
        ]
      ]
    }
  },
  "required": [
    "macs"
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
    "macs": {
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "examples": [
        [
          "683b679ac024"
        ]
      ]
    }
  },
  "required": [
    "macs"
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

`mistapi.api.v1.orgs.setting.createOrgWirelessClientsBlocklist()`

## Usage Context

Adds entries to the org-level blacklist (blocklist).

## Gotchas

- Blacklisted clients are denied network access across all sites.

## Related Endpoints

- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Get org settings
- [PUT_orgs_org_id_setting.md](PUT_orgs_org_id_setting.md) — Update org settings

## MistHelper Notes

Not currently used by MistHelper directly.
