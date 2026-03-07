# linkOrgToJuniperJuniperAccount

> linkOrgToJuniperJuniperAccount

## HTTP

`POST /api/v1/orgs/{org_id}/setting/juniper/link_accounts`

## Description

Link Juniper Accounts

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
    "password": {
      "type": "string",
      "description": "Customer account password",
      "examples": [
        "password"
      ]
    },
    "username": {
      "type": "string",
      "description": "Customer account user name",
      "examples": [
        "john@nmo.com"
      ]
    }
  },
  "required": [
    "password",
    "username"
  ]
}
```

## Response

### 200

Account linked

```json
{
  "type": "object",
  "properties": {
    "accounts": {
      "type": "array",
      "items": {
        "title": "juniper_account",
        "type": "object",
        "properties": {
          "linked_by": {
            "type": "string",
            "readOnly": true,
            "examples": [
              "John Smith (john@abccorp.com)"
            ]
          },
          "name": {
            "type": "string",
            "readOnly": true,
            "examples": [
              "ABC Corp"
            ]
          }
        }
      },
      "description": ""
    }
  }
}
```

## Errors

| Status | Description |
|--------|-------------|
| 400 | Account already linked |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.integration_juniper.linkOrgToJuniperJuniperAccount()`

## Usage Context

Links Juniper accounts to the organization settings.

## Gotchas

- Required for Juniper cloud integration features.

## Related Endpoints

- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Get org settings
- [DELETE_orgs_org_id_setting_juniper_link_accounts.md](POST_orgs_org_id_setting_juniper_link_accounts.md) — Unlink

## MistHelper Notes

Not currently used by MistHelper directly.
