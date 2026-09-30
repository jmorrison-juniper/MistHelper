# Research: Certificate Expiry Report

## R1. Mist portal source hierarchy and skill citations

Decision: Use local Mist API sources, the installed `mistapi` package, and the requested Mist skills.

Rationale: The OpenAPI file is authoritative for HTTP paths, parameters, and response shapes. The
installed SDK is authoritative for callable module names. The Mist skills identify the portal pages
and alert thresholds that explain why the report matters.

Skill citations:

- `juniper-mist-aiops/04-alerts/01-alerts-dashboard-categories-and-severity.md` says certificate
  alerts cover RadSec, SSO, and PSK Portal IdP certificates. It also states the `30`, `15`, `7`, `3`,
  and `1` day expiry alert calendar.
- `juniper-mist-aiops/04-alerts/02-certificate-and-infrastructure-alert-types.md` says certificate
  alerts are organization-scoped. It lists `Expired` as critical and `Expiring` as warning.
- `juniper-mist-management/03-security-and-access/02-password-policy-saml-and-certificates.md`
  says SSO certificates live under `Organization > Admin > Settings > Identity Providers`. It also
  says RadSec certificate management lives under the `Certificates` section.
- `juniper-mist-wireless/05-wlan-security-radius-and-psk/06-self-provisioning-roles-and-roaming-controls.md`
  says PSK portal IdP certificates are entered under `Organization > Access > Client Onboarding`.
- `juniper-mist-wan/02-sites-templates-and-onboarding/01-site-variables-and-deployment-order.md`
  says site variables are site configuration data. This report does not use site variables, so the
  WAN skill adds no certificate source to menu 272.

Alternatives considered: Use only operation names from assignment text. Rejected because OpenAPI and
SDK verification found two renamed endpoints that must be recorded.

## R2. Device certificate expiry source

Decision: Use `listOrgDevicesStats` for device `cert_expiry` values.

Rationale: `documentation/api/INDEX.md` maps `listOrgDevicesStats` to
`GET /api/v1/orgs/{org_id}/stats/devices`. The endpoint page shows `cert_expiry` as a nullable
number in device stats. The endpoint accepts `type`, `fields`, `limit`, and `page` query parameters.
The client must request `type=all` so the report includes access points, switches, and gateways.

Required operation contract:

- OperationId: `listOrgDevicesStats`
- Method and path: `GET /api/v1/orgs/{org_id}/stats/devices`
- SDK page: `mistapi.api.v1.orgs.stats.listOrgDevicesStats()`
- Required query: `type=all`
- Recommended query: `fields=cert_expiry,name,mac,type,site_id`

Alternatives considered: Use `listOrgDevices`. Rejected because its endpoint page documents `mac`
and `name`, but not `cert_expiry`.

## R3. Organization certificate and device certificate sources

Decision: Use `listOrgCertificates` and `getOrgSettings`.

Rationale: The assignment named `getOrgCertificates`, but OpenAPI has operationId
`listOrgCertificates` at `GET /api/v1/orgs/{org_id}/cert`. The installed SDK also exposes
`mistapi.api.v1.orgs.cert.listOrgCertificates()`. `getOrgSettings` holds `device_cert.cert`,
`cacerts`, and `mist_nac.server_cert.cert`. These fields map to organization CA, organization
device, RadSec CA, and NAC server certificate rows.

Required operation contracts:

- OperationId: `listOrgCertificates`
- Method and path: `GET /api/v1/orgs/{org_id}/cert`
- SDK page: `mistapi.api.v1.orgs.cert.listOrgCertificates()`
- Relevant fields: `cert`, `pending_cert`, and `pending_cert_expiry`

- OperationId: `getOrgSettings`
- Method and path: `GET /api/v1/orgs/{org_id}/setting`
- Relevant fields: `cacerts`, `device_cert.cert`, `mist_nac.cacerts`, and
  `mist_nac.server_cert.cert`

Alternatives considered: Use `getOrgCrlFile` or `getOrgNacCrl` for expiry rows. Rejected because the
OpenAPI `GET /api/v1/orgs/{org_id}/crl` operationId is `getOrgCrlFile` and returns a binary CRL file,
while `getOrgNacCrl` returns CRL file identifiers and URLs, not certificate expiry metadata. No
OpenAPI operationId named `listOrgCrl` exists.

## R4. SSO IdP certificate sources

Decision: Use `listOrgSsos` and `listOrgPskPortals`.

Rationale: The SSO endpoint exposes `idp_cert` for SAML IdP certificates and LDAP certificate fields.
The PSK portal endpoint exposes `sso.idp_cert`. These sources satisfy the SSO IdP and PSK portal IdP
scopes in the feature specification. NAC server certificate data comes from `getOrgSettings`.

Required operation contracts:

- OperationId: `listOrgSsos`
- Method and path: `GET /api/v1/orgs/{org_id}/ssos`
- SDK page: `mistapi.api.v1.orgs.sso.listOrgSsos()`
- Relevant fields: `idp_cert`, `ldap_cacerts`, and `ldap_client_cert`

- OperationId: `listOrgPskPortals`
- Method and path: `GET /api/v1/orgs/{org_id}/pskportals`
- SDK page: `mistapi.api.v1.orgs.psk_portals.listOrgPskPortals()`
- Relevant field: `sso.idp_cert`

Alternatives considered: Use NAC portal or SAML metadata download endpoints. Rejected for the first
implementation because the assignment does not require NAC portal IdP rows, and the list endpoints
already expose the required SSO and PSK portal certificate fields.

## R5. CRL source

Decision: Do not emit certificate expiry rows from the CRL endpoints.

Rationale: The assignment named `listOrgCrl`, but OpenAPI contains no such operationId. The matching
organization CRL endpoint is `getOrgCrlFile` at `GET /api/v1/orgs/{org_id}/crl`, and it returns a
binary file. The installed SDK exposes `mistapi.api.v1.orgs.crl.getOrgCrlFile()`. The NAC CRL
metadata endpoint is `getOrgNacCrl` at `GET /api/v1/orgs/{org_id}/setting/mist_nac_crls`, and it
returns CRL metadata. The installed SDK does not expose `getOrgNacCrl`, so the client will use
`apisession.mist_get()` for that metadata check. Neither response schema provides certificate expiry
rows.

Alternatives considered: Parse a CRL file during menu 272. Rejected because the feature output is a
certificate expiry report, while a CRL is a revocation list and can contain revoked certificate
entries rather than active certificate sources.

## R6. PEM parsing dependency

Decision: Import `cryptography` directly in the report package to parse PEM certificate values.

Rationale: The feature requires that valid PEM certificate strings parse through the `cryptography`
package. The implementation will use `cryptography.x509.load_pem_x509_certificate()` and will extract
metadata only. `requirements.txt` will receive an explicit pin during implementation.

Alternatives considered: Use the standard-library `ssl` module. Rejected because the feature
explicitly requires `cryptography`, and `ssl` does not provide the required direct PEM parsing model.

## R7. SourceDependencyResolver operation pattern

Decision: `operation.py` will import `SourceDependencyResolver` from
`src.config.source_dependency_resolver`.

Rationale: `src/security/rogue_dhcp/operation.py` and `src/marvis/actions/operation.py` resolve the
organization, session, and exporter through `SourceDependencyResolver`. The new operation must follow
the same pattern to avoid importing the root CLI module.

Alternatives considered: Pass the session and exporter through a standalone wrapper function.
Rejected because the constitution requires class-based behavior and forbids wrappers.

## R8. Export shape and primary key

Decision: Use one metadata-only row per certificate and export with endpoint name
`certificate_expiry_report`.

Rationale: `wiring.md` defines an `auto_increment_with_unique` primary key strategy with unique fields
`org_id`, `source_name`, `scope`, `owner_name`, `serial`, and `not_after`. This allows duplicate
subjects from different owners while preventing duplicate rows for the same certificate.

Alternatives considered: Use subject and issuer as the unique key. Rejected because multiple
certificates can share those fields.

## R9. Installed SDK callable-name verification during implementation

Decision: Use the installed SDK module names and signatures that were verified in the issue #3553
worktree.

Rationale: The implementation inspection found these callable names:

- `mistapi.api.v1.orgs.stats.listOrgDevicesStats(mist_session, org_id, ..., limit=None, page=None)`
- `mistapi.api.v1.orgs.setting.getOrgSettings(mist_session, org_id)`
- `mistapi.api.v1.orgs.cert.listOrgCertificates(mist_session, org_id)`
- `mistapi.api.v1.orgs.ssos.listOrgSsos(mist_session, org_id, limit=None, page=None)`
- `mistapi.api.v1.orgs.pskportals.listOrgPskPortals(mist_session, org_id, limit=None, page=None)`
- `mistapi.api.v1.orgs.crl.getOrgCrlFile(mist_session, org_id)`
- `getOrgNacCrl` has no installed SDK callable. The client uses `apisession.mist_get()`.

Implementation adjustments:

- Use `ssos`, not `sso`, for the SSO SDK module.
- Use `pskportals`, not `psk_portals`, for the PSK portal SDK module.
- Use `getOrgCrlFile` and `getOrgNacCrl` only as metadata evidence. Neither source creates active
  certificate expiry rows.

Alternatives considered: Use `getOrgCertificates`, `mistapi.api.v1.orgs.sso`, or
`mistapi.api.v1.orgs.psk_portals`. Rejected because the installed SDK exposes none of those names.
