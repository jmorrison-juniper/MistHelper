# getOrgLicensesBySite

> getOrgLicensesBySite

## HTTP

`GET /api/v1/orgs/{org_id}/licenses/usages`

## Description

Get Licenses Usage by Sites
This shows license usage (i.e. needed) based on the features enabled for the site.

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
  "uniqueItems": true,
  "type": "array",
  "items": {
    "title": "license_usage_org",
    "required": [
      "num_devices",
      "site_id",
      "usages"
    ],
    "type": "object",
    "properties": {
      "for_site": {
        "type": "boolean",
        "readOnly": true
      },
      "fully_loaded": {
        "type": "object",
        "additionalProperties": {
          "type": "integer",
          "format": "int32"
        },
        "description": "Maximum number of licenses that may be required if the service is enabled on all the Organization Devices. Property key is the service name (e.g. \"SUB-MAN\").",
        "readOnly": true
      },
      "num_devices": {
        "type": "integer",
        "contentEncoding": "int32",
        "readOnly": true
      },
      "site_id": {
        "type": "string",
        "contentEncoding": "uuid",
        "readOnly": true,
        "examples": [
          "441a1214-6928-442a-8e92-e1d34b8ec6a6"
        ]
      },
      "summary": {
        "type": "object",
        "additionalProperties": {
          "type": "integer",
          "format": "int32"
        },
        "description": "Number of licenses currently consumed. Property key is license type (e.g. SUB-MAN).",
        "readOnly": true
      },
      "usages": {
        "type": "object",
        "additionalProperties": {
          "type": "integer",
          "format": "int32"
        },
        "description": "Number of available licenes. Property key is the service name (e.g. \"SUB-MAN\"). name (e.g. \"SUB-MAN\")",
        "readOnly": true
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "fully_loaded": {
          "SUB-LOC": 30,
          "SUB-MAN": 80
        },
        "num_devices": 80,
        "site_id": "4ac1dcf4-9d8b-7211-65c4-057819f0862b",
        "usages": {
          "SUB-LOC": 30,
          "SUB-MAN": 60
        }
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

`mistapi.api.v1.orgs.licenses.getOrgLicensesBySite()`

## Usage Context

Retrieves license usage details showing consumed vs available licenses.

## Gotchas

- Usage is broken down by license type (SUB-MAN, SUB-EX, etc.).

## Related Endpoints

- [GET_orgs_org_id_licenses.md](GET_orgs_org_id_licenses.md) — License summary
- [GET_orgs_org_id_claim_status.md](GET_orgs_org_id_claim_status.md) — Claim status

## MistHelper Notes

Used by MistHelper via `getOrgLicensesSummary` in Menu 52.
