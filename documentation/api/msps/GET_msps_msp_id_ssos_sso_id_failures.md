# listMspSsoLatestFailures

> listMspSsoLatestFailures

## HTTP

`GET /api/v1/msps/{msp_id}/ssos/{sso_id}/failures`

## Description

Get List of MSP SSO Latest Failures

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |
| sso_id | string | Yes |  |

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

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.msps.sso.listMspSsoLatestFailures()`

## Usage Context

Retrieves the most recent SSO login failures for a specific MSP SSO configuration. Use this to troubleshoot SAML authentication issues such as certificate mismatches, assertion format errors, or attribute mapping problems.

## Gotchas

- Failure records include SAML response details that may contain sensitive identity information — handle with care.
- Only recent failures are retained; historical failures are not permanently stored.

## Related Endpoints

- [GET_msps_msp_id_ssos_sso_id.md](GET_msps_msp_id_ssos_sso_id.md) — Get SSO config to compare against failure details
- [PUT_msps_msp_id_ssos_sso_id.md](PUT_msps_msp_id_ssos_sso_id.md) — Update SSO config to fix identified issues
- [GET_msps_msp_id_ssos_sso_id_metadata.md](GET_msps_msp_id_ssos_sso_id_metadata.md) — Download metadata for IdP configuration verification

## MistHelper Notes

Not currently used by MistHelper directly.
