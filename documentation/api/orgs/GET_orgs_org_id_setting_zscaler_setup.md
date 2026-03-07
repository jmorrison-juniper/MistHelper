# getOrgZscalerIntegration

> getOrgZscalerIntegration

## HTTP

`GET /api/v1/orgs/{org_id}/setting/zscaler/setup`

## Description

To get Zscaler integration

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
        "zscalerbeta.net"
      ]
    },
    "partner_key": {
      "type": "string",
      "examples": [
        "K35vrZcK3JvrZc"
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
  "description": "OAuth linked Zscaler apps account details"
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

`mistapi.api.v1.orgs.integration_zscaler.getOrgZscalerIntegration()`

## Usage Context

Retrieves Zscaler integration setup for the organization.

## Gotchas

- Zscaler integration enables cloud security for WAN edge traffic.

## Related Endpoints

- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Full org settings
- [PUT_orgs_org_id_setting.md](PUT_orgs_org_id_setting.md) — Update org settings

## MistHelper Notes

Not currently used by MistHelper directly.
