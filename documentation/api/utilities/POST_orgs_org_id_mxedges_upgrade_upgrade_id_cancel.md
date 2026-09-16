# cancelOrgMxEdgeUpgrade

> cancelOrgMxEdgeUpgrade

## HTTP

`POST /api/v1/orgs/{org_id}/mxedges/upgrade/{upgrade_id}/cancel`

## Description

Cancel a Mist Edge upgrade request on a best-effort basis. Mist Edges that have already been upgraded are not changed.

## Authentication

Requires API token authentication (`Authorization: Token {api_token}` header or `X-CSRFToken` cookie). See Mist API authentication documentation.

## Parameters

None.

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

`mistapi.api.v1.orgs.mxedges.cancelOrgMxEdgeUpgrade()`

## Usage Context

Use this endpoint to remove or stop the resource at
`/api/v1/orgs/{org_id}/mxedges/upgrade/{upgrade_id}/cancel`.
Common use cases:

- Use it when you need to cancel a Mist Edge upgrade request on a best-effort basis.
- Use it only after you read the related resource and confirm the planned change.
- Treat this endpoint as a state-changing request.
- The installed `mistapi` 0.64.0 signature is `cancelOrgMxEdgeUpgrade(mist_session: mistapi.__api_session.APISession, org_id: str, upgrade_id: str) -> mistapi.__api_response.APIResponse`.

## Gotchas

- The path requires `org_id`, `upgrade_id`. Use identifiers from a trusted Mist read.
- This endpoint can change Mist state. Keep a recovery record before you call it.
- Upgrade calls can interrupt service. Use an approved maintenance window.

## Related Endpoints

- [GET_orgs_org_id_mxedges_upgrade_upgrade_id.md](GET_orgs_org_id_mxedges_upgrade_upgrade_id.md) -- getOrgMxEdgeUpgrade uses `GET /api/v1/orgs/{org_id}/mxedges/upgrade/{upgrade_id}`.
- [PUT_orgs_org_id_mxedges_upgrade_upgrade_id.md](PUT_orgs_org_id_mxedges_upgrade_upgrade_id.md) -- updateOrgMxEdgeUpgrade uses `PUT /api/v1/orgs/{org_id}/mxedges/upgrade/{upgrade_id}`.
- [GET_orgs_org_id_mxedges_upgrade.md](GET_orgs_org_id_mxedges_upgrade.md) -- listOrgMxEdgeUpgrades uses `GET /api/v1/orgs/{org_id}/mxedges/upgrade`.

## MistHelper Notes

MistHelper does not currently call `cancelOrgMxEdgeUpgrade`.
Verification source: `git grep -n "cancelOrgMxEdgeUpgrade" -- src MistHelper.py`.
`src/export/endpoint_catalog.py` does not list this operation as an endpoint family row.
