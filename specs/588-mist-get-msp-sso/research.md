# Phase 0 Research: getMspSso

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/msps/GET_msps_msp_id_ssos_sso_id.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that
mirrors the OpenAPI URL: `mistapi.api.v1.msps.ssos.getMspSso(apisession,
msp_id, sso_id)`. The SDK returns a `mistapi.APIResponse` object whose `.data`
attribute is the parsed JSON body. The body is a single JSON object (not a
list, not paginated) describing one SSO/IdP configuration. Notable top-level
keys per the enriched doc:

- Identity / housekeeping: `id` (UUID), `name`, `msp_id`, `org_id`, `site_id`,
  `created_time`, `modified_time`, `domain` (read-only, generated server-side).
- IdP discriminator: `idp_type` -- one of `saml`, `ldap`, `mxedge_proxy`,
  `oauth`, `openroaming`. Every other field is conditional on this value.
- SAML fields: `idp_cert`, `idp_sign_algo`, `idp_sso_url`, `issuer`,
  `nameid_format`, `custom_logout_url`, `default_role`, `role_attr_from`,
  `role_attr_extraction`, `ignore_unmatched_roles`.
- LDAP fields: `ldap_type` (`azure|custom|google|okta|ping_identity`),
  `ldap_base_dn`, `ldap_bind_dn`, `ldap_bind_password`, `ldap_cacerts` (array),
  `ldap_client_cert`, `ldap_client_key`, `ldap_server_hosts` (array),
  `ldap_resolve_groups`, `ldap_group_attr`, `ldap_group_dn`, `ldap_user_filter`,
  `group_filter`, `member_filter`.
- OAuth fields: `oauth_type`, `oauth_cc_client_id`, `oauth_cc_client_secret`,
  `oauth_ropc_client_id`, `oauth_ropc_client_secret`, `oauth_discovery_url`,
  `oauth_tenant_id`, `oauth_provider_domain`, `oauth_ping_identity_region`,
  `scim_enabled`, `scim_secret_token`.
- mxedge_proxy sub-object: `mxcluster_id`, `operator_name`, `proxy_hosts[]`,
  `ssids[]`, `auth_servers[]`, `acct_servers[]`.
- OpenRoaming sub-object: `ssids[]`, `wba_cert`.

Required path parameters: `msp_id` (UUID), `sso_id` (UUID). No query parameters.
No request body.

**Rationale**:
The enriched per-endpoint doc lists the SDK as
`mistapi.api.v1.msps.sso.getMspSso()` (singular `sso`), but the OpenAPI URL is
`/msps/{msp_id}/ssos/{sso_id}` (plural `ssos`) and the spec.md explicitly
names `mistapi.api.v1.msps.ssos`. The mistapi SDK historically generates
module paths from the URL, not the singular noun; adjacent `/msps/.../ssos`
endpoints follow the URL form. We follow the spec.md path. Final verification
happens at implementation time via
`python -c "from mistapi.api.v1.msps import ssos; help(ssos.getMspSso)"`
inside the venv; if the SDK exposes the singular alias, both names refer to
the same callable.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/msps/{msp_id}/ssos/{sso_id}`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method
   exists.
2. *Use the singular `mistapi.api.v1.msps.sso` path implied by the doc.*
   Rejected -- the URL token is plural (`ssos`), and the spec.md (authoritative
   feature contract) names the plural path. If the SDK has both, the plural
   form is canonical.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **natural primary key** strategy on a single output table:

- `msp_ssos`: PK = `id` (the SSO UUID returned by the API).

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `natural_pk`,
`primary_key=['id']`, with `indexes=['msp_id', 'org_id', 'name', 'idp_type']`
to support common NOC queries ("show all SAML SSOs in MSP X" or "find SSO by
name").

**Rationale**:
The endpoint returns a single SSO record with a stable, server-issued UUID
(`id`). This UUID is globally unique across all MSPs, orgs, and sites in Mist
Cloud (read-only and generated at creation time per the OpenAPI schema). Using
`id` alone as the PK matches how MistHelper handles every other Mist
configuration object with a stable UUID (sites, devices, templates, networks).
`INSERT OR REPLACE` upserts on the SSO UUID handle repeated reads cleanly --
re-running the menu item against the same SSO updates the existing row with
the latest `modified_time` and any field changes.

**Alternatives Considered**:

1. *`composite_pk` on `(msp_id, id)`.* Rejected -- redundant. SSO UUIDs are
   globally unique; the API guarantees no two SSOs share an `id` regardless
   of MSP scope. Adding `msp_id` to the PK would not change uniqueness but
   would clutter joins.
2. *`auto_increment_with_unique` with `id` as the unique key.* Rejected --
   pointless indirection. The natural UUID is stable, present in every
   response, and a perfect primary key.
3. *Composite `(msp_id, sso_id)` mirroring the URL.* Rejected -- the URL
   structure does not imply the database structure. The body's `id` field is
   the authoritative identity.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/msp_<msp_id_short>_sso_<sso_id_short>.csv`
- SQLite table: `msp_ssos`
- `msp_id_short` and `sso_id_short` are the first 8 hex characters of each
  UUID -- the convention already used by adjacent MistHelper exports for
  human-readable filenames without leaking full UUIDs into shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getMspSso"` (matching the
operationId verbatim). The DataExporter uses that string as the lookup key
into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
The endpoint targets exactly one SSO per call, so the filename embeds both
identifying short IDs. The shared SQLite table `msp_ssos` accumulates every
SSO ever read by any invocation of this menu item across any MSP; the PK on
`id` keeps it tidy. Naming the table `msp_ssos` (plural) mirrors the URL token
and aligns with sibling tables produced by the related list endpoint
`listMspSsos` (spec branch elsewhere) so a single SQL query can join across
read patterns.

**Alternatives Considered**:

1. *Per-MSP table (`msp_<short>_ssos`).* Rejected -- proliferates tables;
   breaks cross-MSP querying; the natural PK on `id` already gives clean
   per-MSP filtering via the indexed `msp_id` column.
2. *Full UUIDs in the filename.* Rejected -- leaks UUIDs into shell history
   and `ls` output unnecessarily; short form is enough to disambiguate
   locally.
3. *Single combined filename without `sso_id` (e.g., `msp_<short>_sso.csv`).*
   Rejected -- a single MSP can host many SSOs; collapsing them into one
   filename loses the per-SSO export trace.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 59**, sitting at the top of the
MSP-scoped read cluster inside the Safe Org Exports range. The category label
is "Safe Org Exports -- MSPs SSO".

**Rationale**:
The menu ranges documented in `.github/copilot-instructions.md` are:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource
Intensive, 102-123 WebSocket, 124-152 Interactive, 154-194 Destructive.
MSP-scoped read operations are functionally identical to org-scoped reads
(same auth, same backend, same risk profile) so they belong in the safe-
export cluster. Number 59 is the last available integer in the 1-59 range
just before the Interactive Safe block starts at 60. The provisional number
will be re-verified at `/speckit.tasks` time by grepping `MistHelper.py` for
the latest allocated menu integer; if 59 is taken, the next free integer in
the same cluster is used.

**Alternatives Considered**:

1. *Slot inside Interactive Safe (60-96).* Rejected -- the endpoint has no
   interactive sub-flow; it is a direct GET with two prompts and a write.
   "Interactive Safe" implies an in-flow menu or polling loop.
2. *Append to the end of the menu (e.g., 195).* Rejected -- the destructive
   cluster ends at 194; placing a read-only MSP query above the destructive
   block visually mis-signals the risk level to a junior NOC engineer.
3. *Group with WebSocket (102-123).* Rejected -- this is a REST GET, not a
   streaming socket.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via
`safe_input()`:

1. `msp_id` -- prompt: `"MSP ID (UUID): "`, context: `"msp_sso:msp_id"`.
   Default: the value of `MIST_MSP_ID` in `.env` if present (pressing Enter
   accepts the default). Validated via the existing `is_valid_uuid()` helper
   before the API call; on failure, log `WARNING` and return early.
2. `sso_id` -- prompt: `"SSO ID (UUID): "`, context: `"msp_sso:sso_id"`.
   No `.env` default (SSO UUIDs vary per query). Validated via
   `is_valid_uuid()` before the API call; on failure, log `WARNING` and
   return early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`. The token must hold
  read access at MSP scope; lacking that scope yields a 403 handled per the
  contract.
- `MIST_MSP_ID` -- optional default for prompt 1.

**Rationale**:
The endpoint is MSP-scoped and requires exactly the two path parameters
(`msp_id`, `sso_id`). Org / site / device IDs are not involved -- MSPs sit
above orgs in the Mist hierarchy. Defaulting `msp_id` from `.env` matches
the same convenience used by org-scoped menu items (`MIST_ORG_ID`); not
defaulting `sso_id` is intentional because most NOC users iterate across many
SSOs, and a sticky default would lead to accidental writes to the wrong
table row.

**Alternatives Considered**:

1. *Auto-list MSP SSOs first (via `listMspSsos`) and let the user pick by
   number.* Rejected -- multiplies API calls; the parent list endpoint has its
   own spec branch and menu item; users who need that flow can run the list
   first.
2. *Accept the SSO `name` instead of `sso_id`.* Rejected -- name is mutable
   and not guaranteed unique within an MSP. UUID is the safe key.
3. *Prompt for an output filename override.* Rejected -- adds keystrokes
   without operational value; the deterministic filename scheme in Research
   Task 3 makes results easy to find under `data/`.
