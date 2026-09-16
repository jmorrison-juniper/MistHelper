# disableOrgE911Report

> disableOrgE911Report

## HTTP

`DELETE /api/v1/orgs/{org_id}/exports/e911_report`

## Description

Disable automatic E911 AP BSSID report generation for the organization.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

None.

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "E911 AP BSSID report status for the organization",
  "properties": {
    "detail": {
      "description": "Human-readable description of the action taken",
      "type": "string"
    },
    "last_generated": {
      "description": "Unix timestamp of when the report file was last generated. Only present when `status` is `available`.",
      "type": "integer"
    },
    "status": {
      "description": "Current status of E911 report generation. enum: `disabled`, `scheduled`, `available`",
      "enum": [
        "disabled",
        "scheduled",
        "available"
      ],
      "type": "string"
    },
    "url": {
      "description": "Presigned URL to download the CSV file. Only present when `status` is `available`.",
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

`mistapi.api.v1.orgs.exports.disableOrgE911Report()`

## Usage Context

Use this endpoint to remove or stop the resource at
`/api/v1/orgs/{org_id}/exports/e911_report`.
Common use cases:

- Use it when you need to disable automatic E911 AP BSSID report generation for the organization.
- Use it only after you read the related resource and confirm the planned change.
- Treat this endpoint as a state-changing request.
- The installed `mistapi` 0.64.0 signature is `disableOrgE911Report(mist_session: mistapi.__api_session.APISession, org_id: str) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `org_id`. Use identifiers from a trusted Mist read.
- This endpoint can change Mist state. Keep a recovery record before you call it.

## Related Endpoints

- [GET_orgs_org_id_exports_e911_report.md](GET_orgs_org_id_exports_e911_report.md) -- getOrgE911Report uses `GET /api/v1/orgs/{org_id}/exports/e911_report`.
- [POST_orgs_org_id_exports_e911_report.md](POST_orgs_org_id_exports_e911_report.md) -- enableOrgE911Report uses `POST /api/v1/orgs/{org_id}/exports/e911_report`.
- [DELETE_orgs_org_id.md](DELETE_orgs_org_id.md) -- deleteOrg uses `DELETE /api/v1/orgs/{org_id}`.

## MistHelper Notes

MistHelper does not currently call `disableOrgE911Report`.
Verification source: `git grep -n "disableOrgE911Report" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
