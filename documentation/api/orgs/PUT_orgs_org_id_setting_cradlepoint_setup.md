# updateOrgCradlepointConnectionToMist

> updateOrgCradlepointConnectionToMist

## HTTP

`PUT /api/v1/orgs/{org_id}/setting/cradlepoint/setup`

## Description

This updates the Cradlepoint integration settings in Mist

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
    "cp_api_id": {
      "type": "string",
      "examples": [
        "84446d61-2206-4ea5-855a-0043f980be54"
      ]
    },
    "cp_api_key": {
      "type": "string",
      "examples": [
        "79c329da9893e34099c7d8ad5cb9c941"
      ]
    },
    "ecm_api_id": {
      "type": "string",
      "examples": [
        "73446d61-2206-4ea5-855a-0043f980be62"
      ]
    },
    "ecm_api_key": {
      "type": "string",
      "examples": [
        "68b329da9893e34099c7d8ad5cb9c9405"
      ]
    },
    "enable_lldp": {
      "type": "boolean"
    }
  }
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

`mistapi.api.v1.orgs.integration_cradlepoint.updateOrgCradlepointConnectionToMist()`

## Usage Context

Updates the Cradlepoint integration configuration.

## Gotchas

- Requires valid Cradlepoint credentials.

## Related Endpoints

- [POST_orgs_org_id_setting_cradlepoint_setup.md](POST_orgs_org_id_setting_cradlepoint_setup.md) — Initial setup
- [GET_orgs_org_id_setting_cradlepoint.md](GET_orgs_org_id_setting_cradlepoint.md) — Get config

## MistHelper Notes

Not currently used by MistHelper directly.
