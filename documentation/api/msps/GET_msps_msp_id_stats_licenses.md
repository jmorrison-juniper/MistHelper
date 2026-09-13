# listMspOrgLicenses

> listMspOrgLicenses

## HTTP

`GET /api/v1/msps/{msp_id}/stats/licenses`

## Description

Get List of MSP Licenses

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "amendments": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "license_amendment",
        "type": "object",
        "properties": {
          "created_time": {
            "type": "number",
            "description": "When the object has been created, in epoch",
            "readOnly": true
          },
          "end_time": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "id": {
            "type": "string",
            "description": "Unique ID of the object instance in the Mist Organization",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "53f10664-3ce8-4c27-b382-0ef66432349f"
            ]
          },
          "modified_time": {
            "type": "number",
            "description": "When the object has been modified for the last time, in epoch",
            "readOnly": true
          },
          "quantity": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "start_time": {
            "type": "integer",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "subscription_id": {
            "type": "string",
            "readOnly": true
          },
          "type": {
            "type": "string",
            "description": "Type of license. The list of supported license type can be retrieve with the [List License Type]($e/Constants%20Definitions/listLicenseTypes) API request.",
            "readOnly": true
          }
        }
      },
      "description": "",
      "readOnly": true
    },
    "entitled": {
      "type": "object",
      "additionalProperties": {
        "type": "integer",
        "format": "int32"
      },
      "description": "Property key is license type (e.g. SUB-MAN) and Property value is the number of licenses entitled.",
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
    "licenses": {
      "type": "array",
      "items": {
        "title": "license_sub",
        "type": "object",
        "properties": {
          "created_time": {
            "type": "number",
            "description": "When the object has been created, in epoch",
            "readOnly": true
          },
          "end_time": {
            "type": "integer",
            "description": "End date of the license term",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "id": {
            "type": "string",
            "description": "Unique ID of the object instance in the Mist Organization",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "53f10664-3ce8-4c27-b382-0ef66432349f"
            ]
          },
          "modified_time": {
            "type": "number",
            "description": "When the object has been modified for the last time, in epoch",
            "readOnly": true
          },
          "order_id": {
            "type": "string",
            "readOnly": true
          },
          "org_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "quantity": {
            "type": "integer",
            "description": "Number of devices entitled for this license",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "remaining_quantity": {
            "type": "integer",
            "description": "Number of licenses left in this subscription",
            "contentEncoding": "int32"
          },
          "start_time": {
            "type": "integer",
            "description": "Start date of the license term",
            "contentEncoding": "int32",
            "readOnly": true
          },
          "subscription_id": {
            "type": "string",
            "readOnly": true
          },
          "type": {
            "type": "string",
            "description": "Type of license. The list of supported license type can be retrieve with the [List License Type]($e/Constants%20Definitions/listLicenseTypes) API request.",
            "readOnly": true
          }
        }
      },
      "description": ""
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
  },
  "description": "License"
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

`mistapi.api.v1.msps.licenses.listMspOrgLicenses()`

## Usage Context

Retrieves license usage statistics broken down by organization within the MSP. Shows how many licenses each org is using vs allocated, enabling capacity planning and license compliance monitoring.

## Gotchas

- Statistics are near-real-time but may have minor delays compared to actual device counts.
- No known gotchas with the endpoint itself.

## Related Endpoints

- [GET_msps_msp_id_licenses.md](GET_msps_msp_id_licenses.md) — Raw license inventory
- [GET_msps_msp_id_stats_orgs.md](GET_msps_msp_id_stats_orgs.md) — Org-level operational statistics
- [PUT_msps_msp_id_licenses.md](PUT_msps_msp_id_licenses.md) — Rebalance licenses based on stats

## MistHelper Notes

Not currently used by MistHelper directly.
