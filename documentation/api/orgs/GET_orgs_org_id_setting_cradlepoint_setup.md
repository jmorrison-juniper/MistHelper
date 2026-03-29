# testOrgCradlepointConnection

> testOrgCradlepointConnection

## HTTP

`GET /api/v1/orgs/{org_id}/setting/cradlepoint/setup`

## Description

This tests the Cradlepoint integration in Mist

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
  "type": "object",
  "properties": {
    "error": {
      "type": "string",
      "description": "if status is `inactive` this field returns the reason for it being inactive.",
      "readOnly": true,
      "examples": [
        "Cradlepoint API keys are no longer valid, please verify and update the keys under organization settings."
      ]
    },
    "last_status": {
      "type": "string",
      "description": "status of integration detected during last sync. enum: `active`, `inactive`",
      "readOnly": true
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

`mistapi.api.v1.orgs.integration_cradlepoint.testOrgCradlepointConnection()`

## Usage Context

Retrieves Cradlepoint integration setup for the organization.

## Gotchas

- Cradlepoint integration requires a valid NCM account.

## Related Endpoints

- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Full org settings
- [PUT_orgs_org_id_setting.md](PUT_orgs_org_id_setting.md) — Update org settings

## MistHelper Notes

Not currently used by MistHelper directly.
