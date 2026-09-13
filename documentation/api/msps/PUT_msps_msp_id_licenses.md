# moveOrDeleteMspLicenseToAnotherOrg

> moveOrDeleteMspLicenseToAnotherOrg

## HTTP

`PUT /api/v1/msps/{msp_id}/licenses`

## Description

Move or Delete MSP Licenses

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |

## Request Body

Content-Type: `application/json`

```json
{
  "type": "object",
  "properties": {
    "amendment_id": {
      "type": "string",
      "description": "Required if `op`==`unamend`"
    },
    "dst_org_id": {
      "type": "string",
      "description": "Required if `op`==`amend`, destination org id",
      "contentEncoding": "uuid"
    },
    "notes": {
      "type": "string",
      "description": "Required if `op`==`annotate`"
    },
    "op": {
      "type": "string",
      "description": "enum: `amend`, `annotate`, `delete`, `unamend`"
    },
    "quantity": {
      "type": "number",
      "description": "Required if `op`==`amend`"
    },
    "subscription_id": {
      "minLength": 1,
      "type": "string",
      "description": "Required if `op`==`annotate`"
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

`mistapi.api.v1.msps.licenses.moveOrDeleteMspLicenseToAnotherOrg()`

## Usage Context

Moves licenses between organizations within the MSP pool or releases them back to the unallocated pool. Use this to rebalance license allocations when sites grow, shrink, or are decommissioned.

## Gotchas

- Moving a license away from an org may immediately reduce that org's feature availability if it drops below the required license count.
- Licenses with device-specific assignments may need to be unbound before moving.

## Related Endpoints

- [GET_msps_msp_id_licenses.md](GET_msps_msp_id_licenses.md) — View current license pool state
- [POST_msps_msp_id_claim.md](POST_msps_msp_id_claim.md) — Add new licenses to the pool
- [GET_msps_msp_id_stats_licenses.md](GET_msps_msp_id_stats_licenses.md) — Per-org license usage statistics

## MistHelper Notes

Not currently used by MistHelper directly.
