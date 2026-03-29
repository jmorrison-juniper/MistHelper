# setupOrgZscalerIntegration

> setupOrgZscalerIntegration

## HTTP

`POST /api/v1/orgs/{org_id}/setting/zscaler/setup`

## Description

To setup Zscaler integration

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
        "zscalerbeta.net"
      ]
    },
    "partner_key": {
      "type": "string",
      "examples": [
        "K35vrZcK3JvrZc"
      ]
    },
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
    "cloud_name",
    "partner_key",
    "password",
    "username"
  ],
  "description": "OAuth linked Zscaler apps account details"
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

`mistapi.api.v1.orgs.integration_zscaler.setupOrgZscalerIntegration()`

## Usage Context

Configures Zscaler cloud security integration.

## Gotchas

- Requires valid Zscaler credentials and tunnel configuration.

## Related Endpoints

- [GET_orgs_org_id_setting_zscaler.md](GET_orgs_org_id_setting_zscaler_setup.md) — Get Zscaler config
- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Get org settings

## MistHelper Notes

Not currently used by MistHelper directly.
