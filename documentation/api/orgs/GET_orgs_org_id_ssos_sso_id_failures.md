# listOrgSsoLatestFailures

> listOrgSsoLatestFailures

## HTTP

`GET /api/v1/orgs/{org_id}/ssos/{sso_id}/failures`

## Description

Get List of Org SSO Latest Failures

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| sso_id | string | Yes |  |

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
  "type": "object",
  "properties": {
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "response_sso_failure_search_item",
        "required": [
          "detail",
          "saml_assertion_xml",
          "timestamp"
        ],
        "type": "object",
        "properties": {
          "detail": {
            "type": "string"
          },
          "saml_assertion_xml": {
            "type": "string"
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          }
        }
      },
      "description": ""
    }
  },
  "required": [
    "results"
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

`mistapi.api.v1.orgs.sso.listOrgSsoLatestFailures()`

## Usage Context

Retrieves SSO login failure events for a specific SSO configuration.

## Gotchas

- Useful for debugging SAML configuration issues.

## Related Endpoints

- [GET_orgs_org_id_ssos_sso_id.md](GET_orgs_org_id_ssos_sso_id.md) — Get SSO config
- [GET_orgs_org_id_ssos_sso_id_metadata.md](GET_orgs_org_id_ssos_sso_id_metadata.md) — SAML metadata

## MistHelper Notes

Not currently used by MistHelper directly.
