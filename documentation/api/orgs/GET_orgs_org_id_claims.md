# listOrgAsyncClaims

> listOrgAsyncClaims

## HTTP

`GET /api/v1/orgs/{org_id}/claims`

## Description

List all async inventory claim jobs for the organization, optionally including per-device details per claim.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

### Query Parameters

| Name | Type | Required | Default | Enum | Description |
|------|------|----------|---------|------|-------------|
| detail | boolean | No |  |  | Whether to include per-device detail in each claim record |

## Request Body

None.

## Response

### 200

OK

```json
{
  "additionalProperties": false,
  "description": "List of async inventory claim jobs for the organization",
  "properties": {
    "claims": {
      "description": "Async claim job status records",
      "items": {
        "additionalProperties": false,
        "description": "Async inventory claim job status",
        "properties": {
          "claim_id": {
            "description": "Unique identifier of the async claim job",
            "format": "uuid",
            "type": "string"
          },
          "completed": {
            "description": "Device MAC addresses that completed asynchronous license claim processing",
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "details": {
            "description": "Per-device asynchronous license claim status details",
            "items": {
              "additionalProperties": false,
              "description": "Per-device asynchronous license claim status",
              "properties": {
                "mac": {
                  "description": "Device MAC address for this license claim detail",
                  "type": "string"
                },
                "status": {
                  "description": "Claim processing state for this device",
                  "type": "string"
                },
                "timestamp": {
                  "description": "Epoch timestamp, in seconds",
                  "format": "double",
                  "readOnly": true,
                  "type": "number"
                }
              },
              "type": "object"
            },
            "type": "array"
          },
          "failed": {
            "description": "Number of devices that failed claim processing",
            "type": "integer"
          },
          "incompleted": {
            "description": "Device MAC addresses not yet completed in asynchronous license claim processing",
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "org_id": {
            "description": "Unique identifier of a Mist organization",
            "examples": [
              "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61"
            ],
            "format": "uuid",
            "readOnly": true,
            "type": "string"
          },
          "processed": {
            "description": "Number of devices processed so far",
            "type": "integer"
          },
          "scheduled_at": {
            "description": "Epoch timestamp when the async claim was scheduled",
            "type": "integer"
          },
          "status": {
            "description": "Processing state for an asynchronous license claim. enum: `prepared`, `ongoing`, `done`",
            "enum": [
              "prepared",
              "ongoing",
              "done"
            ],
            "type": "string"
          },
          "succeed": {
            "description": "Number of devices that successfully completed claim processing",
            "type": "integer"
          },
          "timestamp": {
            "description": "Epoch timestamp, in seconds",
            "format": "double",
            "readOnly": true,
            "type": "number"
          },
          "total": {
            "description": "Total number of devices included in the claim",
            "type": "integer"
          }
        },
        "type": "object"
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

`mistapi.api.v1.orgs.claims.listOrgAsyncClaims()`

## Usage Context

Use this endpoint to read the resource at `/api/v1/orgs/{org_id}/claims`.
Common use cases:

- Use it when you need to list all async inventory claim jobs for the organization, optionally including per-device details per claim.
- Use it in an audit or status workflow before you make a related change.
- Treat this endpoint as a read-only request.
- The installed `mistapi` 0.64.0 signature is `listOrgAsyncClaims(mist_session: mistapi.__api_session.APISession, org_id: str, detail: bool | None = None) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `org_id`. Use identifiers from a trusted Mist read.
- Query parameters include `detail`. Keep filters narrow for repeatable results.

## Related Endpoints

- [POST_orgs_org_id_claims.md](POST_orgs_org_id_claims.md) -- createOrgAsyncClaim uses `POST /api/v1/orgs/{org_id}/claims`.
- [DELETE_orgs_org_id.md](DELETE_orgs_org_id.md) -- deleteOrg uses `DELETE /api/v1/orgs/{org_id}`.
- [DELETE_orgs_org_id_aamwprofiles_aamwprofile_id.md](DELETE_orgs_org_id_aamwprofiles_aamwprofile_id.md) -- deleteOrgAAMWProfile uses `DELETE /api/v1/orgs/{org_id}/aamwprofiles/{aamwprofile_id}`.

## MistHelper Notes

MistHelper does not currently call `listOrgAsyncClaims`.
Verification source: `git grep -n "listOrgAsyncClaims" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
