# claimOrgLicense

> claimOrgLicense

## HTTP

`POST /api/v1/orgs/{org_id}/claim`

## Description

Claim Org licenses / activation codes

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
    "async": {
      "type": "boolean",
      "description": "Whether to do a async claim process",
      "default": false
    },
    "code": {
      "type": "string",
      "description": "Activation code"
    },
    "device_type": {
      "type": "string",
      "description": "enum: `ap`, `gateway`, `switch`"
    },
    "type": {
      "type": "string",
      "description": "what to claim. enum: `all`, `inventory`, `license`"
    }
  },
  "required": [
    "code",
    "type"
  ],
  "description": "Request Body"
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
| 400 | Invalid key (or already used) |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.licenses.claimOrgLicense()`

## Usage Context

Claims devices into the organization using claim codes.

## Gotchas

- Claim codes are typically found on the device label or packaging.
- Claimed devices appear in the org inventory.

## Related Endpoints

- [GET_orgs_org_id_claim_status.md](GET_orgs_org_id_claim_status.md) — Check claim status
- [GET_orgs_org_id_inventory.md](GET_orgs_org_id_inventory.md) — Org inventory

## MistHelper Notes

Not currently used by MistHelper directly.
