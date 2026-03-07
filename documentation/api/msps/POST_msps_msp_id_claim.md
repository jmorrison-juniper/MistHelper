# claimMspLicense

> claimMspLicense

## HTTP

`POST /api/v1/msps/{msp_id}/claim`

## Description

Claim an Order by Activation Code

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "code": {
      "type": "string"
    }
  },
  "required": [
    "code"
  ]
}
```

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "inventory_added": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "response_claim_license_inventory_item",
        "required": [
          "mac",
          "magic",
          "model",
          "serial",
          "type"
        ],
        "type": "object",
        "properties": {
          "mac": {
            "type": "string"
          },
          "magic": {
            "type": "string"
          },
          "model": {
            "type": "string"
          },
          "serial": {
            "type": "string"
          },
          "type": {
            "type": "string"
          }
        }
      },
      "description": ""
    },
    "inventory_duplicated": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "response_claim_license_inventory_item",
        "required": [
          "mac",
          "magic",
          "model",
          "serial",
          "type"
        ],
        "type": "object",
        "properties": {
          "mac": {
            "type": "string"
          },
          "magic": {
            "type": "string"
          },
          "model": {
            "type": "string"
          },
          "serial": {
            "type": "string"
          },
          "type": {
            "type": "string"
          }
        }
      },
      "description": ""
    },
    "inventory_pending": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "response_claim_license_inventory_pending_item",
        "type": "object",
        "properties": {
          "mac": {
            "type": "string"
          }
        }
      },
      "description": "for async claim"
    },
    "license_added": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "response_claim_license_license_item",
        "required": [
          "end",
          "quantity",
          "start",
          "type"
        ],
        "type": "object",
        "properties": {
          "end": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "quantity": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "start": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "type": {
            "type": "string"
          }
        }
      },
      "description": ""
    },
    "license_duplicated": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "response_claim_license_license_item",
        "required": [
          "end",
          "quantity",
          "start",
          "type"
        ],
        "type": "object",
        "properties": {
          "end": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "quantity": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "start": {
            "type": "integer",
            "contentEncoding": "int32"
          },
          "type": {
            "type": "string"
          }
        }
      },
      "description": ""
    },
    "license_error": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "response_claim_license_license_error_item",
        "required": [
          "order",
          "reason"
        ],
        "type": "object",
        "properties": {
          "order": {
            "type": "string"
          },
          "reason": {
            "type": "string"
          }
        }
      },
      "description": ""
    }
  },
  "required": [
    "inventory_added",
    "inventory_duplicated",
    "license_added",
    "license_duplicated",
    "license_error"
  ]
}
```

## Errors

| Status | Description |
|--------|-------------|
| 400 | Response when the key is invalid (or already used) |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.msps.licenses.claimMspLicense()`

## Usage Context

Claims a license activation code into the MSP license pool. License codes are provided by Juniper sales and add subscription entitlements (AP, switch, gateway, Marvis, etc.) to the MSP's shared pool.

## Gotchas

- Each activation code can only be claimed once — double-claiming returns an error.
- The claimed license is added to the MSP pool and must be explicitly allocated to child orgs.

## Related Endpoints

- [GET_msps_msp_id_licenses.md](GET_msps_msp_id_licenses.md) — Verify the license was added to the pool
- [PUT_msps_msp_id_licenses.md](PUT_msps_msp_id_licenses.md) — Distribute the license to an org

## MistHelper Notes

Not currently used by MistHelper directly.
