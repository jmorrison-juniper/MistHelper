# getOrgEdgeconnectRegisterCmd

> getOrgEdgeconnectRegisterCmd

## HTTP

`GET /api/v1/orgs/{org_id}/edgeconnect/register_cmd`

## Description

Returns a registration code for adopting an EdgeConnect device into Mist.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

EdgeConnect Registration Command

```json
{
  "additionalProperties": false,
  "description": "EdgeConnect device registration command response",
  "properties": {
    "registration_code": {
      "description": "Registration code used to adopt an EdgeConnect device into Mist",
      "type": "string"
    }
  },
  "type": "object"
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

`mistapi.api.v1.orgs.edgeconnect.getOrgEdgeconnectRegisterCmd()`

## Usage Context

Use this endpoint to read the resource at
`/api/v1/orgs/{org_id}/edgeconnect/register_cmd`.
Common use cases:

- Use it when you need to returns a registration code for adopting an EdgeConnect device into Mist.
- Use it in an audit or status workflow before you make a related change.
- Treat this endpoint as a read-only request.
- The installed `mistapi` 0.64.0 signature is `getOrgEdgeconnectRegisterCmd(mist_session: mistapi.__api_session.APISession, org_id: str) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `org_id`. Use identifiers from a trusted Mist read.

## Related Endpoints

- [DELETE_orgs_org_id.md](DELETE_orgs_org_id.md) -- deleteOrg uses `DELETE /api/v1/orgs/{org_id}`.
- [DELETE_orgs_org_id_aamwprofiles_aamwprofile_id.md](DELETE_orgs_org_id_aamwprofiles_aamwprofile_id.md) -- deleteOrgAAMWProfile uses `DELETE /api/v1/orgs/{org_id}/aamwprofiles/{aamwprofile_id}`.
- [DELETE_orgs_org_id_admins_admin_id.md](DELETE_orgs_org_id_admins_admin_id.md) -- revokeOrgAdmin uses `DELETE /api/v1/orgs/{org_id}/admins/{admin_id}`.

## MistHelper Notes

MistHelper does not currently call `getOrgEdgeconnectRegisterCmd`.
Verification source: `git grep -n "getOrgEdgeconnectRegisterCmd" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
