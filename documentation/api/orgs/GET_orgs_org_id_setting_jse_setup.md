# getOrgJseIntegration

> getOrgJseIntegration

## HTTP

`GET /api/v1/orgs/{org_id}/setting/jse/setup`

## Description

Get Org JSE Integration

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

OK

```json
{
  "title": "account_jse_info",
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

`mistapi.api.v1.orgs.integration_jse.getOrgJseIntegration()`

## Usage Context

Retrieves Juniper Sky Enterprise (JSE) setup configuration for the organization.

## Gotchas

- Setup endpoint returns the current JSE linking status.

## Related Endpoints

- [GET_orgs_org_id_setting_jse_info.md](GET_orgs_org_id_setting_jse_info.md) — JSE info
- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Full org settings

## MistHelper Notes

Not currently used by MistHelper directly.
