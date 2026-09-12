# getOrgNacCrl

> getOrgNacCrl

## HTTP

`GET /api/v1/orgs/{org_id}/setting/mist_nac_crls`

## Description

Returns all uploaded CRL file IDs with names for the orgI

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
  "title": "response_nac_crl_files",
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "title": "nac_crl_file",
        "type": "object",
        "properties": {
          "created_time": {
            "type": "number",
            "description": "When the object has been created, in epoch",
            "readOnly": true
          },
          "id": {
            "type": "string",
            "description": "Unique ID for the uploaded CRL file, used to reference the file",
            "readOnly": true,
            "examples": [
              "a1ca26f3-44dd-4833-9a7b-97bbb2ab5230"
            ]
          },
          "modified_time": {
            "type": "number",
            "description": "When the object has been modified for the last time, in epoch",
            "readOnly": true
          },
          "name": {
            "type": "string",
            "description": "Issuer name for the CRL file",
            "examples": [
              "SampleCertificateSigner"
            ]
          },
          "url": {
            "type": "string",
            "description": "URL to download the uploaded CRL file",
            "examples": [
              "http://url/to/crl_file"
            ]
          }
        }
      },
      "description": ""
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

`mistapi.api.v1.orgs.nac_crl.getOrgNacCrl()`

## Usage Context

Retrieves Certificate Revocation Lists (CRLs) for Mist NAC.

## Gotchas

- CRLs are used to revoke certificates for 802.1X authentication.

## Related Endpoints

- [GET_orgs_org_id_setting_mist_scep.md](GET_orgs_org_id_setting_mist_scep.md) — SCEP settings
- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Full org settings

## MistHelper Notes

Not currently used by MistHelper directly.
