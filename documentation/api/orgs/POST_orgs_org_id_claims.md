# createOrgAsyncClaim

> createOrgAsyncClaim

## HTTP

`POST /api/v1/orgs/{org_id}/claims`

## Description

Schedules an async claim for inventory devices. Inventory claiming is queued and processed in the background; the response returns immediately with a `claim_id` for polling. Licenses (if `type=all`) are still claimed synchronously during the request.

Use `GET /api/v1/orgs/{org_id}/claims/{claim_id}` to poll the result.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

## Request Body

Content-Type: `application/json`

```json
{
  "description": "Request to schedule an asynchronous inventory claim",
  "properties": {
    "code": {
      "description": "Activation code to claim",
      "type": "string"
    },
    "device_type": {
      "default": "ap",
      "description": "enum: `ap`, `gateway`, `switch`",
      "enum": [
        "ap",
        "gateway",
        "switch"
      ],
      "type": "string"
    },
    "type": {
      "description": "Claim scope for async inventory claiming. enum: `all`, `inventory`",
      "enum": [
        "all",
        "inventory"
      ],
      "type": "string"
    }
  },
  "required": [
    "code",
    "type"
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
  "description": "Response to an async inventory claim request",
  "properties": {
    "claim_id": {
      "description": "Unique identifier for the async claim job, used to poll status",
      "format": "uuid",
      "type": "string"
    },
    "inventory_pending": {
      "description": "Inventory devices pending asynchronous claim processing",
      "items": {
        "additionalProperties": false,
        "description": "Inventory device pending asynchronous claim processing",
        "properties": {
          "mac": {
            "description": "Device MAC address pending asynchronous inventory claim",
            "type": "string"
          }
        },
        "type": "object"
      },
      "type": "array",
      "uniqueItems": true
    }
  },
  "type": "object"
}
```

## Errors

| Status | Description |
|--------|-------------|
| 400 | Invalid key (or already used) |
| 401 | Unauthorized |
| 403 | Permission Denied |
| 404 | Not found. The API endpoint doesn’t exist or resource doesn’ t exist |
| 429 | Too Many Request. The API Token used for the request reached the 5000 API Calls per hour threshold |

## Pagination

Not paginated.

## Rate Limiting

Standard Mist API rate limits apply.

## mistapi SDK

`mistapi.api.v1.orgs.claims.createOrgAsyncClaim()`

## Usage Context

Use this endpoint to start or create the resource at `/api/v1/orgs/{org_id}/claims`.
Common use cases:

- Use it when you need to schedules an async claim for inventory devices.
- Use it only after you read the related resource and confirm the planned change.
- Treat this endpoint as a state-changing request.
- The installed `mistapi` 0.64.0 signature is `createOrgAsyncClaim(mist_session: mistapi.__api_session.APISession, org_id: str, body: dict | list) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `org_id`. Use identifiers from a trusted Mist read.
- The JSON body requires `code`, `type`. Missing required fields return a 400 response.
- This endpoint can change Mist state. Keep a recovery record before you call it.

## Related Endpoints

- [GET_orgs_org_id_claims.md](GET_orgs_org_id_claims.md) -- listOrgAsyncClaims uses `GET /api/v1/orgs/{org_id}/claims`.
- [DELETE_orgs_org_id.md](DELETE_orgs_org_id.md) -- deleteOrg uses `DELETE /api/v1/orgs/{org_id}`.
- [DELETE_orgs_org_id_aamwprofiles_aamwprofile_id.md](DELETE_orgs_org_id_aamwprofiles_aamwprofile_id.md) -- deleteOrgAAMWProfile uses `DELETE /api/v1/orgs/{org_id}/aamwprofiles/{aamwprofile_id}`.

## MistHelper Notes

MistHelper does not currently call `createOrgAsyncClaim`.
Verification source: `git grep -n "createOrgAsyncClaim" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
