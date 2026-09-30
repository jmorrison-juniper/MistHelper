# Research: Admin Token Hygiene

## Decision: Use installed `mistapi` functions for Mist API reads

**Rationale**: The virtual environment at
`C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene\.venv\Scripts\python.exe`
confirmed all needed SDK functions. The constitution prohibits direct HTTP
calls when an SDK function exists.

**SDK locations confirmed with the requested interpreter**:

| Operation ID | SDK function | File | Signature |
| - | - | - | - |
| `listOrgAdmins` | `mistapi.api.v1.orgs.admins.listOrgAdmins` | `C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene\.venv\Lib\site-packages\mistapi\api\v1\orgs\admins.py` | `(mist_session, org_id)` |
| `listOrgApiTokens` | `mistapi.api.v1.orgs.apitokens.listOrgApiTokens` | `C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene\.venv\Lib\site-packages\mistapi\api\v1\orgs\apitokens.py` | `(mist_session, org_id)` |
| `getOrgSettings` | `mistapi.api.v1.orgs.setting.getOrgSettings` | `C:\Users\jmorrison\mh-fleet\3554-admin-token-hygiene\.venv\Lib\site-packages\mistapi\api\v1\orgs\setting.py` | `(mist_session, org_id)` |

**Alternatives considered**:

- Direct `mist_get()` calls. Rejected because SDK functions exist.
- Reusing menu 47 and 48 outputs as input. Rejected because the report must run
  in one operation and must avoid writing token keys to intermediate files.

## Decision: Use three Mist API operation IDs

**Rationale**: `documentation/mist-api-openapi3json.json` contains the required
operation IDs.

### `listOrgAdmins`

- Method and path: `GET /api/v1/orgs/{org_id}/admins`
- Path parameters: `org_id`, required UUID string.
- Query parameters: none.
- Request body: none.
- Success response: `200` returns an array of `admin` objects.
- Useful response fields: `admin_id`, `email`, `first_name`, `last_name`,
  `name`, `privileges`, `enable_two_factor`, `two_factor_verified`,
  `via_sso`, `password_modified_time`, `expire_time`, `compliance_status`,
  `session_expiry`, `tags`, `hours`, `oauth_google`, and `no_tracking`.
- Privilege fields: `role`, `scope`, `org_id`, `org_name`, `site_id`,
  `sitegroup_ids`, `orggroup_ids`, `msp_id`, `msp_name`, `name`, and `views`.

### `listOrgApiTokens`

- Method and path: `GET /api/v1/orgs/{org_id}/apitokens`
- Path parameters: `org_id`, required UUID string.
- Query parameters: none.
- Request body: none.
- Success response: `200` returns an array of `org_apitoken` objects.
- Useful response fields: `id`, `name`, `created_by`, `created_time`,
  `last_used`, `org_id`, `privileges`, `src_ips`, and `key`.
- Secret handling: `key` can appear in the API response. The implementation
  must delete it before logging, scoring, exporting, or raising errors.
- Privilege fields: `role`, `scope`, `org_id`, `site_id`, `sitegroup_id`, and
  `views`.

### `getOrgSettings`

- Method and path: `GET /api/v1/orgs/{org_id}/setting`
- Path parameters: `org_id`, required UUID string.
- Query parameters: none.
- Request body: none.
- Success response: `200` returns one `org_setting` object.
- Useful response fields: `password_policy`, `ui_idle_timeout`,
  `api_policy`, `created_time`, `modified_time`, `id`, and `org_id`.
- Password policy fields from the schema: `enabled`, `expiry_in_days`,
  `min_length`, `requires_special_char`, and `requires_two_factor_auth`.
- Password policy fields from examples: `enabled`, `freshness`, `min_length`,
  `requires_special_char`, and `requires_two_factor_auth`.
- Implementation note: read both `expiry_in_days` and `freshness` for password
  age context, because the schema and examples differ.

**Alternatives considered**:

- Use only `listOrgAdmins` and `listOrgApiTokens`. Rejected because
  organization settings can hold password policy context.
- Treat `getOrgSettings` as mandatory for report generation. Rejected because
  missing settings must not stop rows from being written. Settings gaps become
  `unknown` findings.

## Decision: Reuse the menu 47 and 48 export reference, but do not reuse token output

**Rationale**: `src/export/org_admin_exporter.py` shows current menus 47 and 48.
`OrgAdminExporter.api_tokens()` calls
`mistapi.api.v1.orgs.apitokens.listOrgApiTokens` and writes
`OrgApiTokens.csv`. `OrgAdminExporter.admins()` calls
`mistapi.api.v1.orgs.admins.listOrgAdmins` and writes `OrgAdmins.csv`.

The hygiene feature uses the same source endpoints, but it must score risk and
must never write token keys. The new operation must build safe row models before
it calls the exporter.

**Alternatives considered**:

- Read `OrgApiTokens.csv` and `OrgAdmins.csv`. Rejected because stale files can
  differ from live Mist state and can contain token key material.
- Extend `OrgAdminExporter`. Rejected because this feature is a scored report,
  not a plain export.

## Decision: Follow package operation patterns that use the shared API session

**Rationale**: Existing operation packages use the shared dependency resolver
for the active session and organization ID.

- `src/security/rogue_dhcp/operation.py` resolves the organization through
  `SourceDependencyResolver.ConfigUtils.get_cached_or_prompted_org_id()` and
  returns `SourceDependencyResolver.apisession`.
- `src/marvis/actions/operation.py` builds `MarvisActionsClient` with
  `SourceDependencyResolver.apisession`, the organization ID, and the shared
  page limit.
- `MistHelper.py` has direct `MainEntrypoint.context.apisession` call sites for
  menu-level wiring. The new package should stay decoupled and use
  `SourceDependencyResolver`. Later menu wiring can pass or expose the same
  live session through the established resolver.

**Alternatives considered**:

- Import `MainEntrypoint` directly in the report package. Rejected because that
  couples a report package to the root entry point.
- Pass raw session and organization ID through standalone wrapper functions.
  Rejected because the project requires class-based design and no wrappers.

## Decision: Score roles by effective privilege

**Rationale**: Mist management documentation states that Mist applies the
highest privilege when API-created scopes conflict. The report must avoid
underreporting access.

Role evidence from
`C:\Users\jmorrison\.copilot\skills\juniper-mist-management\01-accounts-and-roles\02-user-roles-and-privileges.md`:

- `Super User` has read and write access to the entire organization, all sites,
  administrator management, new site creation, all device types, and all
  configuration settings.
- `Org Admin` can write most organization and site settings, but cannot create
  administrators or modify login controls.
- `Network Admin` with `All Sites` can modify all sites and has organization
  audit log and inventory visibility.
- `Network Admin` with selected sites or groups is limited to assigned sites.
- `Observer` has read-only access to allowed sites, plus read-only inventory
  when scope is `All Sites`.
- If conflicting privileges and scopes come from API operations, Mist applies
  the highest privilege.

**Alternatives considered**:

- Report only the first privilege. Rejected because the API returns lists and
  conflicting entries can exist.
- Treat unknown roles as safe. Rejected because unknown access must be visible.
  Unknown role values become findings.

## Decision: Use Mist management password and token guidance for findings

**Rationale**: The feature belongs to Mist administration scope.

Password policy evidence from
`C:\Users\jmorrison\.copilot\skills\juniper-mist-management\03-security-and-access\02-password-policy-saml-and-certificates.md`:

- Local password rules live in `Organization > Admin > Settings` under
  `Password Policy`.
- The local policy can require minimum length, special characters, two-factor
  authentication, and password reset after a configured number of days.
- SSO users use the identity provider policy instead of the Mist local password
  policy.
- A local `Super User` break-glass account should remain available for identity
  provider outages.

Token evidence from
`C:\Users\jmorrison\.copilot\skills\juniper-mist-management\05-account-app-alerts-api-and-webhooks\02-user-tokens-alert-notifications-and-webhooks.md`:

- User API tokens identify a specific user and inherit that user's permissions.
- Organization API tokens are created in `Organization > Admin > Settings`
  under `API Token`.
- Organization token scope should limit blast radius.
- A token that needs one site group should not receive all-site access.
- Rotate tokens when a user leaves, an integration moves to a different scope,
  or a secret store reports exposure.

Organization settings evidence from
`C:\Users\jmorrison\.copilot\skills\juniper-mist-management\02-organization-sites-and-inventory\02-organization-settings-support-and-contracts.md`:

- Organization settings include `Password Policy`, `Session Policy`, and
  `API Token`.
- `API Token` creates organization tokens with access level and site or group
  limits.

**Alternatives considered**:

- Add domain-specific thresholds from AIOps, wireless, or WAN skills. Rejected
  because this feature scores administration access, not service assurance,
  WLAN configuration, or WAN intent.

## Decision: Record assignment skills with no extra threshold

**Rationale**: `juniper-mist-aiops`, `juniper-mist-wireless`, and
`juniper-mist-wan` were consulted as assignment skills. They do not add another
threshold for this management-scope feature without direct evidence.

**Alternatives considered**:

- Add AIOps, wireless, or WAN thresholds to token findings. Rejected because no
  consulted source tied those thresholds to administrator or token hygiene.

## Decision: Define report output through a contract

**Rationale**: Operators need stable CSV columns and a stable console summary.
Tests can validate the contract without needing live Mist access.

**Alternatives considered**:

- Let implementation choose columns from raw API keys. Rejected because this
  can expose token keys and creates unstable output.
