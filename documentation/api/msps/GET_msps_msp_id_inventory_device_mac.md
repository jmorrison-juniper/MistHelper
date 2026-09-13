# getMspInventoryByMac

> getMspInventoryByMac

## HTTP

`GET /api/v1/msps/{msp_id}/inventory/{device_mac}`

## Description

Get Inventory By device MAC address

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |
| device_mac | string | Yes |  |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "for_site": {
      "type": "boolean",
      "readOnly": true
    },
    "mac": {
      "type": "string",
      "readOnly": true
    },
    "model": {
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
    "serial": {
      "type": "string",
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
    "type": {
      "type": "string",
      "readOnly": true
    }
  },
  "required": [
    "mac",
    "model",
    "org_id",
    "serial",
    "site_id",
    "type"
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

`mistapi.api.v1.msps.inventory.getMspInventoryByMac()`

## Usage Context

Looks up a specific device by MAC address across all organizations within the MSP. This is invaluable for quickly locating which org a device belongs to when you only have the MAC address (e.g., from a shipping manifest or physical label).

## Gotchas

- The MAC address format must match the API's expected format (typically colon-separated lowercase, e.g., `aa:bb:cc:dd:ee:ff`).
- If the device is not claimed to any MSP org, the endpoint returns a 404.

## Related Endpoints

- [GET_msps_msp_id_orgs.md](GET_msps_msp_id_orgs.md) — List orgs to narrow search scope
- [../orgs/GET_orgs_org_id_inventory.md](../orgs/GET_orgs_org_id_inventory.md) — Full inventory within a specific org

## MistHelper Notes

Not currently used by MistHelper directly. Menu **117** (`MSPInventoryExporter`) provides MSP-level inventory export capabilities.
