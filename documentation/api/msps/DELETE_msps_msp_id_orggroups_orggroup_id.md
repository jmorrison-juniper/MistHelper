# deleteMspOrgGroup

> deleteMspOrgGroup

## HTTP

`DELETE /api/v1/msps/{msp_id}/orggroups/{orggroup_id}`

## Description

Delete MSP Org Group

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| msp_id | string | Yes |  |
| orggroup_id | string | Yes |  |

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

`mistapi.api.v1.msps.org_groups.deleteMspOrgGroup()`

## Usage Context

Deletes an MSP organization group. This removes the logical grouping but does not affect the member organizations themselves — they remain under MSP management.

## Gotchas

- Deletion removes the group only, not the organizations within it.
- Any automated workflows or reports referencing this org group will need to be updated.

## Related Endpoints

- [GET_msps_msp_id_orggroups.md](GET_msps_msp_id_orggroups.md) — List org groups to verify before deletion
- [POST_msps_msp_id_orggroups.md](POST_msps_msp_id_orggroups.md) — Create a replacement group if needed

## MistHelper Notes

Not currently used by MistHelper directly.
