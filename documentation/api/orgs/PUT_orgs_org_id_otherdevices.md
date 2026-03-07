# updateOrgOtherDevices

> updateOrgOtherDevices

## HTTP

`PUT /api/v1/orgs/{org_id}/otherdevices`

## Description

Assign or unassign OtherDevices to and from a site.

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
    "macs": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "MAC address of the peer device."
    },
    "op": {
      "type": "string",
      "description": "The operation being performed. enum: `assign`, `unassign`"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid"
    }
  },
  "required": [
    "op"
  ]
}
```

## Response

### 200

OK

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

`mistapi.api.v1.orgs.devices_-_others.updateOrgOtherDevices()`

## Usage Context

Bulk-updates "other device" entries in the organization.

## Gotchas

- Accepts an array of device MAC and update payloads.

## Related Endpoints

- [PUT_orgs_org_id_otherdevices_device_mac.md](PUT_orgs_org_id_otherdevices_device_mac.md) — Update single
- [GET_orgs_org_id_stats_otherdevices.md](GET_orgs_org_id_stats_otherdevices.md) — Stats

## MistHelper Notes

Not currently used by MistHelper directly.
