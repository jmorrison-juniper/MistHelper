# listGatewayApplications

> listGatewayApplications

## HTTP

`GET /api/v1/const/gateway_applications`

## Description

Get the full list of applications that we recognize

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of Alarm Definitions

```json
{
  "type": "array",
  "items": {
    "title": "const_gateway_applications_definition",
    "type": "object",
    "properties": {
      "app_id": {
        "type": "boolean",
        "examples": [
          true
        ]
      },
      "key": {
        "type": "string",
        "examples": [
          "4shared"
        ]
      },
      "name": {
        "type": "string",
        "examples": [
          "4shared"
        ]
      },
      "ssr_app_id": {
        "type": "boolean",
        "examples": [
          true
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "app_id": true,
        "key": "4shared",
        "name": "4shared",
        "ssr_app_id": true
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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.constants.definitions.listGatewayApplications()`

## Usage Context

Returns the list of applications recognized by Juniper gateway devices (SRX/SSR) for application-aware routing and firewall policies. These gateway-specific application definitions may differ from the general application list as they are optimized for WAN edge traffic classification.

## Gotchas

- Gateway applications are specific to SRX/SSR devices — for AP-level application visibility use the general applications endpoint.
- The overlap between gateway applications and general applications is partial; some applications are only available on one side.

## Related Endpoints

- [GET_const_applications.md](GET_const_applications.md) — General application definitions
- [GET_const_app_categories.md](GET_const_app_categories.md) — Application categories
- [../orgs/GET_orgs_org_id_servicepolicies.md](../orgs/GET_orgs_org_id_servicepolicies.md) — Service policies that reference these applications

## MistHelper Notes

Not currently used by MistHelper directly.
