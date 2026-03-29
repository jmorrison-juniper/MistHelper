# setupOrgJseIntegration

> setupOrgJseIntegration

## HTTP

`POST /api/v1/orgs/{org_id}/setting/jse/setup`

## Description

In JSE UI: 
1. Create custom role with Read access to service_location and RW access to site and IPSec profile APIs. 
2. Create a user with the above custom role. - email: john@abc.com 
3. Activate the user in the JSE account. 
4. Create the service locations on the JSE account.

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
    "cloud_name": {
      "type": "string",
      "examples": [
        "devcentral.juniperclouds.net"
      ]
    },
    "password": {
      "type": "string",
      "examples": [
        "foryoureyesonly"
      ]
    },
    "username": {
      "type": "string",
      "examples": [
        "john@abc.com"
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

`mistapi.api.v1.orgs.integration_jse.setupOrgJseIntegration()`

## Usage Context

Configures Juniper Sky Enterprise (JSE) integration for the organization.

## Gotchas

- Requires valid JSE credentials.

## Related Endpoints

- [GET_orgs_org_id_setting_jse_info.md](GET_orgs_org_id_setting_jse_info.md) — Get JSE info
- [GET_orgs_org_id_setting_jse_setup.md](GET_orgs_org_id_setting_jse_setup.md) — Get JSE setup

## MistHelper Notes

Not currently used by MistHelper directly.
