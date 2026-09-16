# deleteMspSsoAdmins

> deleteMspSsoAdmins

## HTTP

`POST /api/v1/msps/{msp_id}/ssos/{sso_id}/delete_admins`

## Description

Remove SSO-linked MSP administrator accounts by email for this SSO profile.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "additionalProperties": false,
  "description": "Request body listing SSO admin email addresses to delete",
  "properties": {
    "emails": {
      "description": "List of admin email addresses to delete",
      "items": {
        "type": "string"
      },
      "type": "array"
    }
  },
  "required": [
    "emails"
  ],
  "type": "object"
}
```

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "Result of deleting SSO admin accounts",
  "properties": {
    "deleted": {
      "description": "List of email addresses that were successfully deleted",
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "errors": {
      "description": "List of error messages for emails that could not be deleted",
      "items": {
        "type": "string"
      },
      "type": "array"
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

`mistapi.api.v1.msps.ssos.deleteMspSsoAdmins()`

## Usage Context

Use this endpoint to remove or stop the resource at
`/api/v1/msps/{msp_id}/ssos/{sso_id}/delete_admins`.
Common use cases:

- Use it when you need to remove SSO-linked MSP administrator accounts by email for this SSO profile.
- Use it only after you read the related resource and confirm the planned change.
- Treat this endpoint as a state-changing request.
- The installed `mistapi` 0.64.0 signature is `deleteMspSsoAdmins(mist_session: mistapi.__api_session.APISession, msp_id: str, sso_id: str, body: dict | list) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `msp_id`, `sso_id`. Use identifiers from a trusted Mist read.
- The JSON body requires `emails`. Missing required fields return a 400 response.
- This endpoint can change Mist state. Keep a recovery record before you call it.

## Related Endpoints

- [DELETE_msps_msp_id_ssos_sso_id.md](DELETE_msps_msp_id_ssos_sso_id.md) -- deleteMspSso uses `DELETE /api/v1/msps/{msp_id}/ssos/{sso_id}`.
- [GET_msps_msp_id_ssos_sso_id.md](GET_msps_msp_id_ssos_sso_id.md) -- getMspSso uses `GET /api/v1/msps/{msp_id}/ssos/{sso_id}`.
- [GET_msps_msp_id_ssos_sso_id_failures.md](GET_msps_msp_id_ssos_sso_id_failures.md) -- listMspSsoLatestFailures uses `GET /api/v1/msps/{msp_id}/ssos/{sso_id}/failures`.

## MistHelper Notes

MistHelper does not currently call `deleteMspSsoAdmins`.
Verification source: `git grep -n "deleteMspSsoAdmins" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
