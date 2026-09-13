# setSiteDevicesGbpTag

> setSiteDevicesGbpTag

## HTTP

`POST /api/v1/sites/{site_id}/devices/gbp_tag`

## Description

Set GBP Tag for multiple devices

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| site_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "gbp_tag": {
      "type": "integer",
      "contentEncoding": "int32"
    },
    "macs": {
      "minItems": 1,
      "uniqueItems": true,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "",
      "examples": [
        [
          "683b679ac024"
        ]
      ]
    }
  },
  "required": [
    "gbp_tag",
    "macs"
  ],
  "description": "Request Body"
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

`mistapi.api.v1.sites.devices.setSiteDevicesGbpTag()`

## Usage Context

Assigns Group-Based Policy (GBP) tags to devices. GBP tags are used for micro-segmentation.

## Gotchas

- GBP requires EVPN-VXLAN fabric configuration.

## Related Endpoints

- [GET_sites_site_id_devices.md](GET_sites_site_id_devices.md) — List devices
- [GET_sites_site_id_evpn_topologies.md](GET_sites_site_id_evpn_topologies.md) — EVPN topologies

## MistHelper Notes

Not currently used by MistHelper directly.
