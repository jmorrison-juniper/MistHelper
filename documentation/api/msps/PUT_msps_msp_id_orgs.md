# manageMspOrgs

> manageMspOrgs

## HTTP

`PUT /api/v1/msps/{msp_id}/orgs`

## Description

Assign or Unassign Orgs to an MSP account

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
    "op": {
      "type": "string",
      "description": "enum: `assign`, `unassign`"
    },
    "org_ids": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of org_id"
    }
  },
  "required": [
    "op",
    "org_ids"
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

`mistapi.api.v1.msps.orgs.manageMspOrgs()`

## Usage Context

Bulk-manages organizations under an MSP — allows adopting, releasing, or modifying multiple organizations in a single request. Use this for batch operations when onboarding or offboarding multiple customer organizations simultaneously.

## Gotchas

- This is a bulk operation that affects multiple orgs at once — verify the org list carefully before executing.
- Some operations (like releasing an org) may be irreversible.

## Related Endpoints

- [GET_msps_msp_id_orgs.md](GET_msps_msp_id_orgs.md) — List current orgs to build the bulk operation list
- [PUT_msps_msp_id_orgs_org_id.md](PUT_msps_msp_id_orgs_org_id.md) — Update a single org
- [POST_msps_msp_id_orgs.md](POST_msps_msp_id_orgs.md) — Create individual orgs

## MistHelper Notes

Not currently used by MistHelper directly.
