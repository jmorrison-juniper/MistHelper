# rebootOrgOtherDevice

> rebootOrgOtherDevice

## HTTP

`POST /api/v1/orgs/{org_id}/otherdevices/{device_mac}/reboot`

## Description

Reboot OtherDevice

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| org_id | string | Yes |  |
| device_mac | string | Yes |  |

## Request Body

None.

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

`mistapi.api.v1.orgs.devices_-_others.rebootOrgOtherDevice()`

## Usage Context

Reboots an "other device" (non-Juniper) by MAC address.

## Gotchas

- Only supported for devices with reboot capability via Mist.

## Related Endpoints

- [GET_orgs_org_id_stats_otherdevices.md](GET_orgs_org_id_otherdevices.md) — Other device stats

## MistHelper Notes

Not currently used by MistHelper directly.
