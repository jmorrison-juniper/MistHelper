# Mist Apply Contract: Create Gateway Template

## Operation

- SDK operation: `createOrgGatewayTemplate`
- Mist API operation: `POST /api/v1/orgs/{org_id}/gatewaytemplates`
- Request body: `gateway_template` schema in `documentation/mist-api-openapi31json.json`
- Transport: the supported `mistapi` 0.64.x SDK only
- Scope: create one new organization gateway template from the reviewed proposal

Before implementation, obtain product-owner approval for creating a new organization gateway template as the required cloud effect. The issue does not confirm this exact operation or a site assignment. Then verify the SDK module path, function signature, authentication behavior, accepted payload, and response against the installed SDK. The local planning workspace does not have `mistapi` installed. If the effect is not approved, revise this contract and the spec. If the SDK operation is absent or incompatible, stop and revise this contract before implementation. Do not replace it with direct HTTP.

## Preconditions

1. The proposal is complete and reviewed.
2. The selected role and hardware model still match the proposal.
3. The Mist session is valid and the operator can access the selected organization.
4. The operator types the required confirmation phrase.
5. The proposal passes the verified gateway template request schema.

If any precondition fails, make no SDK call.

## Result

- On a confirmed SDK success, report template creation and show the returned template identifier when present.
- On an SDK failure, report failure without exposing credentials or claiming the template was created.
- On an interrupted request without a definitive response, report an indeterminate result and do not retry automatically.
- Do not update or delete an existing template, assign the new template to a site, or apply it to a device in this feature.

## Required Contract Tests

- Verify the SDK call uses the operator's Mist session and selected organization.
- Verify the request matches the SDK operation's accepted payload and endpoint.
- Verify missing credentials and rejected confirmation make zero SDK calls.
- Verify an SDK error does not produce a success result.
- Verify an interrupted or ambiguous result is not retried automatically.
- Verify logs and operator-facing errors do not expose tokens or passwords.
