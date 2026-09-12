# listOrgJsiPastPurchases

> listOrgJsiPastPurchases

## HTTP

`GET /api/v1/orgs/{org_id}/jsi/inventory`

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
| limit | integer | No | 100 |  |  |
| page | integer | No | 1 |  |  |
| model | string | No |  |  |  |
| serial | string | No |  |  |  |

## Request Body

None.

## Response

### 200

OK

```json
{
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
  "description": "",
  "examples": [
    [
      {
        "device_name": "name1",
        "eol_time": 1561507200,
        "eos_time": 1672012800,
        "master": true,
        "model": "EX2300-24MP",
        "org_id": "6e843b41-f953-4af9-80e5-e1a70f65754a",
        "serial": "XN3123300095",
        "sku": "EX2300",
        "status": "connected",
        "suggested_version": "Latest 21.4R3-Sx",
        "type": "switch",
        "version": "23.4R2-S4.11",
        "version_eos_time": 1672012800,
        "version_time": 1561507200,
        "warranty": "Enhanced Hardware Warranty",
        "warranty_time": 1672012800,
        "warranty_type": "Enhanced Hardware Warranty"
      }
    ]
  ]
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

`mistapi.api.v1.orgs.jsi.listOrgJsiPastPurchases()`

## Usage Context

Retrieves the full JSI (Juniper Secure Infrastructure) inventory for the organization.

## Gotchas

- JSI inventory is separate from the standard Mist inventory.

## Related Endpoints

- [GET_orgs_org_id_jsi_inventory_search.md](GET_orgs_org_id_jsi_inventory_search.md) — Search JSI inventory
- [GET_orgs_org_id_jsi_devices.md](GET_orgs_org_id_jsi_devices.md) — JSI devices

## MistHelper Notes

Not currently used by MistHelper directly.
