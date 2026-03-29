# moveOrDeleteOrgLicenseToAnotherOrg

> moveOrDeleteOrgLicenseToAnotherOrg

## HTTP

`PUT /api/v1/orgs/{org_id}/licenses`

## Description

Move, Undo Move or Delete Org License to Another Org
If the admin has admin privilege against the `org_id` and `dst_org_id`, he can move some of the licenses to another Org. Given that: 
1. the specified license is currently active 
2. there’s enough licenses left in the specified license (by subscription_id) 
3. there will still be enough entitled licenses for the type of license after the amendment

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
    "amendment_id": {
      "type": "string",
      "description": "If `op`==`unamend`, the ID of the operation to cancel",
      "contentEncoding": "uuid"
    },
    "dst_org_id": {
      "type": "string",
      "description": "If `op`==`amend`, the id of the org where the license is moved",
      "contentEncoding": "uuid"
    },
    "notes": {
      "type": "string",
      "description": "If `op`==`annotate`"
    },
    "op": {
      "type": "string",
      "description": "to move a license, use the `amend` operation. enum: `amend`, `annotate`, `delete`, `unamend`"
    },
    "quantity": {
      "type": "integer",
      "description": "If `op`==`amend`, the number of licenses to move",
      "contentEncoding": "int32"
    },
    "subscription_id": {
      "type": "string",
      "description": "If `op`==`amend` or `op`==`delete`, the ID of the subscription to use"
    }
  },
  "required": [
    "op"
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

`mistapi.api.v1.orgs.licenses.moveOrDeleteOrgLicenseToAnotherOrg()`

## Usage Context

Updates license assignments or subscriptions for the organization.

## Gotchas

- License changes may affect feature availability across sites.

## Related Endpoints

- [GET_orgs_org_id_licenses.md](GET_orgs_org_id_licenses.md) — Get licenses
- [GET_orgs_org_id_licenses_summary.md](GET_orgs_org_id_licenses.md) — License summary

## MistHelper Notes

License info uses Menu 19 (`getOrgLicensesSummary`). Update is not used directly.
