# Client Contract: NAC IDP Credential Test

## Provider list contract

`NacIdpCredentialClient.list_identity_providers()` returns `list[IdentityProviderChoice]`.

### Primary source

- Operation: `getOrgSettings`
- Method and path: `GET /api/v1/orgs/{org_id}/setting`
- Path parameter: `org_id` as a UUID string
- Field path: `mist_nac.idps`
- Provider identifier: `id`

### Fallback source

- Operation: `listOrgSsos`
- Method and path: `GET /api/v1/orgs/{org_id}/ssos`
- Path parameter: `org_id` as a UUID string
- Query parameters: `limit` and `page`
- Provider identifier: `id`

The fallback exists for evidence only. The operation labels fallback rows as SSO rows, because organization SSO is not the same control point as NAC identity providers.

## Validation contract

`NacIdpCredentialClient.validate_credential(request)` returns `CredentialTestResult`.

- Operation: `validateOrgIdpCredential`
- Method and path: `POST /api/v1/orgs/{org_id}/mist_nac/test_idp`
- Path parameter: `org_id` as a UUID string
- Body: `{"idp_id": string, "username": string, "password": string}`
- Success response: HTTP `200` with response data that includes `status: success`
- Failure response: HTTP `200` with `status: failure` or HTTP `4xx` with an error payload

## Export contract

The operation writes `NacIdpCredentialTest.csv` through `DataExporter.write_with_format_selection`.

Required field order:

1. `tested_at`
2. `idp_id`
3. `idp_name`
4. `idp_type`
5. `idp_source`
6. `username`
7. `verdict`
8. `reason`
9. `attributes`

The export contract forbids a `password` column.
