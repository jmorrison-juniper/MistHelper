# Research: NAC IDP Credential Test

## Decision 1: Validate credential endpoint

**Decision**: Use `POST /api/v1/orgs/{org_id}/mist_nac/test_idp` through `mistapi.api.v1.orgs.mist_nac.validateOrgIdpCredential(apisession, org_id, body)`.

**Rationale**: The OpenAPI operationId is `validateOrgIdpCredential`. It has path parameter `org_id` as a UUID. The SDK exposes the same function with signature `(mist_session, org_id, body)`. The SDK sends the body with `mist_session.mist_post` to `/api/v1/orgs/{org_id}/mist_nac/test_idp`.

**Alternatives considered**: A raw `apisession.mist_post` call was not selected because the installed SDK has the function.

## Decision 2: Request body shape

**Decision**: Build the body as `{"idp_id": <id>, "username": <username>, "password": <password>}`.

**Rationale**: The feature issue requires `idp_id`, `username`, and `password`. The OpenAPI schema references `username_password`, which defines `username` and `password`. It does not set `additionalProperties` to `false`, so `idp_id` can be included. The endpoint response examples return `idp_id` and `idp_type`, and the no-match example says `No matching IDP found`, which shows that Mist selects an identity provider for the credential test.

**Alternatives considered**: Sending only `username` and `password` would match the narrow schema, but it would not test the operator-selected provider.

## Decision 3: Identity provider source

**Decision**: Use `getOrgSettings` and read `mist_nac.idps` for NAC identity provider identifiers. Use `listOrgSsos` only as a named fallback for SSO context. Record that `listOrgNacIdps` does not exist in the OpenAPI file or installed SDK.

**Rationale**: The OpenAPI schema `org_setting_mist_nac` contains `idps`, and each `org_setting_mist_nac_idp` contains `id` as a UUID and `user_realms`. The installed SDK exposes `getOrgSettings`. The OpenAPI file and SDK expose `listOrgSsos`, but that endpoint returns organization SSO providers for portal login. It does not represent Access Assurance NAC identity providers. The installed SDK has no `mistapi.api.v1.orgs.nac.listOrgNacIdps` module or function.

**Alternatives considered**: `listOrgSsos` was rejected as the primary source because it covers organization SSO. A nonexistent `listOrgNacIdps` function was rejected because neither OpenAPI nor SDK expose it.

## Decision 4: Response normalization

**Decision**: Normalize `response.data` from the validation call into a `CredentialTestResult`. Treat `status == "success"` as success. Treat `status == "failure"`, HTTP status `>=400`, or an `error` field as failure.

**Rationale**: The endpoint description shows WebSocket response examples with `status`, `error`, `idp_id`, and `idp_type`. It also says more attributes can be added later. The model must keep unknown attributes so operators can see returned groups or attributes.

**Alternatives considered**: A fixed group-only schema was rejected because the endpoint description says more attributes can be added later.

## Decision 5: Secret handling

**Decision**: Use `getpass.getpass` for the password prompt. Never log the password, never store it in the result model, and never export it.

**Rationale**: Access Assurance skill guidance states that Entra ID and Okta credential validation uses user credentials for EAP-TTLS style flows. The same page says `NAC IDP Authentication Success` proves that the IdP validated credentials. Credential safety is mandatory for a cutover check. Source: `juniper-access-assurance-nac/04-certificates-identity/02-public-idp-and-ldaps-integration.md`.

**Alternatives considered**: `InputUtils.safe_input` was rejected for the password because it echoes typed input.

## Decision 6: Failure evidence wording

**Decision**: Print the API failure reason and recommend checking the identity provider configuration outside the operation.

**Rationale**: Mist management guidance for SSO failures says operators should inspect failure evidence, including IdP, attributes, and audit evidence. Source: `juniper-mist-management/01-accounts-and-roles/03-global-login-and-sso.md`.

**Alternatives considered**: Raising an exception was rejected because acceptance criteria require no traceback on failed validation.

## Decision 7: API call framing

**Decision**: Keep all Mist calls under the organization scope and use the regional API host already held by the active `apisession`.

**Rationale**: Mist automation guidance states that the API host names the regional cloud, and the path after the host names the scope and object. Source: `juniper-mist-automation/01-rest-api-model/01-call-structure-and-http-methods.md`.

**Alternatives considered**: Building a host manually was rejected because MistHelper already owns the authenticated session.
