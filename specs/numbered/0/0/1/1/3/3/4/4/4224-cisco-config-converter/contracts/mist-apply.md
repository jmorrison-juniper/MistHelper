# Mist Apply Contract: Deferred

## Operation

- SDK operation: `createOrgGatewayTemplate`
- Mist API operation: `POST /api/v1/orgs/{org_id}/gatewaytemplates`
- SDK module: `mistapi.api.v1.orgs.gatewaytemplates`
- SDK signature: `createOrgGatewayTemplate(mist_session, org_id, body)`
- Request body: gateway-template schema in `documentation/mist-api-openapi31json.json`
- Transport: the supported `mistapi` 0.64.x SDK only
- Verified fields: required `name`, type `standalone` or `spoke`, and optional `dns_servers`
  as an array of strings
- Documented responses: HTTP 200, 400, 401, 403, 404, and 429

The first release supports preview, review, and JSON export only. It does not call the Mist API
or create a gateway template. A verified SDK contract does not authorize a cloud change.

## Future Apply Gate

Cloud apply remains outside this release. Before a future apply feature, obtain separate scope
and approval for the cloud effect. Define organization selection, confirmation, failure
handling, retry policy, and contract tests. Use the verified SDK operation only. Do not add
wrapper fields or settings derived from unsupported Cisco commands.
