# listLicenseTypes

> listLicenseTypes

## HTTP

`GET /api/v1/const/license_types`

## Description

Get License Types

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

List of License Types

```json
{
  "type": "array",
  "items": {
    "title": "const_license_type",
    "type": "object",
    "properties": {
      "description": {
        "type": "string",
        "examples": [
          "Wired Assurance 12"
        ]
      },
      "includes": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "",
        "examples": [
          [
            "sub_ex12a",
            "sub_ex12p"
          ]
        ]
      },
      "key": {
        "type": "string",
        "examples": [
          "sub_ex12"
        ]
      },
      "name": {
        "type": "string",
        "examples": [
          "SUB-EX12"
        ]
      }
    }
  },
  "description": "",
  "examples": [
    [
      {
        "description": "Wired Assurance 12",
        "includes": [
          "sub_ex12a",
          "sub_ex12p"
        ],
        "key": "sub_ex12",
        "name": "SUB-EX12"
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

`mistapi.api.v1.constants.definitions.listLicenseTypes()`

## Usage Context

Returns the list of Mist license types and their descriptions (e.g., SUB-MAN, SUB-EX, SUB-VNA). Use this to interpret license data from org license summaries and validate entitlement coverage for features like Marvis, WAN Assurance, and Premium Analytics.

## Gotchas

- License SKU names follow Juniper naming conventions and may change between subscription tiers.
- No known gotchas with the endpoint itself; the response is a static reference list.

## Related Endpoints

- [../orgs/GET_orgs_org_id_licenses.md](../orgs/GET_orgs_org_id_licenses.md) — Org license inventory (actual licenses owned)
- [../orgs/GET_orgs_org_id_licenses_summary.md](../orgs/GET_orgs_org_id_licenses_summary.md) — License usage summary

## MistHelper Notes

Not currently used by MistHelper as a direct constants lookup. Menu **48** (`OrgLicenseExporter.licenses`) and Menu **49** (`OrgLicenseExporter.license_summary`) export license data whose types correspond to definitions returned here.
