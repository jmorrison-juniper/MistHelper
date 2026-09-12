# listOrgDevicesSummary

> listOrgDevicesSummary

## HTTP

`GET /api/v1/orgs/{org_id}/devices/summary`

## Description

Get Org Devices Summary

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
    "num_aps": {
      "type": "integer",
      "contentEncoding": "int32",
      "readOnly": true
    },
    "num_gateways": {
      "type": "integer",
      "contentEncoding": "int32",
      "readOnly": true
    },
    "num_mxedges": {
      "type": "integer",
      "contentEncoding": "int32",
      "readOnly": true
    },
    "num_switches": {
      "type": "integer",
      "contentEncoding": "int32",
      "readOnly": true
    },
    "num_unassigned_aps": {
      "type": "integer",
      "contentEncoding": "int32",
      "readOnly": true
    },
    "num_unassigned_gateways": {
      "type": "integer",
      "contentEncoding": "int32",
      "readOnly": true
    },
    "num_unassigned_switches": {
      "type": "integer",
      "contentEncoding": "int32",
      "readOnly": true
    }
  }
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

`mistapi.api.v1.orgs.devices.listOrgDevicesSummary()`

## Usage Context

Retrieves a summary of all devices in the organization with aggregate statistics.

## Gotchas

- Provides counts by type, model, firmware version, and status.

## Related Endpoints

- [GET_orgs_org_id_devices_search.md](GET_orgs_org_id_devices_search.md) — Search devices
- [GET_orgs_org_id_devices_count.md](GET_orgs_org_id_devices_count.md) — Count devices

## MistHelper Notes

Not currently used by MistHelper directly.
