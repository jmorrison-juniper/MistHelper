# searchOrgJsiAssetsAndContracts

> searchOrgJsiAssetsAndContracts

## HTTP

`GET /api/v1/orgs/{org_id}/jsi/inventory/search`

## Description

This gets all devices purchased from the accounts associated with the Org 
  * Fetch Install base devices for all linked accounts and associated account of the linked accounts. 
  * The primary and the associated account ids will be queries from SFDC by passing the linked account 
  * Returns only the device centric details of the Install base device. No customer specific information will be returned.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| claimed | boolean | No |  |  | Device claim status, `true` for claimed devices, `false` for all devices |
| model | string | No |  |  | Device model |
| serial | string | No |  |  | Device serial |
| sku | string | No |  |  | SKU name of the device |
| status | string | No |  |  | Device status |
| warranty_type | string | No |  |  | Device warranty type |
| eol_after | string | No |  |  | Filter devices with End Of Life date after this date |
| eol_before | string | No |  |  | Filter devices with End Of Life date before this date |
| eos_after | string | No |  |  | Filter devices with End Of Support date after this date |
| eos_before | string | No |  |  | Filter devices with End Of Support date before this date |
| version_eos_after | string | No |  |  | Filter devices with OS Version End Of Support date after this date |
| version_eos_before | string | No |  |  | Filter devices with OS Version End Of Support date before this date |
| has_support | boolean | No |  |  | Indicates if the device is covered under active support contract |
| sirt_id | string | No |  |  | To get the onboarded devices that are affected by the SIRT ID |
| pbn_id | string | No |  |  | To get the onboarded devices that are affected by the PBN ID |
| text | string | No |  |  | Wildcards for `serial`, `model`, `account_id` |
| limit | integer | No | 100 |  |  |
| sort | string | No | timestamp |  | On which field the list should be sorted, -prefix represents DESC order |
| search_after | string | No |  |  | Pagination cursor for retrieving subsequent pages of results. This value is automatically populated by Mist in the `next` URL from the previous response and should not be manually constructed. |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "end": {
      "type": "integer",
      "description": "Offset to end at",
      "contentEncoding": "int32"
    },
    "limit": {
      "type": "integer",
      "description": "Number of results to return",
      "contentEncoding": "int32"
    },
    "next": {
      "type": "string"
    },
    "results": {
      "type": "array",
      "items": {
        "title": "js_inventory_item",
        "type": "object",
        "properties": {
          "claimed": {
            "type": "boolean",
            "description": "Indicates if the device is claimed by any org"
          },
          "device_name": {
            "type": "string",
            "description": "Name of the device"
          },
          "eol_psn": {
            "type": "string",
            "description": "EOL PSN",
            "examples": [
              "TSB18097"
            ]
          },
          "eol_time": {
            "type": "integer",
            "description": "End of life time",
            "contentEncoding": "int32"
          },
          "eos_time": {
            "type": "integer",
            "description": "End of support time",
            "contentEncoding": "int32"
          },
          "has_support": {
            "type": "boolean",
            "description": "Indicates if the device is covered under active support contract"
          },
          "master": {
            "type": "boolean",
            "description": "Indicates whether it is Master"
          },
          "model": {
            "type": "string",
            "description": "Model of the install base inventory"
          },
          "org_id": {
            "type": "string",
            "contentEncoding": "uuid",
            "readOnly": true,
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ]
          },
          "serial": {
            "type": "string",
            "description": "Serial Number of the inventory"
          },
          "sku": {
            "type": "string",
            "description": "Serviceable device stock"
          },
          "status": {
            "type": "string",
            "description": "Status of the connected device"
          },
          "suggested_version": {
            "type": "string",
            "description": "Suggested SW version"
          },
          "type": {
            "type": "string",
            "description": "enum: `ap`, `gateway`, `switch`"
          },
          "version": {
            "type": "string",
            "description": "SW version running"
          },
          "version_description": {
            "type": "string",
            "description": "Version description"
          },
          "version_eos_time": {
            "type": "integer",
            "description": "End of Service of version",
            "contentEncoding": "int32"
          },
          "version_time": {
            "type": "integer",
            "description": "FRS date of the version",
            "contentEncoding": "int32"
          },
          "warranty": {
            "type": "string",
            "description": "warranty description"
          },
          "warranty_time": {
            "type": "integer",
            "description": "Time when warranty needs to be renewed",
            "contentEncoding": "int32"
          },
          "warranty_type": {
            "type": "string",
            "description": "Warranty type for Juniper Support Insight (JSI) devices. The warranty type\nis used to determine the support level and duration of the warranty for the\ndevice. enum:\n  * WTY00001: Standard Hardware Warranty\n  * WTY00002: Enhanced Hardware Warranty\n  * WTY00003: Dead On Arrival Warranty\n  * WTY00004: Limited Lifetime Warranty\n  * WTY00005: Software Warranty\n  * WTY00006: Limited Lifetime Warranty for WLA\n  * WTY00007: Warranty-JCPO EOL (DOA Not Included)\n  * WTY00008: MIST Enhanced Hardware Warranty\n  * WTY00009: MIST Standard Warranty\n  * WTY00099: Determine Lifetime warranty"
          }
        }
      },
      "description": ""
    },
    "start": {
      "type": "integer",
      "description": "Offset to start from",
      "contentEncoding": "int32"
    },
    "total": {
      "type": "integer",
      "description": "Total number of results",
      "contentEncoding": "int32"
    }
  }
}
```

## Errors

| Status | Description |
|--------|-------------|
| 400 | Bad Request - no Juniper Account Linked |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Supports pagination. Use `limit` and `page` query parameters.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.jsi.searchOrgJsiAssetsAndContracts()`

## Usage Context

Searches JSI inventory with filtering options.

## Gotchas

- No known gotchas.

## Related Endpoints

- [GET_orgs_org_id_jsi_inventory_count.md](GET_orgs_org_id_jsi_inventory_count.md) — Count JSI inventory
- [GET_orgs_org_id_jsi_inventory.md](GET_orgs_org_id_jsi_inventory.md) — Full JSI inventory

## MistHelper Notes

Not currently used by MistHelper directly.
