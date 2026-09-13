# Phase 0 Research: getMspAdmin

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/msps/GET_msps_msp_id_admins_admin_id.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.msps.admins.getMspAdmin(apisession, msp_id, admin_id)`.
The SDK returns a `mistapi.APIResponse` object whose `.data` attribute is the parsed
JSON body. The body is a single JSON object (not a list, not paginated) with the
following top-level keys per the enriched doc:

- `admin_id` (UUID string -- read-only, server-assigned)
- `email` (string -- absent for Org API Token admins)
- `first_name`, `last_name`, `name` (strings -- `name` only for Org API Token)
- `phone`, `phone2` (strings -- digits including country code)
- `enable_two_factor`, `two_factor_verified` (booleans -- read-only)
- `oauth_google`, `via_sso` (booleans -- read-only)
- `compliance_status` (string enum: `blocked`, `restricted`)
- `expire_time` (int32 epoch)
- `hours` (int 1-168, default 24 -- invite validity window)
- `no_tracking` (boolean or null -- EU privacy opt-in/out flag)
- `password_modified_time` (number, epoch seconds)
- `session_expiry` (int 10-20160 -- read-only)
- `tags` (string[] -- read-only)
- `privileges` (array of `admin_privilege` objects: `{role, scope, msp_id?, org_id?,
  site_id?, sitegroup_ids?, orggroup_ids?, views?, name?, msp_name?, msp_url?,
  msp_logo_url?, org_name?}`)

Required path parameters: `msp_id` (UUID) and `admin_id` (UUID).
No query parameters. No request body.

**Rationale**:
The enriched doc explicitly lists `mistapi.api.v1.msps.admins.getMspAdmin()` and the
spec.md repeats the same module path. The mistapi SDK historically organizes module
paths by URL path (verified by adjacent endpoints under `msps/{msp_id}/admins` such as
the list, update, and delete operations -- all under `mistapi.api.v1.msps.admins`).
The function name `getMspAdmin` matches the operationId one-for-one. Final verification
happens at implementation time via
`python -c "from mistapi.api.v1.msps.admins import getMspAdmin; help(getMspAdmin)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/msps/{msp_id}/admins/{admin_id}`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the OpenAPI tag (`MSPs Admins`) to derive the module path.* Rejected -- the
   mistapi SDK organizes modules by URL path, not OpenAPI tag, and the spec.md (the
   authoritative feature contract) names the URL-based path.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on two separate output tables:

- `msp_admins`: PK = `(msp_id, admin_id)` -- one row per (MSP, admin). `admin_id` is a
  Mist-issued UUID and is globally unique in practice, but pairing with `msp_id`
  preserves tenant context, supports cross-MSP MistHelper deployments, and matches the
  natural URL key the user supplies.
- `msp_admin_privileges`: PK = `(msp_id, admin_id, scope, scope_target)` -- one row per
  privilege entry in the response's `privileges` array. `scope_target` is the
  MistHelper-injected concatenation of whichever scope-specific identifier is present
  (`msp_id` when `scope=msp`, `org_id` when `scope=org`, `site_id` when `scope=site`,
  the first `sitegroup_ids` element when `scope=sitegroup`, the first `orggroup_ids`
  element when `scope=orggroup`).

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk` for both
tables, with `msp_id` injected by MistHelper before the upsert (the response body does
not echo the path `msp_id`).

**Rationale**:
The endpoint reports the *current* profile and privilege set of a single admin.
Re-running the menu item against the same (msp, admin) pair must update the existing
rows rather than append duplicate snapshots. The admin profile changes rarely
(role, contact info, 2FA state) while privileges change more often (admins gain or
lose org/site scope) -- splitting summary and privileges into separate tables lets
SQLite `INSERT OR REPLACE` upsert each table independently without losing rows. The
admin-summary PK uses `(msp_id, admin_id)` because the `admin_id` UUID is the natural
business key the Mist API recognizes. The privileges PK includes `scope` and
`scope_target` because a single admin can have multiple privileges with different
scopes (one `msp` scope plus several `org` scopes plus several `site` scopes).

**Alternatives Considered**:

1. *`natural_pk` on `admin_id` alone for the summary table.* Rejected -- omits the
   tenant context an operator needs when joining MSP-admin tables across multiple
   MSPs, and the URL path includes `msp_id` so it is always known.
2. *`auto_increment_with_unique` for both tables.* Rejected -- would let repeated polls
   accumulate duplicate snapshots, defeating the upsert behavior the spec requires
   (FR-005, FR-007 in spec.md).
3. *Single combined table with JSON-encoded `privileges` column.* Rejected -- breaks
   SQL queryability and conflicts with the flattening convention used everywhere else
   in MistHelper. A typical operator query is "which admins have `role=admin` at site
   X" -- impossible without a flat privileges table.
4. *Privileges PK of `(msp_id, admin_id, role, scope)`.* Rejected -- a single admin can
   legitimately have `role=admin` on two different orgs (two `org`-scope rows with the
   same role), so role is not part of the natural key. `scope_target` is.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/msp_<msp_id_short>_admin_<admin_id_short>.csv`
- CSV (privileges): `data/msp_<msp_id_short>_admin_<admin_id_short>_privileges.csv`
- SQLite tables: `msp_admins` and `msp_admin_privileges`
- `<msp_id_short>` and `<admin_id_short>` are the first 8 hex characters of the
  respective UUIDs -- already the convention used by adjacent exports in MistHelper
  for human-readable filenames without leaking full UUIDs into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"getMspAdmin"` for the summary write and `"getMspAdminPrivileges"` for the
privileges write. The DataExporter uses these strings as the lookup keys into
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by other GET-by-id exports in MistHelper (filename
embeds the natural key prefix so users can find prior runs at a glance). Two output
files / two SQLite tables keeps the schema clean and lets an operator query the
summary without joining when they don't need privilege detail. Tables are named in
the plural to match the existing convention for collection-style tables
(`org_sites`, `org_licenses_summary`, etc.).

**Alternatives Considered**:

1. *Single output file with JSON-encoded `privileges` column.* Rejected -- see
   Research Task 2 alternative 3.
2. *Full UUIDs in the filename.* Rejected -- leaks full UUIDs into shell history and
   `ls` output unnecessarily. The 8-char short form is enough to disambiguate locally.
3. *Naming tables `msp_admin_summary` / `msp_admin_privileges`.* Rejected -- the
   summary table holds one row per admin (not one row per polling event), so a plain
   collection name `msp_admins` better reflects its semantics. The detail table keeps
   the explicit `_privileges` suffix.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 57**, sitting inside the Safe Org Exports
cluster between adjacent MSP-related exports. The category label is "Safe Org
Exports -- MSP Admins".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive,
102-123 WebSocket, 124-152 Interactive, 154-194 Destructive. MSP read operations are
strictly read-only and small (single JSON object) -- they belong in the Safe Org
Exports band. Number 57 is provisionally chosen as the next contiguous integer in the
misc / MSP sub-band of 1-59. The number is provisional -- at `/speckit.tasks` time,
`MistHelper.py` is grep'd for the latest allocated menu integer and 57 is shifted
forward (or back to fill a gap) if a conflict exists with another in-flight branch.

**Alternatives Considered**:

1. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends at 194,
   and placing a read-only MSP admin lookup above the destructive block visually
   mis-signals the risk level to a junior NOC engineer scrolling the menu.
2. *Slot inside Resource Intensive (96-101).* Rejected -- this endpoint is a single
   GET that returns a small JSON object, with no pagination and no long-running work.
   It belongs in the safe block.
3. *Slot inside Interactive Safe (60-96).* Rejected -- "Interactive Safe" is reserved
   for menus that drive multi-step user dialogues (e.g. device pickers, site
   selectors). This menu prompts twice and returns; it fits the basic Safe Org
   Exports pattern.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `msp_id` -- prompt: `"MSP ID (UUID): "`, context: `"msp_admin:msp_id"`. Default:
   the value of `MIST_MSP_ID` in `.env` if present (pressing Enter accepts the
   default). Validated via the existing `is_valid_uuid()` helper before the API call;
   on failure, log `WARNING` and return early.
2. `admin_id` -- prompt: `"Admin ID (UUID): "`, context: `"msp_admin:admin_id"`.
   Default: the value of `MIST_ADMIN_ID` in `.env` if present. Same UUID validation
   and early-return behavior on failure.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_MSP_ID` -- optional default for prompt 1.
- `MIST_ADMIN_ID` -- optional default for prompt 2.

**Rationale**:
The endpoint is keyed entirely by the two URL path parameters and has no query
parameters or request body. Site, device, and org IDs are not involved. Defaulting
both prompts from `.env` lets the `--test` non-interactive smoke run hit a known MSP
admin without manual input, while still letting an operator override either value
interactively. UUID validation client-side avoids a wasted API round trip on typos.

**Alternatives Considered**:

1. *Add a third prompt for an output filename override.* Rejected -- adds keystrokes
   without operational value. The deterministic filename scheme in Research Task 3
   makes results easy to find under `data/`.
2. *Auto-list MSP admins and let the user pick one.* Rejected -- that is a different
   feature (operationId `listMspAdmins`, its own spec). This menu item is the
   focused GET-by-id contract; menu composition is a future enhancement.
3. *Read both UUIDs only from `.env`, no prompt.* Rejected -- removes the operator's
   ability to ad-hoc query a different admin without editing `.env`, and breaks the
   established prompt-with-default UX pattern used by other Safe Org Exports.
