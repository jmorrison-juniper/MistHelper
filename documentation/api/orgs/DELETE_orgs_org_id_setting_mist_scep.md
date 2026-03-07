# disableOrgMistScep

> disableOrgMistScep

## HTTP

`DELETE /api/v1/orgs/{org_id}/setting/mist_scep`

## Description

Disable Mist SCEP Org setting

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
    "cert_providers": {
      "type": "array",
      "items": {
        "title": "org_setting_scep_cert_provider",
        "enum": [
          "intune",
          "jamf",
          "byod"
        ],
        "type": "string",
        "description": "enum: `intune`, `jamf`, `byod`"
      },
      "description": "List of SCEP cert providers, e.g. `intune`, `jamf`, `byod`"
    },
    "enabled": {
      "type": "boolean",
      "readOnly": true
    },
    "intune_scep_url": {
      "type": "string",
      "readOnly": true,
      "examples": [
        "https://scep.mistsys.com/api/v1/incoming/intune/:org_id/scep"
      ]
    },
    "jamf_access_token": {
      "type": "string",
      "readOnly": true,
      "examples": [
        "1Z4QqEnCt05Jjt3TV5LgPJ4V_WL_RWnJ7dqVMLYHj81="
      ]
    },
    "jamf_scep_url": {
      "type": "string",
      "readOnly": true,
      "examples": [
        "https://scep.mistsys.com/api/v1/incoming/intune/:org_id/scep"
      ]
    },
    "jamf_webhook_url": {
      "type": "string",
      "readOnly": true,
      "examples": [
        "https://scep.mistsys.com/api/v1/webhook/jamf/:org_id/scep"
      ]
    },
    "suspended": {
      "type": "boolean",
      "description": "Whether SCEP is suspended for this org",
      "default": false
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

`mistapi.api.v1.orgs.scep.disableOrgMistScep()`

## Usage Context

Removes the SCEP (Simple Certificate Enrollment Protocol) configuration from the organization.

## Gotchas

- Disables SCEP-based certificate enrollment for NAC.

## Related Endpoints

- [POST_orgs_org_id_setting_mist_scep.md](POST_orgs_org_id_setting_mist_scep.md) — Setup SCEP
- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Org settings

## MistHelper Notes

Not currently used by MistHelper directly.
