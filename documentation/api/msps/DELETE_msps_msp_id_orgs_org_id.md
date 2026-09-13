# deleteMspOrg

> deleteMspOrg

## HTTP

`DELETE /api/v1/msps/{msp_id}/orgs/{org_id}`

## Description

Delete MSP Org

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |
| org_id | string | Yes |  |

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

`mistapi.api.v1.msps.orgs.deleteMspOrg()`

## Usage Context

Removes an organization from MSP management. The org may continue to exist as a standalone Mist org but loses MSP-level administration, license pooling, and centralized management.

## Gotchas

- Removing an org from MSP management does not delete the org itself — it becomes independent.
- Licenses that were pooled from the MSP may be reclaimed, potentially affecting the org's feature availability.

## Related Endpoints

- [GET_msps_msp_id_orgs.md](GET_msps_msp_id_orgs.md) — List orgs to identify the target
- [GET_msps_msp_id_orgs_org_id.md](GET_msps_msp_id_orgs_org_id.md) — Verify org details before removal
- [PUT_msps_msp_id_orgs.md](PUT_msps_msp_id_orgs.md) — Bulk org management as an alternative

## MistHelper Notes

Not currently used by MistHelper directly.
