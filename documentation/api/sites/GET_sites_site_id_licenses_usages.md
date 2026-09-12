# getSiteLicenseUsage

> getSiteLicenseUsage

## HTTP

`GET /api/v1/sites/{site_id}/licenses/usages`

## Description

This shows license usage (i.e. needed) based on the features enabled for the site.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

None.

## Response

### 200

Site License Usage

```json
{
  "type": "object",
  "properties": {
    "org_entitled": {
      "type": "object",
      "additionalProperties": {
        "type": "integer",
        "format": "int32"
      },
      "description": "License entitlement for the entire org",
      "examples": [
        {
          "SUB-LOC": 30,
          "SUB-MAN": 60
        }
      ]
    },
    "svna_enabled": {
      "type": "boolean",
      "description": "Eligibility for the Switch SLE"
    },
    "trial_enabled": {
      "type": "boolean"
    },
    "usages": {
      "type": "object",
      "additionalProperties": {
        "type": "integer",
        "format": "int32"
      },
      "description": "Subscriptions and their quantities",
      "examples": [
        {
          "SUB-LOC": 30,
          "SUB-MAN": 60
        }
      ]
    },
    "vna_eligible": {
      "type": "boolean",
      "description": "Eligibility for the AP/Client SLE"
    },
    "vna_ui": {
      "type": "boolean",
      "description": "If True, Conversational Assistant and Marvis Action available"
    },
    "wvna_eligible": {
      "type": "boolean",
      "description": "Eligibility for the WAN SLE"
    }
  },
  "required": [
    "org_entitled",
    "svna_enabled",
    "trial_enabled",
    "usages",
    "vna_eligible",
    "vna_ui",
    "wvna_eligible"
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

`mistapi.api.v1.sites.licenses.getSiteLicenseUsage()`

## Usage Context

Retrieves license usage data for a site, showing consumed vs available licenses by subscription type.

## Gotchas

- License usage reflects current device assignments. Adding/removing devices changes counts.

## Related Endpoints

- [../orgs/GET_orgs_org_id_licenses.md](../orgs/GET_orgs_org_id_licenses.md) — Org-level licenses
- [GET_sites_site_id_devices.md](GET_sites_site_id_devices.md) — Devices consuming licenses

## MistHelper Notes

Not currently used by MistHelper directly. Menu **16** uses `getOrgLicensesSummary` at org level.
