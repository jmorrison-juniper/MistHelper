# updateOrgOtherDevice

> updateOrgOtherDevice

## HTTP

`PUT /api/v1/orgs/{org_id}/otherdevices/{device_mac}`

## Description

If the Site / Device cannot be identified, a manual association can be made

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| device_mac | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "device_mac": {
      "type": "string"
    },
    "site_id": {
      "type": "string",
      "contentEncoding": "uuid",
      "examples": [
        "43e9c864-a7e4-4310-8031-d9817d2c5a43"
      ]
    }
  }
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

`mistapi.api.v1.orgs.devices_-_others.updateOrgOtherDevice()`

## Usage Context

Updates an "other device" (non-Juniper) entry by MAC address.

## Gotchas

- Limited to devices that Mist can manage via its other-device framework.

## Related Endpoints

- [GET_orgs_org_id_stats_otherdevices.md](GET_orgs_org_id_otherdevices.md) — Stats
- [PUT_orgs_org_id_otherdevices.md](PUT_orgs_org_id_otherdevices.md) — Bulk update

## MistHelper Notes

Not currently used by MistHelper directly.
