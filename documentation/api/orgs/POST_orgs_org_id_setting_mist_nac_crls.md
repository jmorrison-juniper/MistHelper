# importOrgNacCrl

> importOrgNacCrl

## HTTP

`POST /api/v1/orgs/{org_id}/setting/mist_nac_crls`

## Description

The Import NAC Org CRL File endpoint allows users to manually upload a Certificate Revocation List (CRL) file in either PEM or DER format. This is a multipart POST request. We support one file upload per issuer, and re-uploads for the same issuer will overwrite the existing file.

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
    "file": {
      "type": "string",
      "description": "a PEM or DER formatted CRL file",
      "contentEncoding": "base64"
    },
    "json": {
      "type": "string",
      "description": "a JSON string with \"name\" field for CRL file issuer (optional)"
    }
  }
}
```

## Response

### 200

Example response

```json
{
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

`mistapi.api.v1.orgs.nac_crl.importOrgNacCrl()`

## Usage Context

Uploads Certificate Revocation Lists (CRLs) for Mist NAC.

## Gotchas

- CRLs must be in PEM format.
- Revoked certificates are immediately denied access.

## Related Endpoints

- [GET_orgs_org_id_setting_mist_nac_crls.md](GET_orgs_org_id_setting_mist_nac_crls.md) — Get CRLs
- [GET_orgs_org_id_setting.md](GET_orgs_org_id_setting.md) — Get org settings

## MistHelper Notes

Not currently used by MistHelper directly.
