# listOrgDevices

> listOrgDevices

## HTTP

`GET /api/v1/orgs/{org_id}/devices`

## Description

Get List of Org Devices

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
  "type": "object",
  "properties": {
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "org_device",
        "required": [
          "mac",
          "name"
        ],
        "type": "object",
        "properties": {
          "mac": {
            "type": "string"
          },
          "name": {
            "type": "string"
          }
        }
      },
      "description": ""
    }
  },
  "required": [
    "results"
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

`mistapi.api.v1.orgs.devices.listOrgDevices()`

## Usage Context

Lists all devices across all sites in the organization.

## Gotchas

- Defaults to APs only; use `type=all` to include switches and gateways.

## Related Endpoints

- [GET_orgs_org_id_devices_search.md](GET_orgs_org_id_devices_search.md) — Search devices
- [GET_orgs_org_id_inventory.md](GET_orgs_org_id_inventory.md) — Full inventory

## MistHelper Notes

Not currently used by MistHelper directly. See `getOrgInventory` for Menu 12.
