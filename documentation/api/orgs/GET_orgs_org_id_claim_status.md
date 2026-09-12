# GetOrgLicenseAsyncClaimStatus

> GetOrgLicenseAsyncClaimStatus

## HTTP

`GET /api/v1/orgs/{org_id}/claim/status`

## Description

Get Processing Status for Async Claim

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
| detail | boolean | No |  |  | Request license details |

## Request Body

None.

## Response

### 200

OK

```json
{
  "type": "object",
  "properties": {
    "completed": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": ""
    },
    "details": {
      "type": "array",
      "items": {
        "title": "response_async_license_detail",
        "type": "object",
        "properties": {
          "mac": {
            "type": "string",
            "description": "Device MAC Address"
          },
          "status": {
            "type": "string"
          },
          "timestamp": {
            "type": "number",
            "description": "Epoch (seconds)",
            "readOnly": true
          }
        },
        "description": "detail claim status per device"
      },
      "description": ""
    },
    "failed": {
      "type": "integer",
      "description": "Current failed number of device",
      "contentEncoding": "int32"
    },
    "incompleted": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Current incompleted lists (macs)"
    },
    "processed": {
      "type": "integer",
      "description": "Current processed number of device",
      "contentEncoding": "int32"
    },
    "scheduled_at": {
      "type": "integer",
      "description": "epoch time of aysnc claim scheduled",
      "contentEncoding": "int32"
    },
    "status": {
      "type": "string",
      "description": "processing status of async. enum: `prepared`, `ongoing`, `done`"
    },
    "succeed": {
      "type": "integer",
      "description": "Current succeed number of device",
      "contentEncoding": "int32"
    },
    "timestamp": {
      "type": "number",
      "description": "Epoch (seconds)",
      "readOnly": true
    },
    "total": {
      "type": "integer",
      "description": "total number of device included in claim",
      "contentEncoding": "int32"
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

`mistapi.api.v1.orgs.licenses.GetOrgLicenseAsyncClaimStatus()`

## Usage Context

Checks the status of device claim operations for the organization.

## Gotchas

- Returns pending, success, and failed claim statuses.

## Related Endpoints

- [POST_orgs_org_id_inventory.md](POST_orgs_org_id_inventory.md) — Claim devices
- [GET_orgs_org_id_inventory.md](GET_orgs_org_id_inventory.md) — Org inventory

## MistHelper Notes

Not currently used by MistHelper directly.
