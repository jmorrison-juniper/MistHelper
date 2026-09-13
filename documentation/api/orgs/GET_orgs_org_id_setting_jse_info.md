# getOrgJseInfo

> getOrgJseInfo

## HTTP

`GET /api/v1/orgs/{org_id}/setting/jse/info`

## Description

Retrieves the list of JSE orgs associated with the account.

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

Example response

```json
{
  "type": "object",
  "properties": {
    "cloud_name": {
      "type": "string",
      "examples": [
        "devcentral.juniperclouds.net"
      ]
    },
    "org_names": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "username": {
      "type": "string",
      "examples": [
        "john@abc.com"
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

`mistapi.api.v1.orgs.integration_jse.getOrgJseInfo()`

## Usage Context

Retrieves Juniper Sky Enterprise (JSE) info for the organization.

## Gotchas

- JSE integration must be enabled in org settings.

## Related Endpoints

- [GET_orgs_org_id_setting_jse_setup.md](GET_orgs_org_id_setting_jse_setup.md) — JSE setup
- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Full org settings

## MistHelper Notes

Not currently used by MistHelper directly.
