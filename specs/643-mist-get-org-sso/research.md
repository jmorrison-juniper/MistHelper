# Phase 0 Research: getOrgSso

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_ssos_sso_id.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the module path that mirrors the
OpenAPI URL: `mistapi.api.v1.orgs.ssos.getOrgSso(apisession, org_id, sso_id)`.
The SDK returns a `mistapi.APIResponse` object whose `.data` attribute is the
parsed JSON body. The body is a single JSON object (not a list, not paginated,
no query parameters). Top-level keys per the doc's 200 response schema:

- `id` (UUID -- Mist-assigned SSO record id, `readOnly`)
- `org_id` (UUID, `readOnly`) and `site_id` (UUID, `readOnly`) -- injected by
  Mist when the record was created
- `msp_id` (UUID, `readOnly`) -- present only for MSP-scoped SSOs
- `name` (string, **required**)
- `idp_type` (string enum: `saml` for Admin SSO; `ldap`, `mxedge_proxy`,
  `oauth`, `openroaming` for NAC SSO)
- `domain` (string, `readOnly`) -- Mist-generated slug used to build the
  SAML ACS/SLO URLs
- SAML fields (when `idp_type=saml`): `custom_logout_url`, `default_role`,
  `idp_cert`, `idp_sign_algo` (enum), `idp_sso_url`, `ignore_unmatched_roles`,
  `issuer`, `nameid_format`, `role_attr_extraction`, `role_attr_from`
- LDAP fields (when `idp_type=ldap`): `ldap_base_dn`, `ldap_bind_dn`,
  `ldap_bind_password` (**secret**), `ldap_cacerts[]`, `ldap_client_cert`,
  `ldap_client_key` (**secret**), `ldap_group_attr`, `ldap_group_dn`,
  `ldap_resolve_groups`, `ldap_server_hosts[]`, `ldap_type` (enum),
  `ldap_user_filter`, `group_filter`, `member_filter`
- OAuth fields (when `idp_type=oauth`): `oauth_cc_client_id`,
  `oauth_cc_client_secret` (**secret**), `oauth_discovery_url`,
  `oauth_ping_identity_region`, `oauth_provider_domain`, `oauth_ropc_client_id`,
  `oauth_ropc_client_secret` (**secret**), `oauth_tenant_id`, `oauth_type`
  (enum), `scim_enabled`, `scim_secret_token` (**secret**)
- `mxedge_proxy` object (when `idp_type=mxedge_proxy`) with sub-arrays
  `auth_servers[]` (host, port, secret, timeout, retry,
  require_message_authenticator) and `acct_servers[]` (host, port, secret) plus
  scalars `mxcluster_id`, `operator_name`, `proxy_hosts[]`, `ssids[]`
- `openroaming` object (when `idp_type=openroaming`) with `ssids[]` and
  `wba_cert` (**secret**)
- `created_time` (epoch, `readOnly`), `modified_time` (epoch, `readOnly`)

Required path parameters: `org_id` (UUID) and `sso_id` (UUID). No query
parameters. No request body.

**Rationale**:
The spec.md names the SDK module as `mistapi.api.v1.orgs.ssos`, matching the
URL segment (`.../orgs/{org_id}/ssos/{sso_id}` -> `mistapi.api.v1.orgs.ssos`).
The enriched per-endpoint doc's SDK section shows the singular form
`mistapi.api.v1.orgs.sso.getOrgSso()`, but adjacent operationIds under the same
URL path (`listOrgSsos`, `deleteOrgSso`, `updateOrgSso`) live under
`mistapi.api.v1.orgs.ssos` in the installed 0.59+ SDK -- verified by the
existing MistHelper call at line 11890
(`mistapi.api.v1.orgs.ssos.listOrgSsos`). The spec-named plural form is
correct; the doc's singular form is stale. Final verification happens at
implementation time via
`python -c "from mistapi.api.v1.orgs.ssos import getOrgSso; help(getOrgSso)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/ssos/{sso_id}`.* Rejected -- the
   constitution forbids direct HTTP when a mistapi method exists.
2. *Use the singular `mistapi.api.v1.orgs.sso` path from the doc.* Rejected --
   the plural `ssos` module is confirmed by the existing `listOrgSsos` call
   already in `MistHelper.py`.
3. *Call `listOrgSsos` and filter by id in Python.* Rejected -- doubles API
   cost, defeats the whole point of the `getOrgSso` operationId, and fails when
   the caller only has the sso_id (list returns all SSOs which may include
   thousands of NAC entries for large orgs).

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **`natural_pk`** strategy on the main SSO summary table, keyed on the
Mist-assigned SSO UUID (`id`). For the two `mxedge_proxy` RADIUS sub-arrays,
use **`composite_pk`** on `(sso_id, host, port)`.

- `org_sso`: PK = `id` (natural). Indexes: `org_id`, `name`, `idp_type`.
- `org_sso_mxedge_proxy_auth_servers`: PK = `(sso_id, host, port)`.
- `org_sso_mxedge_proxy_acct_servers`: PK = `(sso_id, host, port)`.

`ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `natural_pk` for the
main entry and `composite_pk` for the two sub-tables.

**Rationale**:
The Mist API assigns and returns a stable UUID `id` for every SSO record; that
UUID does not change across polls or edits. This exactly matches the
`natural_pk` pattern already used by `sites`, `devices`, and templates in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`. Re-running the menu against the same
`sso_id` cleanly upserts via `INSERT OR REPLACE ... WHERE id = ?`. The
`mxedge_proxy` RADIUS server sub-arrays contain no stable server-side
identifier, so we key each entry by the parent SSO plus the RADIUS host/port
pair, which uniquely identifies one server row within one SSO configuration.

**Alternatives Considered**:

1. *`composite_pk` on `(org_id, id)`.* Rejected -- `id` is already globally
   unique in Mist Cloud, and the composite would give no additional safety
   while making cross-org queries harder.
2. *`auto_increment_with_unique` with `id` as a UNIQUE column.* Rejected --
   this is the fallback for endpoints that lack any natural key; `getOrgSso`
   has one, so use it.
3. *Flatten the RADIUS sub-arrays into JSON-encoded columns on the summary
   table.* Rejected -- breaks SQL queryability and conflicts with the
   flattening convention used everywhere else in MistHelper.
4. *Use `sso_id` alone as PK for sub-arrays.* Rejected -- would allow only one
   RADIUS server per SSO, contradicting the schema.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/org_<org_id_short>_sso_<sso_id_short>.csv`
- CSV (auth servers, only when `idp_type=mxedge_proxy`):
  `data/org_<org_id_short>_sso_<sso_id_short>_auth_servers.csv`
- CSV (acct servers, only when `idp_type=mxedge_proxy`):
  `data/org_<org_id_short>_sso_<sso_id_short>_acct_servers.csv`
- SQLite tables: `org_sso`, `org_sso_mxedge_proxy_auth_servers`,
  `org_sso_mxedge_proxy_acct_servers`
- `_short` suffix = first 8 hex characters of the UUID -- established
  MistHelper convention for human-readable filenames that avoid leaking full
  UUIDs into shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getOrgSso"` (matching the
operationId) for the summary and `"getOrgSsoMxedgeProxyAuthServers"` /
`"getOrgSsoMxedgeProxyAcctServers"` for the sub-tables. The DataExporter uses
these strings as lookup keys into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by `listOrgSsos` and other org-scoped exports
in MistHelper. Splitting the mxedge_proxy RADIUS servers into two dedicated
child tables keeps the summary schema flat and queryable, and only materializes
those tables when the SSO is actually of `idp_type=mxedge_proxy`.

**Alternatives Considered**:

1. *Single output file with JSON-encoded `mxedge_proxy` column.* Rejected --
   breaks SQL queryability and violates the flattening convention.
2. *Full org UUID + sso UUID in the filename.* Rejected -- leaks IDs into
   shell history / ls output. Short form is enough to disambiguate locally.
3. *One file per SSO with all IdP-type-specific fields as NULL columns.*
   Accepted for the summary table (a single wide `org_sso` table with sparse
   columns is standard SQLite practice), rejected for the RADIUS sub-arrays
   (which are variable-length lists).

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 196**, sitting in the "Safe Org
Exports -- SSO Configuration" category. Provisional -- verified at
`/speckit.tasks` time via a fresh grep of `MistHelper.py`.

**Rationale**:
A regex sweep of `MistHelper.py` (`^\s*"(\d+)":\s*\(`) shows 196 registered
menu integers with maximum 195 and zero gaps below it. The destructive block
ends at 194; 195 is already an existing safe operation. 196 is the next
contiguous integer and sits outside the destructive block (154-194), so it is
correctly categorized as a safe / read-only operation without renumbering any
existing item.

Placing this alongside `listOrgSsos` (which sits at line 11890 registered
elsewhere in the menu dispatch table) would be semantically preferable but
would require renumbering existing entries -- explicitly out of scope for a
single-endpoint addition. The `--test` sweep skip list (14, 18, 63-65, 90-100)
does not touch 196, so the new item is exercised by every default test run.

**Alternatives Considered**:

1. *Slot adjacent to `listOrgSsos` at 58.* Rejected -- 58 is already occupied
   (`OrgExportUtils`-owned entry) and renumbering would touch every downstream
   menu integer.
2. *Slot inside the destructive block (154-194).* Rejected -- this is a
   read-only GET; placing it in the destructive block visually mis-signals
   risk to a junior NOC engineer.
3. *Wait for a full menu reorganization.* Rejected -- blocks this endpoint on
   an unrelated refactor. 196 is safe and available today.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context: `"org_sso:org_id"`.
   Default: value of `MIST_ORG_ID` in `.env` if present (pressing Enter accepts
   the default). Validated via the existing `is_valid_uuid()` helper before
   any further work; on failure, log `WARNING` and return early.
2. `sso_id` -- prompt: `"SSO ID (UUID): "`, context: `"org_sso:sso_id"`.
   Default: value of `MIST_SSO_ID` in `.env` if present, else no default (user
   must supply). Also validated via `is_valid_uuid()`; on failure, log
   `WARNING` and return early.

`.env` values consumed (loaded via the existing `python-dotenv` bootstrap,
never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.
- `MIST_SSO_ID` -- optional default for prompt 2 (new; documented in
  `deploy/.env.example` in the same PR).

**Rationale**:
The endpoint requires exactly two path parameters and no query parameters, so
two prompts cover the full contract. No site scoping, no device scoping, no
detail flag. Offering `MIST_SSO_ID` as an optional default lets automation
(`python MistHelper.py --menu 196` piped from a wrapper script) run
non-interactively.

**Alternatives Considered**:

1. *Auto-select the first SSO from a prior `listOrgSsos` call.* Rejected --
   couples this menu item to prior state and hides which SSO is being fetched.
   The two explicit prompts make the operation self-documenting.
2. *Accept `sso_id` from the command line via a new `--sso-id` flag.*
   Rejected -- MistHelper's argument surface is intentionally minimal; the
   `.env` default plus `safe_input()` covers automation cleanly without
   growing the CLI grammar.
3. *Prompt for org name instead of `org_id`.* Rejected -- name lookup would
   require an extra `listOrgs` call; the SSO menu item stays cheap when the
   user knows the UUID.
